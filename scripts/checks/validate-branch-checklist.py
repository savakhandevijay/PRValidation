#!/usr/bin/env python3
"""
Validate Git branch compliance against Google Sheet checklist.
Auto-detects current git branch if no argument is passed.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Any

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ModuleNotFoundError:
    print(
        "❌ Missing Google API dependencies.\n"
        "Run: source .venv/bin/activate && pip install google-api-python-client google-auth",
        file=sys.stderr,
    )
    sys.exit(2)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS_FILE = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(PROJECT_ROOT / "scripts" / "credentials" / "google-service-account.json"),
)
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Branches")
BRANCH_COLUMN_NAME = os.environ.get("BRANCH_COLUMN", "Branch")

# Metadata columns to skip during status checking
METADATA_COLUMNS = {
    "branch", "jira", "pr", "pr link", "developer", 
    "author", "date", "status", "notes", "comments"
}

# Values accepted as completed or safely skipped
VALID_VALUES = {
    "yes", "y", "true", "done", "completed", 
    "pass", "passed", "na", "n/a", "not applicable", "1"
}


def get_current_git_branch() -> str:
    """Fetch active Git branch name automatically."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def normalize(value: Any) -> str:
    """Normalize string values for comparison."""
    if value is None:
        return ""
    return str(value).strip().lower()


def load_credentials() -> Credentials:
    """Load Service Account Credentials."""
    credentials_path = Path(CREDENTIALS_FILE)
    if not credentials_path.exists():
        print(f"❌ Credentials file not found: {credentials_path}")
        sys.exit(1)

    return Credentials.from_service_account_file(
        str(credentials_path),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )


def get_sheet_data() -> list[list[str]]:
    """Fetch raw values from configured sheet range."""
    if not GOOGLE_SHEET_ID:
        print("❌ GOOGLE_SHEET_ID environment variable is missing.")
        sys.exit(1)

    credentials = load_credentials()

    try:
        service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        range_name = f"{GOOGLE_SHEET_NAME}!A1:ZZ"
        response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=GOOGLE_SHEET_ID, range=range_name)
            .execute()
        )
        return response.get("values", [])
    except HttpError as exc:
        print(f"❌ Google Sheets API Request Failed: {exc}")
        sys.exit(1)


def main() -> None:
    # 1. Determine target branch
    branch_name = sys.argv[1].strip() if len(sys.argv) > 1 else get_current_git_branch()

    if not branch_name:
        print("❌ Unable to detect Git branch name. Provide it manually.")
        sys.exit(2)

    print("==========================================")
    print("      WSS / PHP Branch Checklist Verification")
    print("==========================================")
    print(f"Target Branch : {branch_name}")
    print(f"Target Sheet  : {GOOGLE_SHEET_NAME}")
    print("==========================================\n")

    rows = get_sheet_data()
    if not rows or len(rows) < 2:
        print("❌ Google Sheet contains no records.")
        sys.exit(1)

    header_row = rows[0]
    header_map = {normalize(col): idx for idx, col in enumerate(header_row)}

    branch_col_idx = header_map.get(normalize(BRANCH_COLUMN_NAME))
    if branch_col_idx is None:
        print(f"❌ Column '{BRANCH_COLUMN_NAME}' missing in Sheet header.")
        sys.exit(1)

    # 2. Locate target branch row
    target_row = None
    for row in rows[1:]:
        if branch_col_idx < len(row) and row[branch_col_idx].strip() == branch_name:
            target_row = row
            break

    if not target_row:
        print(f"❌ Branch '{branch_name}' was not found in the Google Sheet.")
        sys.exit(1)

    print(f"✅ Found branch entry in sheet: '{branch_name}'\n")

    # 3. Perform Checklist Verification
    failed_checks = []
    passed_checks = []

    for col_name, idx in header_map.items():
        if col_name in METADATA_COLUMNS:
            continue

        raw_col_title = header_row[idx]
        val = normalize(target_row[idx]) if idx < len(target_row) else ""

        if val in VALID_VALUES:
            passed_checks.append(raw_col_title)
        else:
            failed_checks.append((raw_col_title, val if val else "EMPTY"))

    # 4. Report Results
    if failed_checks:
        print(f"❌ Checklist Incomplete ({len(failed_checks)} item(s) pending):\n")
        for title, status in failed_checks:
            print(f"  [❌ UNMET] {title}")
            print(f"            Current Value: '{status}'")
        print("\nEnsure all conditional points (DB, Swagger, Crons, PII) are marked 'YES' or 'N/A'.")
        sys.exit(1)

    print(f"✅ All {len(passed_checks)} required checklist parameters are verified.")
    print("✅ PR Validation Successful!")
    sys.exit(0)


if __name__ == "__main__":
    main()