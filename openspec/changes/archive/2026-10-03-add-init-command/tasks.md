# Tasks

## 1. Shared synchronization and native replacement

- [x] 1.1 Read `AGENTS.md`, the applicable language, repository, workflow, PHPDoc, environment, artifact, and Git conventions, and this change's proposal, design, and specs before editing package files; verify the working diff and identify any user changes to preserve.
- [x] 1.2 Extract the target loop behind `SyncCommand` into a shared synchronization collaborator with structured failure and successful-change information; verify existing `CommandIntegrationTest` status, drift, continuation, and no-op tests still pass without output changes.
- [x] 1.3 Extract reusable safe native replacement mechanics from `SyncWriter` for both marker insertion and managed-block replacement; add or retain tests proving CRLF and permissions preservation, symlink rejection, concurrent-change protection, temporary-file cleanup, and no rewriting of unchanged targets.
- [x] 1.4 Inject `Synchronizer` into `SyncCommand` and share one instance with `InitCommand` in `Application::default()`; verify existing synchronization and initialization regressions.
- [x] 1.5 Move the four `Target*` classes to `src/Target/`, update namespaces and imports in package code and existing tests, and verify the behavior remains unchanged; preserve the YAML `tools` key and class names.

- [x] 1.6 Remove the redundant `SyncWriter` adapter and inject `TargetWriter` directly into `Synchronizer`; update application wiring and existing tests while preserving drift checks, replacement generation, and native write safeguards.

## 2. Root discovery and scope YAML creation

- [x] 2.1 Expose discovery through the existing native target mappings and detect only the three exact root filenames; add focused tests for all tool combinations, alternate names, subdirectory-only configurations, and no recognized root file.
- [x] 2.2 Implement create-only default YAML generation with global `include: [src]`, empty global excludes, and empty local arrays for detected tools; verify empty scope arrays are serialized as `[]`, the output loads through `ScopeLoader`, does not require `src` to exist, and never overwrites YAML created concurrently.
- [x] 2.3 Preserve and validate existing YAML and calculate only its listed tools' effective scopes; test custom scopes, an empty tools map, unlisted discovered tools, invalid or unreadable YAML, YAML symlinks, and creation failures stopping before native writes.
- [x] 2.4 Document the generated defaults and existing-YAML preservation in the README's scope guidance; verify examples use supported keys and make root-only exact-filename discovery clear.

- [x] 2.5 Remove the former `Init\ScopeInitializer` setup coordinator, move destination validation and default YAML generation into private `ScopeInitializer` helpers, and let `InitCommand` coordinate discovery, create-if-absent, schema loading, and effective-scope calculation; retain existing-YAML preservation, symlink rejection, mandatory native discovery, and create-only safeguards in tests.

- [x] 2.6 Discover native tools once in `InitCommand` and pass the discovered tool map to `ScopeInitializer::create()` and its private `contents()` helper; remove the creator's `TargetRegistry` dependency and verify supplied-tool generation and no-native-file failures.

- [x] 2.7 Centralize YAML destination validation in `ScopeInitializer`, return early for an existing YAML, and call `create()` unconditionally after discovery in `InitCommand`; verify YAML preservation, symlink rejection after successful discovery, missing-native-configuration error precedence, and creation safeguards.

## 3. Empty marker preparation

- [x] 3.1 Implement absent-pair classification and validation using the strict existing `ManagedBlock` locator; test both markers absent, a valid existing pair, incomplete or duplicate markers, reversed markers, incorrect syntax or indentation, and no rewriting during preparation of existing valid blocks.
- [x] 3.2 Implement PHPCS insertion after the first actual non-self-closing `ruleset` opening tag without XML reserialization; test attributes, quoted tag delimiters, tag-like comments, same-line contents, byte preservation, and unsupported insertion locations.
- [x] 3.3 Implement PHPStan insertion under an unambiguous top-level block-form `parameters:` declaration; test trailing comments, LF and CRLF, existing parameters preserved, and absent, inline, nested, or ambiguous layouts returning manual-placement errors.
- [x] 3.4 Implement conventional PHP-CS-Fixer insertion using PHP tokenization without executing the configuration; test ordinary PHP, leading comments, strict-types declarations, correct placement before executable code, unchanged existing Finder code, and unsupported namespace or mixed-content layouts.
- [x] 3.5 Extend `README.md` under the existing `Managed Blocks` heading with correctly indented placement examples and fallback instructions for unsupported layouts; verify the heading still produces the warning's `#managed-blocks` anchor.

- [x] 3.6 Move the insertion locator interface and implementations to `src/InsertionLocator/`, rename the PHPCS implementation to `PhpCodeSnifferInsertionLocator`, and update namespaces, imports, and existing tests.

- [x] 3.7 Rename `MarkerPreparer` to `TargetInitializer` with an `insert()` method, inject `InsertionLocatorRegistry` following the renderer registry pattern, and update application composition and existing marker tests.

## 4. Initialization command, automatic sync, and consumer guidance

- [x] 4.1 Add and register `InitCommand`, update both usage-message sources, and preserve no-extra-argument validation; verify CLI dispatch, unknown-command handling, extra arguments, and documented `vendor/bin/php-qa-scope init` invocation.
- [x] 4.2 Compose root discovery, YAML setup, all-target marker preparation, and one call to the shared sync workflow for successfully prepared targets; add integration tests that observe persisted empty blocks before sync, populated blocks at command completion, and renderer-equivalent content without a second consumer command.
- [x] 4.3 Aggregate preparation and synchronization failures while continuing with later eligible targets and retaining completed writes; test an unsupported first target followed by successful initialization, a missing listed target, sync failure after marker insertion, partial success, retry after repair, and exit codes limited to `0` or `2` for `init`.
- [x] 4.4 Track successful native changes from both phases and emit the exact three-line review warning once at the end on standard error; test normal output separation, the repository URL, warnings after partial failure, and warning suppression for no-op retries or YAML-only creation.
- [x] 4.5 Complete README initialization and review guidance alongside command delivery: explain automatic `sync`, repeats, partial failures, manual marker fallback, conflicting PHPCS scope settings, duplicated PHPStan keys, Finder overrides, and `setFinder($finder)` integration; verify the linked section is sufficient for a package consumer and does not claim native QA readiness.

## 5. Whole-change verification

- [x] 5.1 Run end-to-end temporary-project checks for `init` followed by `check` on clean conventional configurations, repeated `init`, and isolated managed tool subsets; verify YAML and native snapshots, preserved outside bytes, warning behavior, and unchanged `sync`/`check` missing-marker semantics.
- [x] 5.2 Run the full package tests and relevant QA checks in the prescribed PHP environment: `composer test`, `composer sniffer-check`, `composer fixer-check -- --allow-risky=yes`, and `composer stan-check`; resolve change-related failures and record any unrelated limitation.
- [x] 5.3 Validate `add-init-command` with `openspec validate add-init-command --strict`; review the implementation diff against every requirement, verify all warning URLs and capability paths, and confirm planning artifacts are self-sufficient without temporary or conversation-only inputs before marking implementation ready.

## 6. Initialization workflow extraction

- [x] 6.1 Extract the complete initialization workflow into `Initializer/Initializer` and introduce `InitializerResult` for aggregated target errors and native writes; preserve discovery ordering, all marker insertions before synchronization, local error continuation, and command-wide exception propagation.
- [x] 6.2 Inject `Initializer` into `InitCommand`, retain the warning and exit-code mapping in the command, and update application and integration-test composition while sharing the existing synchronizer.
- [x] 6.3 Verify initializer result aggregation directly for successful writes, unchanged retries, and marker-only changes with synchronization failures; run the existing integration regressions, package QA, and OpenSpec validation.

## 7. Responsibility-based namespace organization

- [x] 7.1 Move `Config` classes to `Scope`, place `ScopeInitializer` there, and organize the initializer, synchronizer, block, and target collaborators and result types under the approved names; preserve existing methods and behavior.
- [x] 7.2 Update source namespaces and imports, application composition, PHPDoc, test class/file names and references, and final OpenSpec architecture descriptions; verify no obsolete package references remain.
- [x] 7.3 Run existing package tests, PHPCS, PHP-CS-Fixer, PHPStan, OpenSpec validation, and whitespace checks to verify behavior and write safeguards remain unchanged.
