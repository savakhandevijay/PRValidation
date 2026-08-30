#!/bin/sh

set -u

BASE_BRANCH="${1:-develop}"

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
GIT_ROOT="${PROJECT_ROOT}/src"
PHPSTAN_CONFIG="${PROJECT_ROOT}/phpstan.neon"

CHANGED_FILES="$(mktemp)"

trap 'rm -f "${CHANGED_FILES}"' EXIT

echo "=========================================="
echo "PHPStan - Changed Files Validation"
echo "=========================================="
echo "Project root  : ${PROJECT_ROOT}"
echo "Git root      : ${GIT_ROOT}"
echo "PHPStan config: ${PHPSTAN_CONFIG}"
echo "Base branch   : ${BASE_BRANCH}"
echo

# ------------------------------------------------------------
# Validate repository/configuration
# ------------------------------------------------------------

if [ ! -d "${GIT_ROOT}/.git" ]; then
    echo "❌ Git repository not found:"
    echo "   ${GIT_ROOT}"
    exit 1
fi

if [ ! -f "${PHPSTAN_CONFIG}" ]; then
    echo "❌ PHPStan configuration not found:"
    echo "   ${PHPSTAN_CONFIG}"
    exit 1
fi

# ------------------------------------------------------------
# Get changed PHP files
#
# changed-files.sh returns paths relative to src/www/wss2.
# ------------------------------------------------------------

sh "${PROJECT_ROOT}/scripts/lib/changed-files.sh" "${BASE_BRANCH}" '*.php' > "${CHANGED_FILES}"

# ------------------------------------------------------------
# Remove files that should not be analysed
# ------------------------------------------------------------

FILTERED_FILES="$(mktemp)"

while IFS= read -r file; do

    case "$file" in
        *vendor/* | \
        *temp/* | \
        *api/runtime/* | \
        *api/web/assets/* | \
        *grpcadapter/* | \
        *common/tests/* | \
        *web/assets/*)
            continue
            ;;
    esac

    [ -f "${GIT_ROOT}/${file}" ] || continue

    printf '%s\n' "${GIT_ROOT}/${file}"

done < "${CHANGED_FILES}" > "${FILTERED_FILES}"

mv "${FILTERED_FILES}" "${CHANGED_FILES}"

# ------------------------------------------------------------
# No changed PHP files
# ------------------------------------------------------------

if [ ! -s "${CHANGED_FILES}" ]; then
    echo
    echo "✅ No changed PHP files found."
    exit 0
fi

# ------------------------------------------------------------
# Display changed files
# ------------------------------------------------------------

echo
echo "Changed PHP files:"
echo "------------------------------------------"

cat "${CHANGED_FILES}"

echo "------------------------------------------"
echo

# ------------------------------------------------------------
# Build PHPStan arguments
# ------------------------------------------------------------

set --

while IFS= read -r file; do
    set -- "$@" "$file"
done < "${CHANGED_FILES}"

# ------------------------------------------------------------
# Run PHPStan ONCE
#
# IMPORTANT:
# We intentionally run PHPStan from PROJECT_ROOT so that
# phpstan.neon paths/bootstrapFiles/scanDirectories resolve
# relative to the config file.
# ------------------------------------------------------------

echo "Running PHPStan..."
echo

cd "${PROJECT_ROOT}" || exit 1

php "${PROJECT_ROOT}/vendor/bin/phpstan" analyse \
    --configuration="${PHPSTAN_CONFIG}" \
    --memory-limit=1G \
    --error-format=table \
    "$@" \
    > ${PROJECT_ROOT}/Reports/${BASE_BRANCH}_stan_report.log 2>&1

STATUS=$?

echo

if [ "${STATUS}" -ne 0 ]; then
    echo "❌ PHPStan validation failed."
    exit "${STATUS}"
fi

echo "✅ PHPStan validation passed."
exit 0
