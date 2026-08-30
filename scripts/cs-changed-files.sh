#!/bin/sh
set -u

BASE_BRANCH="${1:-develop}"

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
GIT_ROOT="${PROJECT_ROOT}/src"
CHANGED_FILES="$(mktemp)"

trap 'rm -f "${CHANGED_FILES}"' EXIT

sh "${PROJECT_ROOT}/scripts/lib/changed-files.sh" "${BASE_BRANCH}" '*.php' |
while IFS= read -r file; do

    case "$file" in www/wss2/vendor/*|www/wss2/api/runtime/*|www/wss2/api/views/*|www/wss2/api/web/*) continue; esac

    [ -f "${GIT_ROOT}/${file}" ] || continue

    printf '%s\n' "${GIT_ROOT}/${file}"
done > "${CHANGED_FILES}"

if [ ! -s "${CHANGED_FILES}" ]; then
    echo "✅ No changed PHP files found."
    exit 0
fi

echo "Changed PHP files:"
cat "${CHANGED_FILES}"
echo

echo "Running PHP-CS-Fixer..."
echo

# PHP source file paths normally don't contain spaces,
# so xargs is appropriate for this project.
xargs php "${PROJECT_ROOT}/vendor/bin/php-cs-fixer" check \
    --config="${PROJECT_ROOT}/.php-cs-fixer.php" \
    --diff \
    < "${CHANGED_FILES}"

STATUS=$?

echo

if [ "${STATUS}" -ne 0 ]; then
    echo "❌ PHP-CS-Fixer validation failed."
    echo
    echo "To automatically fix the changed files, run:"
    echo
    echo "  composer cs-fix"
    echo
    exit "${STATUS}"
fi

echo "✅ PHP-CS-Fixer validation passed."