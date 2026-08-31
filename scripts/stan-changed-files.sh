#!/bin/sh

# Load shared setup
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
. "${SCRIPT_DIR}/lib/common.sh"

PHPSTAN_CONFIG="${PROJECT_ROOT}/phpstan.neon"

echo "=========================================="
echo "PHPStan - Changed Files Validation"
echo "=========================================="
echo "Project root  : ${PROJECT_ROOT}"
echo "Git root      : ${GIT_ROOT}"
echo "Current branch: ${CURRENT_BRANCH}"
echo "PHPStan config: ${PHPSTAN_CONFIG}"
echo "Base branch   : ${BASE_BRANCH}"
echo

if [ ! -f "${PHPSTAN_CONFIG}" ]; then
    echo "❌ PHPStan configuration not found:"
    echo "   ${PHPSTAN_CONFIG}"
    exit 1
fi

get_changed_files '*.php' > "${CHANGED_FILES}"

FILTERED_FILES="$(mktemp)"

while IFS= read -r file; do
    case "$file" in
        *vendor/* | *temp/* | *api/runtime/* | *api/web/assets/* | *grpcadapter/* | *common/tests/* | *web/assets/*)
            continue
            ;;
    esac
    [ -f "${GIT_ROOT}/${file}" ] || continue
    printf '%s\n' "${GIT_ROOT}/${file}"
done < "${CHANGED_FILES}" > "${FILTERED_FILES}"

mv "${FILTERED_FILES}" "${CHANGED_FILES}"

if [ ! -s "${CHANGED_FILES}" ]; then
    echo
    echo "✅ No changed PHP files found."
    exit 0
fi

echo
echo "Changed PHP files:"
echo "------------------------------------------"
cat "${CHANGED_FILES}"
echo "------------------------------------------"
echo

set --
while IFS= read -r file; do
    set -- "$@" "$file"
done < "${CHANGED_FILES}"

echo "Running PHPStan..."
echo

cd "${PROJECT_ROOT}" || exit 1

# Ensure target directory exists before saving log
mkdir -p /var/logs

php "${PROJECT_ROOT}/vendor/bin/phpstan" analyse \
    --configuration="${PHPSTAN_CONFIG}" \
    --memory-limit=1G \
    --error-format=table \
    --no-progress \
    --no-ansi \
    "$@" \
    > "/var/logs/${CURRENT_BRANCH}_stan_report.log" 2>&1

STATUS=$?
echo

if [ "${STATUS}" -ne 0 ]; then
    echo "❌ PHPStan validation failed."
    exit "${STATUS}"
fi

echo "✅ PHPStan validation passed."
exit 0