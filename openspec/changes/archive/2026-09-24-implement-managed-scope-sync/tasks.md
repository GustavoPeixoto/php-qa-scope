## 1. Context And Test Setup

- [x] 1.1 Read `README.md`, `AGENTS.md`, `conventions/workflow.md`, `conventions/environment.md`, and this change's planning artifacts; verify the package entrypoints and project rules are understood.
- [x] 1.2 Add PHPUnit as a development dependency and add package test wiring; verify `composer test` invokes PHPUnit.
- [x] 1.3 Add PHPUnit configuration and test directory structure for unit and integration tests; verify PHPUnit discovers the intended test suites.

## 2. Configuration And Scope Model

- [x] 2.1 Implement scope configuration value objects and YAML loading; verify unit tests cover valid configuration, unknown tool keys, missing required arrays, and invalid value types.
- [x] 2.2 Implement managed tool selection from the `tools` map; verify tests show listed tools are managed and omitted tools are skipped without target access.
- [x] 2.3 Implement effective scope calculation; verify tests cover global includes, tool-specific includes, global excludes, tool-specific excludes, and exclude precedence.

## 3. Pattern Handling

- [x] 3.1 Implement supported exclude pattern validation and compilation; verify unit tests cover specific files, specific subtrees, recurring directories, recurring directories under a root, and file suffix patterns.
- [x] 3.2 Reject unsupported pattern syntax; verify unit tests cover unsupported single-segment wildcards, character classes, brace alternatives, negation, and regular expressions.

## 4. Renderers

- [x] 4.1 Add the renderer interface and PHP_CodeSniffer renderer under `src/Renderer/`; use `<file>.</file>` with root-relative include and exclude filters, retain the recursive `.php` extension setting, prune hidden directories unless explicitly included, and add direct entries for explicitly included hidden PHP files only when configured excludes do not match them.
- [x] 4.2 Add the PHPStan renderer under `src/Renderer/`; verify unit tests assert PHPStan-compatible NEON output for paths and exclude paths.
- [x] 4.3 Add the PHP-CS-Fixer renderer under `src/Renderer/`; verify unit tests assert Finder-compatible PHP output for directories, files, and excludes.
- [x] 4.4 Register renderers by supported tool key; verify tests assert each managed tool maps to the expected target file and marker syntax.
- [x] 4.5 Verify the three renderers' effective file selection with fixture files covering ordinary `.php` files, recursively discovered dotfiles and hidden directories, explicitly included hidden files and directories, configured excludes overriding those includes, and `src/Foo/**` excluding `src/Foo` without excluding `tests/Foo`.

## 5. Per-Target Inspection

- [x] 5.1 Implement target file mapping and managed block location; verify unit tests cover valid blocks, missing or duplicated markers, reversed or malformed blocks, and line ending detection.
- [x] 5.2 Implement shared per-target inspection and comparison after command-wide scope loading; verify unit tests cover valid matching and divergent targets, complete marker validation, and target-local read or rendering failures.
- [x] 5.3 Make inspection expose status without constructing a whole-file replacement for `check`; verify focused tests show drift detection and no replacement allocation for matching or checked targets.
- [x] 5.4 Keep each target's native file data scoped to its processing step; verify inflated fixture measurements show peak retained native-file data follows the largest target rather than the sum of target sizes, and record fixture sizes and measurements.

Memory verification used one or three native targets of 8,388,651 to 8,388,671 bytes each, with 8 MiB of content outside the managed block. In separate PHP 8.5 processes, `check` peaked at 12,595,200 bytes for both one and three targets. A whole-project before/after retention simulation peaked at 20,979,712 bytes for one target and 54,550,528 bytes for three. These measurements are fixture-specific evidence of the expected scaling, not a fixed memory limit.

## 6. Sync Writing And CLI

- [x] 6.1 Implement `src/Application.php`, `src/Cli/Input.php`, `src/Cli/Output.php`, and `src/Cli/ExitCode.php`; verify unit tests cover input parsing, output buffering, and documented exit code values.
- [x] 6.2 Implement command registration and dispatch; verify unit tests cover known commands and invalid-command exit code `2`.
- [x] 6.3 Adapt sync writing to update one divergent target at a time; verify tests cover byte-for-byte preservation outside its managed block, line endings, file mode, symlink rejection, concurrent-change detection, and temporary-file cleanup.
- [x] 6.4 Make `check` inspect and report every managed target, continuing after target-local errors; verify integration tests cover `OK`, `OUT-OF-SYNC`, `ERROR <target>: <reason>`, and exit-code precedence `2` over `1` over `0`.
- [x] 6.5 Make `sync` inspect, update, and report each managed target independently; verify integration tests cover failures before and after a successful update, mixed `ERROR`/`UPDATED`/`OK` output, and exit code `2` after partial success.
- [x] 6.6 Preserve command-wide failure for invalid project scope configuration; verify neither command inspects or writes native targets when loading or effective-scope calculation fails.
- [x] 6.7 Verify a retry re-inspects every target and does not rewrite targets already updated or synchronized; assert only still-divergent targets change.

## 7. Package Integration And Verification

- [x] 7.1 Wire `bin/php-qa-scope` to the CLI application and Composer `bin`; verify `vendor/bin/php-qa-scope check` can run in a fixture project.
- [x] 7.2 Ensure package autoloading covers `src/` and test autoloading covers PHPUnit tests; verify `composer dump-autoload` succeeds.
- [x] 7.3 Update `README.md` to document per-target `check` and `sync`, local error continuation, partial successful sync, per-target status lines, retries, aggregate exit codes, and a warning about native hidden-path discovery and generated PHPCS selection and compatibility exclusions; verify it agrees with the specification.
- [x] 7.4 Run the full PHPUnit suite; verify all unit and integration tests pass for the per-target and hidden-path behavior.
- [x] 7.5 Run package QA commands available in the repository; verify PHPCS, PHPStan, and PHP-CS-Fixer checks pass or record any documented environment limitation.
- [x] 7.6 Validate this OpenSpec change; verify `openspec validate "implement-managed-scope-sync" --type change --strict` succeeds.
- [x] 7.7 Audit planning artifacts for self-sufficiency; verify `proposal.md`, `design.md`, `specs/managed-scope-sync/spec.md`, and `tasks.md` contain the complete contract without relying on temporary or unversioned inputs.
