#!/usr/bin/env python3
"""
Validate a branch's checklist against a Google Sheet utilizing a Google 
Apps Script (GAS) Web App proxy secured via HMAC-SHA256 request signatures.
"""

import hashlib
import hmac
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

import requests

# ============================================================
# Configuration
# ============================================================

GIT_REPO_DIR = os.getenv("GIT_REPO_DIR", "/var/www/app/src")

# The URL provided by Google Apps Script after deployment
GAS_WEB_APP_URL = os.getenv("GAS_WEB_APP_URL")

# The shared secret key (must match API_SECRET_KEY in Apps Script Script Properties)
GAS_API_KEY = os.getenv("GAS_API_KEY")

REQUEST_TIMEOUT_SECONDS = 90

VALID_ANSWERS = {"yes", "na", "n/a", "todo"}
INVALID_ANSWERS = {"no"}
VALID_ANSWER_PATTERNS = [r"^DB-\d+$"]
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
# Utility & Security Functions
# ============================================================

def normalize(value: str) -> str:
    return value.strip().casefold()

def is_valid_regex_answer(answer: str) -> bool:
    answer = answer.strip()
    for pattern in VALID_ANSWER_PATTERNS:
        if re.fullmatch(pattern, answer, re.IGNORECASE):
            return True
    return False

def is_section_heading(question: str) -> bool:
    normalized = normalize(question)
    if not normalized:
        return True
    if normalized in {normalize(value) for value in SKIP_EXACT_VALUES}:
        return True
    return False

def generate_hmac_signature(jira_case: str, secret_key: str) -> Tuple[str, str]:
    """
    Generate a time-bound HMAC-SHA256 signature.
    
    Message format: "<timestamp>:<normalized_jira_case>"
    """
    timestamp_str = str(int(time.time()))
    jira_normalized = normalize(jira_case)
    message = f"{timestamp_str}:{jira_normalized}"
    
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return timestamp_str, signature

# ============================================================
# Git
# ============================================================

def get_current_git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", GIT_REPO_DIR, "rev-parse", "--abbrev-ref", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        branch = result.stdout.strip()
        if not branch:
            raise RuntimeError("Unable to determine Git branch.")
        if branch == "HEAD":
            raise RuntimeError("Repository is in detached HEAD state.")
        return branch
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Unable to determine Git branch from {GIT_REPO_DIR}.") from exc

def get_jira_case_from_branch(branch_name: str) -> str:
    branch = branch_name.strip()
    branch = re.sub(r"^(feature|hotfix)-", "", branch, flags=re.IGNORECASE)
    return branch

# ============================================================
# Google Apps Script Web App Integration
# ============================================================

def find_jira_case(jira_case: str) -> Optional[Dict]:
    """
    Search for the Jira case by sending an HMAC-signed request to Apps Script.
    """
    if not GAS_API_KEY:
        raise RuntimeError(
            "GAS_API_KEY environment variable is not configured."
        )

    # Generate timestamp and HMAC signature
    timestamp_str, signature = generate_hmac_signature(jira_case, GAS_API_KEY)

    print(f"\nSearching Google Sheet via Apps Script for Jira case: {jira_case}")
    
    url = (
        f"{GAS_WEB_APP_URL}"
        f"?jira={jira_case}"
        f"&timestamp={timestamp_str}"
        f"&signature={signature}"
    )
    
    try:
        response = requests.get(url, allow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error calling Apps Script Web App: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Web App returned HTTP {response.status_code}. "
            f"Please ensure GAS_WEB_APP_URL is correct."
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("Received invalid JSON from the Web App. Check deployment URL and server logs.")

    if "error" in data:
        raise RuntimeError(f"Apps Script Server Error: {data['error']}")

    if not data.get("found"):
        return None

    print(f"\n✅ Jira case found in worksheet: {data['worksheet_name']}")
    print(f"   Row    : {data['row_index'] + 1}")
    print(f"   Column : {data['column_index'] + 1}")

    return {
        "worksheet_name": data["worksheet_name"],
        "rows": data["rows"],
        "row_index": data["row_index"],
        "column_index": data["column_index"],
    }

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

    for row_index in range(branch_row + 1, len(rows)):
        row = rows[row_index]
        if not row:
            continue

        question = str(row[0]).strip()
        if is_section_heading(question):
            continue

        answer = str(row[branch_column]).strip() if branch_column < len(row) else ""
        answer_normalized = normalize(answer)

        item = {
            "row": row_index + 1,
            "question": question,
            "answer": answer or "<EMPTY>",
        }

        if not answer_normalized or answer_normalized in INVALID_ANSWERS:
            failed_items.append(item)
            continue

        if answer_normalized in VALID_ANSWERS or is_valid_regex_answer(answer):
            passed_items.append(item)
            continue

        failed_items.append(item)

    return passed_items, failed_items

# ============================================================
# Output
# ============================================================

def print_validation_result(
    jira_case: str, worksheet_name: str, passed_items: List[Dict], failed_items: List[Dict]
) -> bool:
    print("\n" + "=" * 70)
    print(" Google Sheet Checklist Validation")
    print("=" * 70)
    print(f"\nJira case : {jira_case}")
    print(f"Worksheet : {worksheet_name}")

    print("\n" + "-" * 70)
    print(f"✅ PASSED / COMPLETED ({len(passed_items)})")
    print("-" * 70)
    if passed_items:
        for item in passed_items:
            print(f"[{item['answer']}] {item['question']}")
    else:
        print("No completed checklist items found.")

    print("\n" + "-" * 70)
    print(f"❌ FAILED / MISSING ({len(failed_items)})")
    print("-" * 70)
    if failed_items:
        for item in failed_items:
            print(f"[{item['answer']}] {item['question']}")
    else:
        print("No failed checklist items.")

    print("\n" + "=" * 70)
    if failed_items:
        print("❌ CHECKLIST VALIDATION FAILED")
        print(f"Completed : {len(passed_items)}")
        print(f"Failed    : {len(failed_items)}")
        print("=" * 70 + "\n")
        return False

    print("✅ CHECKLIST VALIDATION PASSED")
    print(f"Completed : {len(passed_items)}")
    print(f"Failed    : {len(failed_items)}")
    print("=" * 70 + "\n")
    return True

# ============================================================
# Main
# ============================================================

def main():
    try:
        if not GAS_WEB_APP_URL:
            raise RuntimeError(
                "GAS_WEB_APP_URL environment variable is not configured."
            )

        print("\nDEBUG: Reading Git branch...")
        branch_name = get_current_git_branch()
        print(f"Git branch: {branch_name}")

        jira_case = get_jira_case_from_branch(branch_name)
        print(f"Jira case: {jira_case}")

        result = find_jira_case(jira_case)

        if result is None:
            print("\n" + "=" * 70)
            print("❌ CHECKLIST VALIDATION FAILED")
            print("=" * 70)
            print(f"\nJira case '{jira_case}' was not found in any worksheet.")
            print("\nPlease add the Jira case to the Google Sheet before creating the PR.\n")
            sys.exit(1)

        passed_items, failed_items = validate_checklist(
            rows=result["rows"],
            branch_row=result["row_index"],
            branch_column=result["column_index"],
        )

        success = print_validation_result(
            jira_case=jira_case,
            worksheet_name=result["worksheet_name"],
            passed_items=passed_items,
            failed_items=failed_items,
        )

        sys.exit(0 if success else 1)

    except Exception as exc:
        print("\n" + "=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"\nException type: {type(exc).__name__}")
        print(f"Exception: {exc}\n")
        raise

if __name__ == "__main__":
    main()