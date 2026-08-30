#!/bin/sh

set -u

BASE_BRANCH="${1:-develop}"

# Project root = directory containing this script's parent directory.
PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

# Your actual Git repository / application directory.
GIT_ROOT="${PROJECT_ROOT}/src"

failed=0
file_count=0

while IFS= read -r file; do

    # Ignore directories that should not be checked.
    case "$file" in www/wss2/vendor/*|www/wss2/api/runtime/*|www/wss2/api/views/*|www/wss2/api/web/*) continue; esac

    [ -f "${GIT_ROOT}/${file}" ] || continue

    file_count=$((file_count + 1))

    echo "Linting: ${file}"

    if ! php -l "${GIT_ROOT}/${file}"; then
        echo "❌ Syntax error: ${file}"
        failed=1
    fi

done <<EOF
$(sh "${PROJECT_ROOT}/scripts/lib/changed-files.sh" "${BASE_BRANCH}" '*.php')
EOF

echo

if [ "${file_count}" -eq 0 ]; then
    echo "No changed PHP files found."
    exit 0
fi

if [ "${failed}" -ne 0 ]; then
    echo "❌ PHP syntax validation failed."
    exit 1
fi

echo "✅ PHP syntax validation passed."