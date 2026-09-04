#!/usr/bin/env python3

import os
import subprocess
import sys
from typing import List, Tuple

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# Configuration
# ============================================================

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Checklist")

# Values considered valid/completed
VALID_ANSWERS = {
    "yes",
    "na",
    "n/a",
}

# Values considered explicitly failed
INVALID_ANSWERS = {
    "no",
}

# Rows containing these values in column A are section/document
# headings rather than actual checklist questions.
SKIP_EXACT_VALUES = {
    "PHP checklist",
    "Code review guidelines",
    "API reference doc",
    "WSS versioning doc",
    "WSS config doc - WIP",
    "WSS Appsettings Key List",
    "PII checklist",
    "Deployment guide",
}


# ============================================================
# Git
# ============================================================

def get_current_git_branch() -> str:
    """Return the current Git branch name."""

    try:
        result = subprocess.run(
            [
                "git",
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
            raise RuntimeError("Unable to determine Git branch.")

        # Do not run checklist against detached HEAD
        if branch == "HEAD":
            raise RuntimeError(
                "Repository is in detached HEAD state. "
                "Please checkout the feature branch."
            )

        return branch

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Unable to determine current Git branch. "
            "Make sure this command is executed inside a Git repository."
        ) from exc


# ============================================================
# Google Sheets
# ============================================================

def connect_to_google_sheet():
    """Connect to Google Sheets using a service account."""

    if not GOOGLE_SHEET_ID:
        raise RuntimeError(
            "GOOGLE_SHEET_ID environment variable is not configured."
        )

    credentials_file = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    if not credentials_file:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable "
            "is not configured."
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

    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)

    return worksheet


# ============================================================
# Helpers
# ============================================================

def normalize(value: str) -> str:
    return value.strip().lower()


def is_section_heading(question: str) -> bool:
    """
    Determine whether a row is a section/document heading
    instead of an actual checklist question.
    """

    normalized = normalize(question)

    if not normalized:
        return True

    if question.strip() in SKIP_EXACT_VALUES:
        return True

    return False


def find_branch_column(
    rows: List[List[str]],
    branch_name: str,
) -> Tuple[int, int]:
    """
    Search the entire spreadsheet for the branch name.

    Returns:
        (row_index, column_index)

    Both indexes are zero-based.
    """

    branch_normalized = normalize(branch_name)

    for row_index, row in enumerate(rows):

        for column_index, value in enumerate(row):

            if normalize(value) == branch_normalized:
                return row_index, column_index

    return -1, -1


# ============================================================
# Checklist validation
# ============================================================

def validate_checklist(
    rows: List[List[str]],
    branch_name: str,
) -> bool:

    branch_row, branch_column = find_branch_column(
        rows,
        branch_name,
    )

    if branch_row == -1:
        print()
        print("❌ CHECKLIST VALIDATION FAILED")
        print()
        print(f"Feature branch: {branch_name}")
        print()
        print("Branch was NOT found in the Google Sheet.")
        print()
        print(
            "Please add the feature branch to the checklist "
            "spreadsheet before creating the PR."
        )

        return False

    print()
    print("======================================================")
    print(" Google Sheet Checklist Validation")
    print("======================================================")
    print()
    print(f"Feature branch : {branch_name}")
    print(f"Branch cell    : row {branch_row + 1}, column {branch_column + 1}")
    print()

    failures = []
    completed = 0
    skipped = 0

    # Start checking rows AFTER the branch header.
    for row_index in range(branch_row + 1, len(rows)):

        row = rows[row_index]

        # Column A contains checklist question/guideline.
        if len(row) == 0:
            continue

        question = row[0].strip()

        # Ignore empty rows and section headings.
        if is_section_heading(question):
            skipped += 1
            continue

        # Make sure the branch column exists in this row.
        if branch_column >= len(row):
            answer = ""
        else:
            answer = row[branch_column].strip()

        answer_normalized = normalize(answer)

        # Empty answer
        if not answer_normalized:
            failures.append(
                {
                    "row": row_index + 1,
                    "question": question,
                    "answer": "<EMPTY>",
                }
            )
            continue

        # Explicit No
        if answer_normalized in INVALID_ANSWERS:
            failures.append(
                {
                    "row": row_index + 1,
                    "question": question,
                    "answer": answer,
                }
            )
            continue

        # Valid answer
        if answer_normalized in VALID_ANSWERS:
            completed += 1
            continue

        # Unknown answer
        failures.append(
            {
                "row": row_index + 1,
                "question": question,
                "answer": answer,
            }
        )

    # ========================================================
    # Report
    # ========================================================

    print(f"Completed checklist items : {completed}")
    print(f"Skipped section headings  : {skipped}")
    print(f"Failed checklist items    : {len(failures)}")
    print()

    if failures:

        print("------------------------------------------------------")
        print(" Failed Checklist Items")
        print("------------------------------------------------------")

        for item in failures:

            print()
            print(f"Row    : {item['row']}")
            print(f"Answer : {item['answer']}")
            print(f"Check  : {item['question']}")

        print()
        print("======================================================")
        print("❌ CHECKLIST VALIDATION FAILED")
        print("======================================================")
        print()

        return False

    print("======================================================")
    print("✅ CHECKLIST VALIDATION PASSED")
    print("======================================================")
    print()

    return True


# ============================================================
# Main
# ============================================================

def main():

    try:

        branch_name = get_current_git_branch()

        print()
        print(f"Checking Google Sheet for branch: {branch_name}")

        worksheet = connect_to_google_sheet()

        rows = worksheet.get_all_values()

        if not rows:
            raise RuntimeError(
                "Google Sheet is empty."
            )

        success = validate_checklist(
            rows,
            branch_name,
        )

        sys.exit(0 if success else 1)

    except Exception as exc:

        print()
        print("❌ ERROR")
        print()
        print(str(exc))
        print()

        sys.exit(2)


if __name__ == "__main__":
    main()