# PR Code Validation

Automated pull-request validation toolkit for a legacy PHP/Yii2 application.

The project is designed to move repetitive PR-review checks away from manual review and into automated validation.

The current setup supports:

- PHP syntax validation for changed files
- PHP-CS-Fixer validation for changed files
- PHPStan validation for changed files
- PHPStan custom architecture rules
- Yii2 application autoloading for PHPStan
- PHPStan baseline support for legacy code
- Branch/checklist validation using Google Sheets
- Git-based changed-file detection shared across validation scripts

---

## 1. Project Structure

```text
PRCheck/
│
├── composer.json
│
├── phpstan.neon
├── phpstan-baseline.neon
│
├── phpstan/
│   └── Rules/
│       └── Yii2/
│           └── NoActiveRecordInControllerRule.php
│
├── scripts/
│   │
│   ├── lib/
│   │   └── changed-files.sh
│   │
│   ├── lint-changed-files.sh
│   ├── cs-changed-files.sh
│   ├── stan-changed-files.sh
│   │
│   └── checks/
│       ├── validate-branch-checklist.py
│       └── requirements.txt
│
├── credentials/
│   └── google-service-account.json
│
├── var/
│   └── phpstan/
│
└── src/
    └── www/
        └── wss2/
            ├── .git/
            ├── composer.json
            ├── vendor/
            ├── api/
            ├── common/
            ├── backend/
            ├── frontend/
            └── ...
```

### Directory responsibilities

| Directory | Purpose |
|---|---|
| `src/www/wss2` | Actual Yii2 ecommerce application and Git repository |
| `scripts/lib` | Shared Git/change-detection utilities |
| `scripts` | Validation scripts |
| `scripts/checks` | Business/process validation scripts |
| `phpstan` | Custom PHPStan architecture rules |
| `vendor` | PRCheck/tooling Composer dependencies |
| `src/www/wss2/vendor` | Actual Yii2 application dependencies |
| `var/phpstan` | PHPStan cache/temp files |
| `credentials` | Local-only Google credentials; never commit |

---

# 2. Architecture

The repository has two different kinds of validation.

## Code validation

PHP source code is validated with:

```text
PR
 │
 ├── PHP syntax
 ├── PHP-CS-Fixer
 ├── PHPStan
 └── PHPUnit
```

## Business/process validation

Non-code engineering rules are validated separately:

```text
PR
 │
 ├── Branch exists in checklist
 ├── Required checklist completed
 ├── Jira information
 └── Other engineering process checks
```

PHPStan is used for **PHP/code rules**.

Shell/Python scripts are used for **Git, Jira, Google Sheets, release and process rules**.

Do not make PHPStan perform external Google Sheets/Jira API calls.

---

# 3. Prerequisites

## Required

Install:

- PHP 8.4
- Composer 2
- Git
- Python 3.x
- Bash or POSIX-compatible `/bin/sh`

The PHP version used by PRCheck should match the PHP version used by the target application as closely as possible.

Check:

```bash
php --version
```

```bash
composer --version
```

```bash
python3 --version
```

```bash
git --version
```

---

# 4. Install Composer Dependencies

From the PRCheck root:

```bash
composer install
```

The tooling Composer project contains PHPStan/PHP-CS-Fixer dependencies.

The actual Yii2 application has its own Composer dependencies under:

```text
src/www/wss2/vendor/
```

Do not replace the application dependency tree with the PRCheck dependency tree.

---

# 5. Composer Configuration

The root `composer.json` should contain the required development tools and PSR-4 mapping for custom PHPStan rules.

Example:

```json
{
    "autoload-dev": {
        "psr-4": {
            "PHPStanRules\\": "phpstan/"
        }
    },
    "scripts": {
        "lint": "sh ./scripts/lint-changed-files.sh develop",
        "cs-check": "sh ./scripts/cs-changed-files.sh develop",
        "stan": "php vendor/bin/phpstan analyse --memory-limit=512M",
        "stan-changed": "sh ./scripts/stan-changed-files.sh develop"
    }
}
```

After changing `autoload-dev`, always run:

```bash
composer dump-autoload -o
```

---

# 6. Shared Changed-File Logic

The common Git logic is located at:

```text
scripts/lib/changed-files.sh
```

Its responsibility is only to identify files changed relative to a base branch.

Example:

```bash
sh scripts/lib/changed-files.sh develop '*.php'
```

Example output:

```text
api/controllers/ProductController.php
common/models/Product.php
api/services/ProductService.php
```

The paths returned are relative to:

```text
src/www/wss2/
```

The individual validators consume this list.

---

# 7. PHP Syntax Validation

Script:

```text
scripts/lint-changed-files.sh
```

Run locally:

```bash
composer lint
```

Or directly:

```bash
sh ./scripts/lint-changed-files.sh develop
```

The script:

1. Finds PHP files changed against `develop`
2. Ignores vendor/runtime/generated files
3. Runs `php -l` only against changed PHP files
4. Returns exit code `1` if any syntax error exists

No changed PHP files:

```text
✅ No changed PHP files found.
```

---

# 8. PHP-CS-Fixer Validation

Script:

```text
scripts/cs-changed-files.sh
```

Run:

```bash
composer cs-check
```

This validates only PHP files changed relative to the base branch.

CI should use:

```bash
php-cs-fixer check
```

and should not automatically modify the developer's code.

For local fixing, use a separate `cs-fix` command/script.

Expected workflow:

```text
composer cs-check
        ↓
violations found
        ↓
composer cs-fix
        ↓
composer cs-check
        ↓
PASS
```

---

# 9. PHPStan Full Analysis

Run:

```bash
composer stan
```

This performs a full PHPStan analysis of the configured application.

PHPStan uses:

```text
phpstan.neon
```

and:

```text
phpstan-baseline.neon
```

The PHPStan memory limit is configured as:

```bash
--memory-limit=512M
```

The default PHP CLI memory limit may be only:

```text
128M
```

which is generally too small for a large legacy Yii2 application.

Check current PHP CLI memory:

```bash
php -i | grep memory_limit
```

---

# 10. PHPStan Changed-File Analysis

Script:

```text
scripts/stan-changed-files.sh
```

Run:

```bash
composer stan-changed
```

Or:

```bash
sh ./scripts/stan-changed-files.sh develop
```

The intended flow is:

```text
Git
 │
 └── changed PHP files
          │
          ▼
      PHPStan
          │
          ├── Yii2 application autoload
          ├── baseline
          ├── type information
          └── symbol discovery
```

Only the changed files are supplied as PHPStan analysis targets.

However, PHPStan may still need access to other application classes to resolve:

- parent classes
- interfaces
- traits
- method definitions
- properties
- return types
- dependencies

This is why `phpstan.neon` must contain proper Yii2 autoload and symbol-discovery configuration.

---

# 11. PHPStan Yii2 Configuration

The actual Yii2 application is located at:

```text
src/www/wss2
```

The application has its own Composer autoloader:

```text
src/www/wss2/vendor/autoload.php
```

PHPStan should load it through `bootstrapFiles`.

Example:

```neon
parameters:
    bootstrapFiles:
        - %currentWorkingDirectory%/src/www/wss2/vendor/autoload.php
        - %currentWorkingDirectory%/src/www/wss2/vendor/yiisoft/yii2/Yii.php
```

This is important because Yii classes such as:

```text
yii\base\Module
yii\db\ActiveRecord
Yii
```

must be visible to PHPStan.

---

# 12. PHPStan Symbol Discovery

Changed-file-only analysis can produce errors like:

```text
Class app\controllers\WesellorderController
extends unknown class common\components\WssController.
```

This can happen even when:

```text
src/www/wss2/common/components/WssController.php
```

exists and the application executes correctly.

The reason is:

```text
PHPStan analysis target
    = only changed files

but

WssController
    = another application file needed for type discovery
```

Use `scanDirectories` for application source directories that need to be discovered but should not necessarily become analysis targets.

Example:

```neon
parameters:
    scanDirectories:
        - src/www/wss2/common
        - src/www/wss2/api
```

Add only directories that are actually required by your application.

The conceptual distinction is:

```text
paths
    = files PHPStan analyses

scanDirectories
    = files/classes PHPStan may scan to discover symbols
```

---

# 13. Verifying Yii2 Autoloading

Before debugging PHPStan, test the application Composer autoloader directly.

Run:

```bash
php -r "require 'src/www/wss2/vendor/autoload.php'; var_dump(class_exists('yii\\base\\Module'));"
```

Expected:

```text
bool(true)
```

Test the global Yii class:

```bash
php -r "require 'src/www/wss2/vendor/autoload.php'; require 'src/www/wss2/vendor/yiisoft/yii2/Yii.php'; var_dump(class_exists('Yii'));"
```

Expected:

```text
bool(true)
```

If these return `false`, fix the application Composer/bootstrap configuration before debugging PHPStan.

---

# 14. PHPStan Baseline

Legacy applications can contain thousands of existing PHPStan findings.

Do not try to fix all legacy problems before introducing PHPStan into PR validation.

A baseline can capture existing issues:

```bash
vendor/bin/phpstan analyse \
    --memory-limit=512M \
    --generate-baseline=phpstan-baseline.neon
```

Then include it:

```neon
includes:
    - phpstan-baseline.neon
```

The desired behavior is:

```text
Existing legacy problems
        ↓
baseline
        ↓
ignored

New PR problems
        ↓
PHPStan
        ↓
❌ fail
```

The baseline is a temporary mechanism for managing technical debt.

It should not be used to hide framework/autoload configuration problems.

---

# 15. Important Baseline Rule

Errors such as:

```text
Class ... extends unknown class yii\base\Module
```

should generally be fixed through autoloading/symbol discovery rather than blindly added to the baseline.

For example:

```text
yii\base\Module
```

was initially reported as unknown even though it existed under:

```text
src/www/wss2/vendor/
```

The correct solution was to load the application's Composer autoloader.

---

# 16. Testing a PHPStan Custom Rule

Custom rules live under:

```text
phpstan/Rules/
```

Example:

```text
phpstan/
└── Rules/
    └── Yii2/
        └── NoActiveRecordInControllerRule.php
```

Custom rules use PHPStan's:

```php
use PHPStan\Rules\Rule;
```

For PHPStan 2.2.x, register the rule using:

```neon
rules:
    - PHPStanRules\Rules\Yii2\NoActiveRecordInControllerRule
```

The Composer mapping:

```json
"autoload-dev": {
    "psr-4": {
        "PHPStanRules\\": "phpstan/"
    }
}
```

must also exist.

After adding/changing the class:

```bash
composer dump-autoload -o
```

Verify Composer can find it:

```bash
php -r "require 'vendor/autoload.php'; var_dump(class_exists('PHPStanRules\\Rules\\Yii2\\NoActiveRecordInControllerRule'));"
```

Expected:

```text
bool(true)
```

---

# 17. PSR-4 Troubleshooting

If Composer reports:

```text
Class ... does not comply with psr-4 autoloading standard
```

verify that namespace and path match.

For:

```text
phpstan/Rules/Yii2/NoActiveRecordInControllerRule.php
```

the namespace must be:

```php
namespace PHPStanRules\Rules\Yii2;
```

with:

```json
"PHPStanRules\\": "phpstan/"
```

The mapping is:

```text
PHPStanRules\
    ↓
phpstan/

Rules\
    ↓
Rules/

Yii2\
    ↓
Yii2/

NoActiveRecordInControllerRule
```

Then run:

```bash
composer dump-autoload -o
```

---

# 18. Custom Rule Testing Strategy

When creating a custom PHPStan rule, do not immediately write complex business logic.

Test in stages.

## Stage 1 — Prove the rule loads

Use a simple rule that reports a unique test message.

Run:

```bash
vendor/bin/phpstan analyse path/to/TestController.php
```

Expected:

```text
CUSTOM RULE TEST: ...
```

## Stage 2 — Test AST node detection

For example:

```php
Product::find();
```

Confirm that a `StaticCall` is detected.

## Stage 3 — Add type detection

Determine whether:

```text
Product
```

is actually a subclass of:

```text
yii\db\ActiveRecord
```

## Stage 4 — Add the final business rule

Example:

```text
Controller
    +
ActiveRecord query
    ↓
❌ violation
```

This staged approach makes debugging much easier.

---

# 19. Current Example Custom Rule

Current architecture example:

```text
NoActiveRecordInControllerRule
```

Intended rule:

```php
class ProductController extends Controller
{
    public function actionIndex()
    {
        return Product::find()->all();
    }
}
```

should produce an error similar to:

```text
Direct ActiveRecord access is not allowed in controllers.
Use a service or repository instead.
```

while:

```php
class ProductService
{
    public function getProducts()
    {
        return Product::find()->all();
    }
}
```

should be allowed.

---

# 20. Business Rules Should Not Be PHPStan Rules

Rules such as:

```text
Branch must exist in Google Sheet
Checklist must be completed
Jira ticket must exist
Release ticket must exist
PR must contain required metadata
```

are not PHP static-analysis rules.

Keep these under:

```text
scripts/checks/
```

For example:

```text
scripts/checks/
└── validate-branch-checklist.py
```

The architecture should remain:

```text
PHP/code rule
    → PHPStan

Git rule
    → Shell

External/business-process rule
    → Python/API
```

---

# 21. Google Sheet Branch Checklist

The branch checklist validator expects a spreadsheet similar to:

| Branch | Jira | DB Review | API Review | Tests | Rollback |
|---|---|---|---|---|---|
| feature/CEX-123 | CEX-123 | YES | YES | YES | YES |
| feature/CEX-456 | CEX-456 | YES | NO | YES | YES |

Run locally:

```bash
python3 scripts/checks/validate-branch-checklist.py feature/CEX-123
```

The script returns:

```text
0
```

when validation passes.

It returns:

```text
1
```

when validation fails.

Example failure:

```text
❌ Branch 'feature/CEX-999' was not found in the Google Sheet.
```

---

# 22. Python Dependencies

Create:

```text
scripts/checks/requirements.txt
```

Example:

```text
google-api-python-client
google-auth
```

Install:

```bash
python3 -m pip install -r scripts/checks/requirements.txt
```

---

# 23. Google Credentials

The branch checklist validator uses a Google service account.

Local credential path:

```text
credentials/google-service-account.json
```

Do not commit it.

Add to `.gitignore`:

```gitignore
credentials/
*.json
```

For CI, use GitHub secrets or preferably workload identity federation instead of committing a service-account key.

---

# 24. Debugging Guide

## Problem: `mapfile: command not found`

`mapfile` is a Bash-specific command.

Prefer POSIX-compatible shell implementations for scripts that must run inside minimal Alpine containers.

Check:

```bash
echo "$SHELL"
```

and:

```bash
bash --version
```

Avoid depending on Bash unless Bash is intentionally installed.

---

## Problem: Composer says:

```text
You made a reference to a non-existent script @bash ...
```

Do not use:

```json
"lint": "@bash ./scripts/lint-changed-files.sh develop"
```

`@name` is interpreted by Composer as a reference to another Composer script.

Use:

```json
"lint": "sh ./scripts/lint-changed-files.sh develop"
```

or:

```json
"lint": "bash ./scripts/lint-changed-files.sh develop"
```

---

## Problem: Git repository not found

The application Git repository is under:

```text
src/www/wss2/
```

Verify:

```bash
ls -la src/www/wss2/.git
```

The validation scripts should use:

```text
PROJECT_ROOT
    ↓
src/www/wss2
    ↓
Git repository
```

not:

```text
project-root/.git
```

---

## Problem: No changed files are detected

Run:

```bash
sh scripts/lib/changed-files.sh develop '*.php'
```

Verify the branch exists:

```bash
git -C src/www/wss2 branch
```

Verify the remote branch:

```bash
git -C src/www/wss2 branch -r
```

Fetch it:

```bash
git -C src/www/wss2 fetch origin develop
```

Then compare manually:

```bash
git -C src/www/wss2 diff \
    --name-only \
    --diff-filter=ACMR \
    origin/develop...HEAD \
    -- '*.php'
```

---

## Problem: PHPStan memory error

Error:

```text
PHPStan process crashed because it reached configured PHP memory limit: 128M
```

Run:

```bash
vendor/bin/phpstan analyse --memory-limit=512M
```

The Composer script should also contain:

```json
"stan": "php vendor/bin/phpstan analyse --memory-limit=512M"
```

Check current PHP memory:

```bash
php -i | grep memory_limit
```

---

## Problem: PHPStan reports more than 1,000 errors

PHPStan limits table output.

Use:

```bash
PHPSTAN_TABLE_ERROR_FORMATTER_FORCE_SHOW_ALL_ERRORS=1 \
vendor/bin/phpstan analyse --memory-limit=512M
```

Or redirect the result:

```bash
vendor/bin/phpstan analyse \
    --memory-limit=512M \
    --error-format=raw \
    > phpstan-errors.txt 2>&1
```

Then search:

```bash
grep -F "unknown class" phpstan-errors.txt
```

---

## Problem: Yii2 class is reported as unknown

Example:

```text
Class ... extends unknown class yii\base\Module
```

First test:

```bash
php -r "require 'src/www/wss2/vendor/autoload.php'; var_dump(class_exists('yii\\base\\Module'));"
```

Expected:

```text
bool(true)
```

If false, inspect the application Composer installation.

If true, make sure `phpstan.neon` contains:

```neon
bootstrapFiles:
    - %currentWorkingDirectory%/src/www/wss2/vendor/autoload.php
```

For the global Yii class:

```neon
bootstrapFiles:
    - %currentWorkingDirectory%/src/www/wss2/vendor/autoload.php
    - %currentWorkingDirectory%/src/www/wss2/vendor/yiisoft/yii2/Yii.php
```

---

## Problem: Application class is reported as unknown only during changed-file analysis

Example:

```text
Class app\controllers\WesellorderController
extends unknown class common\components\WssController.
```

If the class exists:

```bash
find src/www/wss2 -name 'WssController.php'
```

the issue is probably symbol discovery.

Add the relevant application directory to:

```neon
scanDirectories:
```

For example:

```neon
scanDirectories:
    - src/www/wss2/common
```

Do not add these problems to the baseline simply to make the error disappear.

---

## Problem: Custom PHPStan rule class is not found

Verify:

```bash
php -r "require 'vendor/autoload.php'; var_dump(class_exists('PHPStanRules\\Rules\\Yii2\\NoActiveRecordInControllerRule'));"
```

Expected:

```text
bool(true)
```

If false:

```bash
composer dump-autoload -o
```

Then verify:

```text
phpstan/Rules/Yii2/NoActiveRecordInControllerRule.php
```

contains:

```php
namespace PHPStanRules\Rules\Yii2;
```

and `composer.json` contains:

```json
"autoload-dev": {
    "psr-4": {
        "PHPStanRules\\": "phpstan/"
    }
}
```

---

## Problem: PHPStan custom rule causes an Internal error

A previous mistake was:

```php
$scope->getType($node->class);
```

for a `StaticCall`.

For:

```php
Product::find();
```

`$node->class` is a `PhpParser\Node\Name`, not a `PhpParser\Node\Expr`.

Do not pass `Node\Name` to APIs requiring `Node\Expr`.

When debugging an AST rule, first inspect:

```php
get_class($node)
```

and:

```php
get_class($node->class)
```

before selecting a PHPStan API.

---

## Problem: Composer PSR-4 warning

Example:

```text
Class PHPStanRules\Yii2\... does not comply with psr-4
```

Check namespace/path alignment.

For:

```text
phpstan/Rules/Yii2/NoActiveRecordInControllerRule.php
```

use:

```php
namespace PHPStanRules\Rules\Yii2;
```

Then:

```bash
composer dump-autoload -o
```

---

## Problem: PHP-CS-Fixer exits with code 1

This can be expected.

`php-cs-fixer check` returns a non-zero exit code when formatting violations are found.

That means:

```text
Composer error code 1
```

does not automatically mean the script is broken.

Look at the PHP-CS-Fixer output immediately before the final Composer message.

To fix locally, run the project's fix command.

---

# 25. Recommended Local Validation Commands

From the project root:

```bash
composer lint
```

```bash
composer cs-check
```

```bash
composer stan
```

```bash
composer stan-changed
```

Run all relevant checks before opening a PR.

---

# 26. Recommended PR Validation Flow

The target GitHub Actions workflow should eventually look like:

```text
Pull Request
     │
     ├── PHP syntax
     │      └── changed PHP files
     │
     ├── PHP-CS-Fixer
     │      └── changed PHP files
     │
     ├── PHPStan
     │      └── changed PHP files
     │
     ├── PHPUnit
     │
     ├── Custom PHPStan architecture rules
     │
     └── Business/process validation
            ├── Branch checklist
            ├── Jira validation
            └── Other required checks
```

Only when all required checks pass should the PR move to human technical review.

---

# 27. Design Principle

The purpose of PRCheck is not to eliminate human review.

The purpose is to remove repetitive human review.

Automate:

```text
Formatting
Syntax
Static analysis
Known architecture violations
Required metadata
Checklist validation
Repeated process checks
```

Keep human review focused on:

```text
Architecture
Business correctness
Performance
Security
Production risk
API/gRPC compatibility
Database impact
Design decisions
```

This allows technical leads to spend more time on architecture, mentoring and technical learning rather than repeatedly identifying the same mechanical problems.

---

# 28. Recommended Future Improvements

The project can gradually evolve to include:

```text
PR risk scoring
    ↓
Database-change detection
    ↓
gRPC/protobuf-change detection
    ↓
Docker/RoadRunner-change detection
    ↓
Jira validation
    ↓
Release automation
    ↓
AI-assisted PR review
```

The key rule should remain:

> Every repeated manual review comment that is objective and machine-detectable is a candidate for automation.

---

# 29. Quick Start

```bash
# 1. Clone repository
git clone <repository-url>

# 2. Enter project
cd PRCheck

# 3. Install PHP dependencies
composer install

# 4. Generate Composer autoload
composer dump-autoload -o

# 5. Verify Yii2 autoload
php -r "require 'src/www/wss2/vendor/autoload.php'; var_dump(class_exists('yii\\base\\Module'));"

# 6. Check changed PHP files
sh scripts/lib/changed-files.sh develop '*.php'

# 7. PHP lint
composer lint

# 8. PHP-CS-Fixer
composer cs-check

# 9. Full PHPStan
composer stan

# 10. PHPStan changed files
composer stan-changed

# 11. Branch checklist
python3 scripts/checks/validate-branch-checklist.py feature/CEX-123
```

---

# 30. Exit Codes

All validation scripts should follow this convention:

```text
0 = validation passed
1 = validation failed
2 = configuration/usage error
```

This makes the scripts suitable for both local development and GitHub Actions.

---

## Goal

The desired end state is:

```text
Developer raises PR
        │
        ▼
Automated validation
        │
        ├── Mechanical problems → developer fixes
        │
        └── High-value technical issues → human reviewer
                                      │
                                      ▼
                                  Merge faster
                                      │
                                      ▼
                            More technical focus
```

PRCheck is intended to turn repeated engineering knowledge and review practices into executable checks while keeping human technical judgment where it provides the most value.