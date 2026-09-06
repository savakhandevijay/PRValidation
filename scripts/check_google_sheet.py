#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# Configuration
# ============================================================

# Git repository containing the feature branch
GIT_REPO_DIR = os.getenv(
    "GIT_REPO_DIR",
    "/var/www/app/src",
)

# Google configuration
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# We no longer need GOOGLE_SHEET_NAME because we search
# all worksheets/tabs.
#
# Example:
#
# January
# February
# March
# April
#
# The Jira case can exist in any of them.


# ============================================================
# Checklist Answer Configuration
# ============================================================

# These answers are considered successful.
VALID_ANSWERS = {
    "yes",
    "na",
    "n/a",
    "todo"
}

# These answers are considered failed.
INVALID_ANSWERS = {
    "no",
}


# Regex based valid answers.
#
# Example:
#   DB-123       -> valid
#   DB-12345     -> valid
#   DB-ABC       -> invalid
#
VALID_ANSWER_PATTERNS = [
    r"^DB-\d+$",
]


# Spreadsheet rows which are headings/document references
# rather than actual checklist questions.
#
# These rows are skipped during validation.
SKIP_EXACT_VALUES = {
    "PHP checklist",
    "Code review guidelines",
    "Update caching doc if caching is added",
    "API reference doc",
    "WSS versioning doc",
    "WSS config doc - WIP",
    "Add Qmetry Cases",
    "Update deployment guide",
    "Deployment guide",
}


# ============================================================
# Utility Functions
# ============================================================

def normalize(value: str) -> str:
    """
    Normalize a spreadsheet value for comparison.
    """

    return value.strip().casefold()


def is_valid_regex_answer(answer: str) -> bool:
    """
    Check whether an answer matches one of the configured
    valid regular expressions.
    """

    answer = answer.strip()

    for pattern in VALID_ANSWER_PATTERNS:
        if re.fullmatch(pattern, answer, re.IGNORECASE):
            return True

    return False


def is_section_heading(question: str) -> bool:
    """
    Determine whether a row is a section/document heading
    instead of an actual checklist question.
    """

    normalized = normalize(question)

    if not normalized: 
        return True 
    if normalized in { 
        normalize(value) for value in SKIP_EXACT_VALUES 
    }: 
        return True 
    
    return False


# ============================================================
# Git
# ============================================================

def get_current_git_branch() -> str:
    """
    Get the current Git branch from the configured repository.
    """

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                GIT_REPO_DIR,
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        branch = result.stdout.strip()

        if not branch:
            raise RuntimeError(
                "Unable to determine Git branch."
            )

        if branch == "HEAD":
            raise RuntimeError(
                "Repository is in detached HEAD state."
            )

        return branch

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Unable to determine Git branch from "
            f"{GIT_REPO_DIR}."
        ) from exc


def get_jira_case_from_branch(branch_name: str) -> str:
    """
    Convert Git branch name into Jira case number.

    Examples:

        feature-wss-15056 -> wss-15056
        hotfix-wss-15056  -> wss-15056
        wss-15056         -> wss-15056
    """

    branch = branch_name.strip()

    # Remove feature- or hotfix- prefix.
    #
    # Case insensitive:
    #
    # feature-wss-15056
    # FEATURE-wss-15056
    # hotfix-wss-15056
    # HOTFIX-wss-15056
    #
    branch = re.sub(
        r"^(feature|hotfix)-",
        "",
        branch,
        flags=re.IGNORECASE,
    )

    return branch


# ============================================================
# Google Sheets
# ============================================================

def connect_to_google_spreadsheet():
    """
    Authenticate and return the Google Spreadsheet object.
    """

    if not GOOGLE_SHEET_ID:
        raise RuntimeError(
            "GOOGLE_SHEET_ID environment variable "
            "is not configured."
        )

    credentials_file = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    if not credentials_file:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS environment "
            "variable is not configured."
        )

    if not os.path.isfile(credentials_file):
        raise RuntimeError(
            f"Google credentials file does not exist: "
            f"{credentials_file}"
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials = Credentials.from_service_account_file(
        credentials_file,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    return client.open_by_key(GOOGLE_SHEET_ID)


# ============================================================
# Find Jira Case
# ============================================================

def find_jira_case(
    spreadsheet,
    jira_case: str,
) -> Optional[Dict]:

    """
    Search all worksheets for the Jira case.

    Returns:

        {
            "worksheet": worksheet,
            "rows": rows,
            "row_index": 0-based row index,
            "column_index": 0-based column index,
            "value": matched value
        }

    Returns None if not found.
    """

    jira_case_normalized = normalize(jira_case)

    print()
    print(
        f"Searching all worksheets for Jira case: "
        f"{jira_case}"
    )

    worksheets = spreadsheet.worksheets()

    print(
        f"Worksheets found: {len(worksheets)}"
    )

    for worksheet in worksheets:

        print(
            f"  Checking worksheet: "
            f"{worksheet.title}"
        )

        rows = worksheet.get_all_values()

        for row_index, row in enumerate(rows):

            for column_index, value in enumerate(row):

                if normalize(value) == jira_case_normalized:

                    print()
                    print(
                        f"✅ Jira case found in worksheet: "
                        f"{worksheet.title}"
                    )

                    print(
                        f"   Row    : {row_index + 1}"
                    )

                    print(
                        f"   Column : {column_index + 1}"
                    )

                    return {
                        "worksheet": worksheet,
                        "rows": rows,
                        "row_index": row_index,
                        "column_index": column_index,
                        "value": value,
                    }

    return None


# ============================================================
# Validate Checklist
# ============================================================

def validate_checklist(
    rows: List[List[str]],
    branch_row: int,
    branch_column: int,
) -> Tuple[List[Dict], List[Dict]]:

    passed_items = []
    failed_items = []

    # Start after the Jira case row.
    for row_index in range(
        branch_row + 1,
        len(rows),
    ):

        row = rows[row_index]

        if not row:
            continue

        # Column A contains checklist question.
        question = row[0].strip()

        # Empty rows / headings
        if is_section_heading(question):
            continue

        # Branch/Jira answer column.
        if branch_column >= len(row):
            answer = ""
        else:
            answer = row[branch_column].strip()

        answer_normalized = normalize(answer)

        item = {
            "row": row_index + 1,
            "question": question,
            "answer": answer or "<EMPTY>",
        }

        # ----------------------------------------------------
        # Missing answer
        # ----------------------------------------------------

        if not answer_normalized:

            failed_items.append(item)

            continue

        # ----------------------------------------------------
        # Explicit No
        # ----------------------------------------------------

        if answer_normalized in INVALID_ANSWERS:

            failed_items.append(item)

            continue

        # ----------------------------------------------------
        # Standard valid answers
        #
        # Yes
        # NA
        # N/A
        # todo
        # ----------------------------------------------------

        if answer_normalized in VALID_ANSWERS:

            passed_items.append(item)

            continue

        # ----------------------------------------------------
        # Regex based valid answers
        #
        # Example:
        #
        # DB-123
        # DB-456
        # ----------------------------------------------------

        if is_valid_regex_answer(answer):

            passed_items.append(item)

            continue

        # ----------------------------------------------------
        # Unknown answer
        # ----------------------------------------------------

        failed_items.append(item)

    return passed_items, failed_items


# ============================================================
# Output
# ============================================================

def print_validation_result(
    jira_case: str,
    worksheet_name: str,
    passed_items: List[Dict],
    failed_items: List[Dict],
) -> bool:

    print()
    print("=" * 70)
    print(" Google Sheet Checklist Validation")
    print("=" * 70)

    print()
    print(f"Jira case : {jira_case}")
    print(f"Worksheet : {worksheet_name}")

    # --------------------------------------------------------
    # Successful
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print(
        f"✅ PASSED / COMPLETED "
        f"({len(passed_items)})"
    )
    print("-" * 70)

    if passed_items:

        for item in passed_items:

            print(
                f"[{item['answer']}] "
                f"{item['question']}"
            )

    else:

        print("No completed checklist items found.")

    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print(
        f"❌ FAILED / MISSING "
        f"({len(failed_items)})"
    )
    print("-" * 70)

    if failed_items:

        for item in failed_items:

            print(
                f"[{item['answer']}] "
                f"{item['question']}"
            )

    else:

        print("No failed checklist items.")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)

    if failed_items:

        print(
            "❌ CHECKLIST VALIDATION FAILED"
        )

        print(
            f"Completed : {len(passed_items)}"
        )

        print(
            f"Failed    : {len(failed_items)}"
        )

        print("=" * 70)
        print()

        return False

    print(
        "✅ CHECKLIST VALIDATION PASSED"
    )

    print(
        f"Completed : {len(passed_items)}"
    )

    print(
        f"Failed    : {len(failed_items)}"
    )

    print("=" * 70)
    print()

    return True


# ============================================================
# Main
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # 1. Get Git branch
        # ----------------------------------------------------

        print()
        print(
            "DEBUG: Reading Git branch..."
        )

        branch_name = get_current_git_branch()

        print(
            f"Git branch: {branch_name}"
        )

        # ----------------------------------------------------
        # 2. Convert branch to Jira case
        # ----------------------------------------------------

        jira_case = get_jira_case_from_branch(
            branch_name
        )

        print(
            f"Jira case: {jira_case}"
        )

        # ----------------------------------------------------
        # 3. Connect to Google Spreadsheet
        # ----------------------------------------------------

        print()
        print(
            "DEBUG: Connecting to Google Spreadsheet..."
        )

        spreadsheet = connect_to_google_spreadsheet()

        print(
            f"Spreadsheet: {spreadsheet.title}"
        )

        # ----------------------------------------------------
        # 4. Search all worksheets
        # ----------------------------------------------------

        result = find_jira_case(
            spreadsheet,
            jira_case,
        )

        # ----------------------------------------------------
        # 5. Jira case not found
        # ----------------------------------------------------

        if result is None:

            print()
            print("=" * 70)
            print("❌ CHECKLIST VALIDATION FAILED")
            print("=" * 70)

            print()
            print(
                f"Jira case '{jira_case}' was not found "
                f"in any worksheet."
            )

            print()
            print(
                "Please add the Jira case to the Google "
                "Sheet before creating the PR."
            )

            print()

            sys.exit(1)

        # ----------------------------------------------------
        # 6. Validate checklist
        # ----------------------------------------------------

        passed_items, failed_items = validate_checklist(
            rows=result["rows"],
            branch_row=result["row_index"],
            branch_column=result["column_index"],
        )

        # ----------------------------------------------------
        # 7. Print result
        # ----------------------------------------------------

        success = print_validation_result(
            jira_case=jira_case,
            worksheet_name=result["worksheet"].title,
            passed_items=passed_items,
            failed_items=failed_items,
        )

        # ----------------------------------------------------
        # 8. Exit code
        # ----------------------------------------------------

        sys.exit(0 if success else 1)

    except Exception as exc:

        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)

        print()
        print(
            f"Exception type: {type(exc).__name__}"
        )

        print(
            f"Exception: {exc}"
        )

        print()

        # Print full traceback while debugging.
        raise


if __name__ == "__main__":
    main()
