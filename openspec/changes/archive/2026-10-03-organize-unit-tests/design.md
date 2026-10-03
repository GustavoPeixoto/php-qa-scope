## Context

See `proposal.md` for motivation and scope. The current Unit suite contains 19 files with the namespace `GustavoPeixoto\PhpQaScope\Tests\Unit`. Production code already uses responsibility-based directories, with `Tool.php` and `Application.php` at the source root.

The development PSR-4 mapping in `composer.json` covers the entire `tests/` tree. The Unit suite in `phpunit.xml.dist` uses directory discovery; all configured native QA tools also cover the whole test tree. The shared base class is `tests/TestCase.php`.

Several test files already exercise more than one production component. Their content and Unit classification are retained; directory placement follows their primary responsibility. This structural decision and the exceptions below warrant a design artifact even though no behavioral specs change.

## Goals / Non-Goals

**Goals:**

- Make placement predictable from the production module or the test's composition responsibility.
- Keep the relocation mechanically reviewable and preserve test discovery and execution.

**Non-Goals:**

- See the exclusions in `proposal.md`; this design introduces no further changes to class boundaries, fixtures, helpers, or QA configuration.
- Do not create empty Unit directories for production modules without an existing test file to move.

## Decisions

### 1. Mirror source modules with one explicit composition group

Use the following mapping. Every original file currently resides directly under `tests/Unit/`; every destination below is relative to that directory.

| Existing file | Destination |
| --- | --- |
| `BlockLocatorTest.php` | `Block/BlockLocatorTest.php` |
| `CliTest.php` | `Cli/CliTest.php` |
| `CommandRegistryTest.php` | `Command/CommandRegistryTest.php` |
| `CompositionTest.php` | `Composition/CompositionTest.php` |
| `NativeRegistryTest.php` | `Composition/NativeRegistryTest.php` |
| `ConsoleTest.php` | `Console/ConsoleTest.php` |
| `PatternCompilerTest.php` | `Glob/PatternCompilerTest.php` |
| `PhpCodeSnifferInsertionLocatorTest.php` | `InsertionLocator/PhpCodeSnifferInsertionLocatorTest.php` |
| `PhpCsFixerInsertionLocatorTest.php` | `InsertionLocator/PhpCsFixerInsertionLocatorTest.php` |
| `PhpStanInsertionLocatorTest.php` | `InsertionLocator/PhpStanInsertionLocatorTest.php` |
| `RendererTest.php` | `Renderer/RendererTest.php` |
| `ScopeConfigTest.php` | `Scope/ScopeConfigTest.php` |
| `ScopeInitializerTest.php` | `Scope/ScopeInitializerTest.php` |
| `ScopeLoaderTest.php` | `Scope/ScopeLoaderTest.php` |
| `TargetInitializerTest.php` | `Target/TargetInitializerTest.php` |
| `TargetInspectorTest.php` | `Target/TargetInspectorTest.php` |
| `TargetRegistryTest.php` | `Target/TargetRegistryTest.php` |
| `TargetWriterTest.php` | `Target/TargetWriterTest.php` |
| `ToolTest.php` | `ToolTest.php` (unchanged) |

`Composition/` holds application graph and multi-registry coverage. It is a test organization group rather than a new production module. `RendererTest.php` stays whole under `Renderer/`, and the existing executable-related scenarios in `CliTest.php` and `ConsoleTest.php` retain their current files and suite.

Alternatives considered: grouping by native QA tool would scatter scope, target, and locator coverage across a second taxonomy; placing every file in a new subdirectory would add an artificial home for the root-level `Tool` type; splitting broad tests would exceed the confirmed relocation-only scope.

### 2. Update only path-dependent PHP declarations and executable lookup

For each moved file, append the destination directory name to `GustavoPeixoto\PhpQaScope\Tests\Unit`. For example, `Block/BlockLocatorTest.php` declares `GustavoPeixoto\PhpQaScope\Tests\Unit\Block`. Preserve file basenames, class names, imports that still resolve correctly, methods, assertions, and fixture content. Check for any test-type references that require an updated qualified namespace; no compatibility aliases are needed for internal test classes.

Both existing executable lookups ascend two levels from the current Unit directory:

- `CliTest.php` uses `dirname(__DIR__, 2) . '/bin/php-qa-scope'` when running `init`.
- `ConsoleTest.php` uses the same path when reading the executable for the missing-autoload scenario.

After these files move one level deeper, change those expressions to `dirname(__DIR__, 3) . '/bin/php-qa-scope'`. Other `__DIR__` occurrences in rendering expectations and fixture PHP strings describe generated configuration or fixture behavior and must remain unchanged.

Alternative: add a repository-root helper to `tests/TestCase.php`. Directly adjusting the two expressions avoids changing shared infrastructure for a simple relocation.

### 3. Retain existing discovery and QA configuration

Keep `composer.json`, `phpunit.xml.dist`, `php-qa-scope.yml`, native QA files, `tests/TestCase.php`, and `tests/Integration/` as they are. Their existing paths cover the new directories. A local autoload refresh is allowed if an installed optimized classmap needs rebuilding; it does not require a package metadata change.

Capture the discovered Unit class/method inventory before moving files and compare it afterward, normalizing the intended namespace changes. The current files contain 72 `test*` methods across 19 classes; PHPUnit's discovered inventory is authoritative for execution and any data-provider expansion. Run the complete existing suite to catch both relocated tests and accidental shared-fixture regressions, followed by existing PHPCS, PHPStan, and PHP-CS-Fixer checks.

Use the package's PHP environment and contributor QA commands from `conventions/environment.md`. The existing Fixer configuration requires `composer fixer-check -- --allow-risky=yes` for its `declare_strict_types` rule; this change does not alter that policy. Do not add new tests for a relocation whose acceptance is preservation of the existing inventory and behavior.

### 4. Declare the absence of behavior changes explicitly

Set `skip_specs: true` in the scaffolded change metadata. No capability delta is necessary: production behavior, composition contracts, CLI behavior, and scope synchronization remain unchanged. Existing specs are retained rather than adding a test-layout capability solely to satisfy validation.

## Risks / Trade-offs

- [Namespace differs from the new path] -> Match every namespace to the destination table and verify PHPUnit discovery and static analysis.
- [Executable lookup points outside the repository] -> Update only the two real repository-path expressions and run their existing scenarios.
- [Test coverage disappears or fixture strings change during the move] -> Compare the pre/post Unit inventory and review rename-aware diffs, preserving all fixture strings and assertions.
- [Composition grouping differs from `src/`] -> Keep the exception explicit in this mapping; it reflects the existing cross-module coverage without changing test responsibilities.
- [Broader responsibilities remain in a few Unit classes] -> Retain them deliberately; a future class-splitting change can assess them separately.

## Migration Plan

1. Capture the current discovered Unit inventory and establish the existing test baseline in the PHP environment.
2. Move the 18 files using the table, update namespaces, and correct the two executable lookups.
3. Compare discovery, run the existing suites and QA checks, and review the diff for unintended edits.

No consumer migration or deployment is needed. If rollback is required, reverse the 18 moves and restore the original namespace declarations and two-level executable lookups while preserving unrelated work.
