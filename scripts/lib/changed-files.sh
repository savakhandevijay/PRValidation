#!/bin/sh

set -eu

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BASE_BRANCH="${1:-develop}"
FILE_PATTERN="${2:-*.php}"

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

PROJECT_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)"

# Actual Git repository
GIT_ROOT="${PROJECT_ROOT}/src"

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

if [ ! -d "${GIT_ROOT}/.git" ]; then
    echo "❌ Git repository not found: ${GIT_ROOT}"
    exit 1
fi

cd "${GIT_ROOT}"

echo "Fetching Base branch: origin/${BASE_BRANCH}" >/dev/null 2>&1 || {
    echo "❌ Failed to fetch origin/${BASE_BRANCH}"
    exit 1
}

# ------------------------------------------------------------
# Return changed files
#
# Added:
# A = Added
# C = Copied
# M = Modified
# R = Renamed
# ------------------------------------------------------------

# changed_files="$(mktemp)"

# git diff --name-only --diff-filter=ACMRTUXB  "origin/${BASE_BRANCH}...HEAD" -- '*.php' > "${changed_files}"

git diff --name-only --diff-filter=ACMR "origin/${BASE_BRANCH}...HEAD" -- "${FILE_PATTERN}"