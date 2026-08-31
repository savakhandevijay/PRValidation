#!/bin/sh
set -u

# Base branch parameter (defaults to develop)
BASE_BRANCH="${1:-develop}"

# Compute root paths relative to script location
PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
GIT_ROOT="${PROJECT_ROOT}/src"

# Validate Git repository
if [ ! -d "${GIT_ROOT}/.git" ]; then
    echo "❌ Git repository not found:"
    echo "   ${GIT_ROOT}"
    exit 1
fi

CURRENT_BRANCH="$(git -C "${GIT_ROOT}" branch --show-current 2>/dev/null || echo "detached")"

# Setup temporary file & cleanup trap
CHANGED_FILES="$(mktemp)"
trap 'rm -f "${CHANGED_FILES}"' EXIT

# ------------------------------------------------------------
# Return changed files
#
# Added:
# A = Added
# C = Copied
# M = Modified
# R = Renamed
# ------------------------------------------------------------

# Helper function to get changed files from Git
get_changed_files() {
    FILE_PATTERN="${1:-*.php}"
    git -C "${GIT_ROOT}" diff --name-only --diff-filter=ACMR "origin/${BASE_BRANCH}...HEAD" -- "${FILE_PATTERN}"
}