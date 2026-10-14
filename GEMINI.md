# GEMINI.md

This file provides project-level instructions, context, coding standards, and safety constraints for AI assistants operating within this repository.

---

## 1. Project Context

- **Purpose & Overview**: 
  This repository is an automated Pull Request (PR) validation and code review toolkit for a legacy Yii2 application (Advanced Application Template). It automates code quality, architectural compliance, and security checks on feature branches before code is merged.

- **Runtime & Environment**:
  - **PHP Version**: PHP 8.4+ CLI.
  - **Container Environment**: Alpine Linux (`php:8.4-cli-alpine`), defined in `Dockerfile` and orchestrated via `docker-compose.yml`.
  - **Key System & PHP Extensions**: `bcmath`, `ctype`, `gd`, `iconv`, `mbstring`, `mysqli`, `opcache`, `pcntl`, `pdo_mysql`, `pdo_sqlite`, `simplexml`, `sockets`, `zip`, `memcached`, `msgpack`, `igbinary`, `apcu`, and Python 3.

- **Repository Layout & Target Repository (`src/`)**:
  - The `src/` directory contains the Git clone of the GitHub application repository (`src/www/wss2`).
  - **PR Validation Workflow**:
    1. Fetch the latest PR branch under the `src/` folder:
       ```bash
       git -C src fetch origin <feature-branch>
       git -C src checkout <feature-branch>
       ```
    2. Run the validation toolchain against the target base branch (`develop` by default):
       - Syntax check: `composer lint` (invokes `scripts/lint-changed-files.sh`)
       - Code style check: `composer cs-check` (invokes `scripts/cs-changed-files.sh`)
       - Static analysis & custom architecture rules: `composer stan` (invokes `scripts/stan-changed-files.sh`)
       - AI-assisted diff review: `scripts/pr-review.sh`
       - Checklist validation: `composer dev-check` (`scripts/check_google_sheet.py`)
  - **Coding Standard Rules Path**:
    - Centralized PHP standards and agent rules are maintained at `.agents/rules/PHP_standards_rules.md`. Always check and enforce these rules when reviewing or writing code for feature branches.

- **Project Directory Breakdown**:
  - `src/www/wss2/`: Core Yii2 application (Advanced Template):
    - `api/`: REST API application and controllers.
    - `common/`: Shared models, components, configurations, and domain libraries (`common/lib/`).
    - `console/`: Console commands and batch processes.
    - `environments/`: Environment-specific configurations and encrypted secrets (`.enc`).
  - `phpstan/`: Custom PHPStan rules located in `phpstan/Rules/Wss/`:
    - `NoActiveRecordInControllerRule`: Prohibits ActiveRecord / direct DB calls in controllers.
    - `ReadWriteDatabaseRule`: Enforces DB read/write split (`repDb` vs `db`).
    - `ControllerMutationMustVerifyAccessTokenRule`: Enforces token verification on mutations.
    - `RawSqlMustUseParametersRule`: Guards against SQL injection in raw SQL queries.
    - `AppsettingUsageRule`, `FormErrorLocationRule`, `NamingConventionRule`.
  - `scripts/`: Tooling scripts for git diff inspection, linting, code sniffing, and CI automation.
  - `logs/`: Storage for PHPStan and validation run outputs (e.g., `/var/logs/*_stan_report.log`).

---

## 2. Coding Standards

All code within the Yii2 application must strictly follow these principles:

1. **Controller Architecture & Separation of Concerns**:
   - **Never write business logic, database queries, or 3rd-party API calls directly inside controllers.**
   - Controllers must act solely as thin HTTP orchestrators: receive input, validate request parameters, delegate execution, and return responses.
   - **Always delegate to domain libraries (`common/lib/`) or dedicated service classes.**
   - Do not invoke ActiveRecord methods (`find()`, `findOne()`, `save()`, `delete()`, `updateAll()`) or raw database calls (`createCommand()`) inside controllers (enforced by `NoActiveRecordInControllerRule`).

2. **Database Read/Write Splitting (`repDb` vs `db`)**:
   - **Queries (`SELECT`)**: Always use `repDb` (`Yii::$app->repDb`) for all read-only database operations:
     - Methods: `query()`, `queryAll()`, `queryOne()`, `queryScalar()`, `queryColumn()`, `queryBatch()`, `all()`, `one()`, `scalar()`.
   - **Mutations (`INSERT`, `UPDATE`, `DELETE`)**: Always use `db` (`Yii::$app->db`) for write operations:
     - Methods: `execute()`, `insert()`, `update()`, `delete()`, `upsert()`, `batchInsert()`.
   - Never use `Yii::$app->db` for read queries or `Yii::$app->repDb` for mutations (enforced by `ReadWriteDatabaseRule`).
   - All raw SQL queries executed via `createCommand()` must use parameter binding to prevent SQL injection.

3. **View Security & Dynamic Variable Escaping**:
   - When rendering or generating views, **escape all dynamic variables using `\yii\helpers\Html::encode()`**.
   - Prevent Cross-Site Scripting (XSS) across all templates, emails, and HTML outputs.
   - For raw HTML injection where escaping is intentionally bypassed, ensure strict server-side sanitization.

4. **Credential & Secret Hygiene**:
   - Environment credential files committed to Git must be encrypted with `.enc` extensions (e.g., `environments/*/main-local.php.enc`).
   - **Never commit plain-text credentials, passwords, tokens, private keys, or API secrets to Git.**
   - Local configuration overrides (`*-local.php` without `.enc`) and service account keys must remain strictly gitignored.

5. **Code Style & PHP Standards**:
   - Follow PSR-12, PER-CS, and PHP 8.4 migration conventions configured in `.php-cs-fixer.php`.
   - Strict types where applicable (`declare(strict_types=1);`).
   - PHPStan Level 6 compliance with zero errors outside of baseline allowances.

---

## 3. Safety Constraints

To protect system integrity, workspace security, and source repositories:

1. **Explicit Confirmation for Terminal Commands**:
   - **Restrict terminal auto-execution without explicit confirmation.**
   - Always prompt the user and obtain clear confirmation before executing shell commands, particularly those modifying state, running Docker commands, altering branches, or invoking build scripts.
   - Never execute destructive or high-impact commands (e.g., `rm -rf`, `git reset --hard`, `git clean -f`, `git push --force`, database drop/truncate) without explicit user authorization and clear explanation of intent.

2. **Workspace Boundaries & Scoped File Access**:
   - **Limit all file access strictly to the current project directory**: `/Users/vsavakhande/Projects/learn/PRValidation`.
   - Do not inspect, read, modify, or create files outside this workspace root.
   - Respect git sub-repositories: avoid unintended commits, rebases, or branch resets in both the outer PR validation project and the nested `src/` application repository.
   - Do not attempt to decrypt, expose, or transmit encrypted `.enc` credentials or secrets.
