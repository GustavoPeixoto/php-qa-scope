## Why

Projects need a reliable way to keep native PHP QA file scopes aligned with one `php-qa-scope.yml` file. The CLI must inspect each managed target independently so a problem in one native file does not hide the state of other files or prevent their valid updates.

## What Changes

- Implement the `php-qa-scope` CLI with `check` and `sync` commands.
- Parse and validate `php-qa-scope.yml` from the project root.
- Treat the `tools` map as the explicit declaration of managed tools.
- Compute an effective scope for each managed tool from global and tool-specific include and exclude lists.
- Render managed blocks for PHPStan, PHP_CodeSniffer, and PHP-CS-Fixer.
- Align recursive discovery of hidden paths across the managed tools while honoring explicitly included paths.
- Locate and validate managed blocks in native configuration files without parsing unrelated tool policy.
- Inspect and compare one managed target at a time, retaining native file contents only while processing that target.
- Make `check` report `OK` or `OUT-OF-SYNC` without constructing a replacement file.
- Make `sync` update divergent targets individually and continue after target-local errors.
- Report `OK`, `OUT-OF-SYNC`, `UPDATED`, or `ERROR <target>: <reason>` as appropriate, then aggregate the command exit code.
- Preserve all bytes outside managed blocks when synchronizing.
- Document the tools' hidden-path defaults and any compatibility exclusions added by synchronization.
- Add PHPUnit-based unit and integration coverage for configuration loading, pattern handling, renderers, target inspection, writing, CLI behavior, error continuation, and exit codes.

## Capabilities

### New Capabilities

- `managed-scope-sync`: Defines how `php-qa-scope` loads scope configuration, determines managed tools, renders native configuration blocks, checks and synchronizes each target, reports statuses, and handles target-local and command-wide errors.

### Modified Capabilities

- None.

## Impact

- Affected package entrypoints: `bin/php-qa-scope`, Composer `bin` wiring, and Composer scripts for test execution.
- Affected source areas: CLI orchestration, configuration loading, effective scope calculation, exclude pattern compilation, renderer strategy implementations, per-target inspection and comparison, and sync writing.
- Affected supported tools: PHPStan via `phpstan.neon`, PHP_CodeSniffer via `phpcs.xml`, and PHP-CS-Fixer via `php-cs-fixer.dist.php`.
- Native scope behavior: PHPCS scans from a single `<file>.</file>` root and uses root-relative selection and exclusion patterns, including a compatibility exclusion for hidden directories found during recursion. Explicitly included hidden PHP files receive direct file entries because PHPCS does not discover dotfiles recursively. PHPStan and PHP-CS-Fixer retain their default hidden-path discovery behavior. Configured excludes retain precedence across all tools.
- Affected documentation: the README explains why managed blocks may contain a hidden-path compatibility rule absent from `php-qa-scope.yml`.
- Affected development dependencies: add PHPUnit as the package test framework.
- Runtime behavior: a target-local failure does not prevent later targets from being inspected or updated; a `sync` run may update some targets and exit `2` because another target failed. Invalid project scope configuration stops the command before target processing.
- Resource use: target file contents are released before the next target is read; peak retained native-file data scales with the largest processed target rather than the combined size of all targets.
- Out of scope: running QA tools, defining PHPStan levels, defining PHPCS standards, defining PHP-CS-Fixer rules, managing PHPMD, generating full native configuration files, or adding a plugin system.
- Consulted durable context sources: `README.md`, `AGENTS.md`, `openspec/config.yaml`, and repository conventions under `conventions/`.

## Open Questions

- None. The managed tool set, scope file semantics, hidden-path discovery behavior, managed block contract, supported exclude pattern forms, target-local continuation, and exit code meanings are defined for this implementation.
