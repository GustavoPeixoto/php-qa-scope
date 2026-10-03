## Why

All 19 unit test files currently sit directly under `tests/Unit/`, while production code is already grouped by responsibility. Organizing the existing tests into corresponding directories will make related coverage easier to find as the package grows.

## What Changes

- Move 18 existing unit test files into `Block/`, `Cli/`, `Command/`, `Composition/`, `Console/`, `Glob/`, `InsertionLocator/`, `Renderer/`, `Scope/`, and `Target/` under `tests/Unit/`.
- Keep `ToolTest.php` directly under `tests/Unit/`, matching the root-level `src/Tool.php` declaration.
- Group `CompositionTest.php` and `NativeRegistryTest.php` in `Composition/` because their existing coverage spans multiple collaborators.
- Update moved test namespaces to match their new PSR-4 paths and adjust the executable paths in `CliTest.php` and `ConsoleTest.php` for the extra directory level.
- Preserve existing file basenames, class names, test methods, assertions, fixtures, and suite membership.

Splitting test classes, adding or removing scenarios, reclassifying tests as integration tests, changing production behavior, introducing new helpers, and changing QA policy are outside this change. Existing broad test responsibilities remain intact.

## Capabilities

### New Capabilities

None. This is a test-layout refactor with no new package behavior.

### Modified Capabilities

None. The existing `library-composition`, `managed-scope-sync`, and `scope-initialization` requirements remain unchanged. The change declares `skip_specs: true` in `.openspec.yaml`; no delta specs are required or generated.

## Impact

- Affected files are the existing tests under `tests/Unit/`; the complete destination mapping is in `design.md`.
- Composer already maps `GustavoPeixoto\PhpQaScope\Tests\` to `tests/`, and PHPUnit already discovers the `tests/Unit` directory recursively. Those configurations need no change.
- PHPCS, PHPStan, and PHP-CS-Fixer already include the whole `tests` tree. Scope configuration and managed native blocks need no change.
- `tests/TestCase.php`, `tests/Integration/`, production code, package interfaces, and dependencies remain unchanged.
- The main risks are mismatched namespaces, broken executable paths, or unnoticed loss of test discovery. Implementation validation will compare the Unit inventory before and after, run the existing test suites and QA checks, and inspect the diff for unintended changes.
- Consulted durable sources: `AGENTS.md`, `conventions/language.md`, `conventions/repository.md`, `conventions/workflow.md`, `conventions/git.md`, `conventions/artifacts.md`, `conventions/environment.md`, `openspec/config.yaml`, the existing capability specs, the current source and tests, `composer.json`, `phpunit.xml.dist`, and native QA configuration files.

## Open Questions

None. No relevant pending items remain; scope is limited to relocating the existing files and making the namespace and path adjustments needed to preserve their behavior.
