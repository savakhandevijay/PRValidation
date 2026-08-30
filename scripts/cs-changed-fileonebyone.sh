#!/bin/sh
set -u

BASE_BRANCH="${1:-develop}"

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
GIT_ROOT="${PROJECT_ROOT}/src"

changed_files="$(mktemp)"
trap 'rm -f "${changed_files}"' EXIT

sh "${PROJECT_ROOT}/scripts/lib/changed-files.sh" "${BASE_BRANCH}" '*.php' > "${changed_files}"

if [ ! -s "${changed_files}" ]; then
    echo "No changed PHP files found."
    exit 0
fi

echo "PHP-CS-Fixer validation"
echo "Base branch: ${BASE_BRANCH}"
echo

failed=0
file_count=0

while IFS= read -r file; do

    case "$file" in www/wss2/vendor/*|www/wss2/api/runtime/*|www/wss2/api/views/*|www/wss2/api/web/*) continue; esac

    [ -f "${GIT_ROOT}/${file}" ] || continue

    file_count=$((file_count + 1))

    echo "Checking: ${file}"

    if ! php "${PROJECT_ROOT}/vendor/bin/php-cs-fixer" check \
        --config="${PROJECT_ROOT}/.php-cs-fixer.php" \
        --path-mode=intersection \
        --diff \
        "${GIT_ROOT}/${file}"
    then
        failed=1
    fi

done < "${changed_files}"

echo

if [ "${file_count}" -eq 0 ]; then
    echo "No changed PHP files found."
    exit 0
fi

if [ "${failed}" -ne 0 ]; then
    echo "❌ PHP-CS-Fixer validation failed."
    echo "Run PHP-CS-Fixer locally to fix the changed files."
    exit 1
fi

echo "✅ PHP-CS-Fixer validation passed."
exit 0