#!/bin/sh

# Load shared setup
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
. "${SCRIPT_DIR}/lib/common.sh"

echo "=========================================="
echo "PHP Lint"
echo "=========================================="
echo "Project root  : ${PROJECT_ROOT}"
echo "Git root      : ${GIT_ROOT}"
echo "Current branch: ${CURRENT_BRANCH}"
echo "Base branch   : ${BASE_BRANCH}"
echo

failed=0
file_count=0

get_changed_files '*.php' | while IFS= read -r file; do
    case "$file" in www/wss2/vendor/*|www/wss2/api/runtime/*|www/wss2/api/views/*|www/wss2/api/web/*) continue; esac
    [ -f "${GIT_ROOT}/${file}" ] || continue

    file_count=$((file_count + 1))

    if ! php -l "${GIT_ROOT}/${file}"; then
        echo "❌ Syntax error: ${file}"
        failed=1
    fi
done

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