## Context

See `proposal.md` for motivation. The package is a Composer-distributed CLI that must synchronize only managed file-scope blocks in native PHP QA tool configuration files. The README defines the public behavior: `php-qa-scope.yml` is the source of truth, the `tools` map declares managed tools, supported targets are PHPCS, PHPStan, and PHP-CS-Fixer, and the command must preserve each tool's policy outside managed blocks.

The design therefore keeps native tool policy out of the package core. The implementation should inspect managed markers and scope declarations, not parse complete XML, NEON, or PHP configuration semantics.

## Goals / Non-Goals

**Goals:**

- Keep command orchestration thin and move behavior into testable domain services.
- Represent scope configuration and effective tool scope with explicit value objects.
- Render managed block content through tool-specific renderer strategies.
- Use one generic managed block locator for all native targets.
- Share per-target inspection and comparison between `check` and `sync` without retaining a project-wide file plan.
- Use PHPUnit for focused unit tests and end-to-end integration tests.
- Keep the package small and suitable for Composer distribution.

**Non-Goals:**

- Running PHP QA tools.
- Defining PHPStan levels, PHPCS standards, PHP-CS-Fixer rules, or other tool policy.
- Parsing or rewriting complete native configuration files.
- Creating missing native configuration files or managed markers.
- Managing PHPMD.
- Adding a plugin system or user-defined renderer API.

## Decisions

### CLI as a thin application layer with command handlers

Decision: `bin/php-qa-scope` should load Composer autoloading and delegate to `src/Application.php`. The application should parse raw CLI input into `src/Cli/Input.php`, resolve a command through `src/Command/CommandRegistry.php`, execute a `src/Command/Command.php` implementation, format user-visible output through `src/Cli/Output.php`, and return `src/Cli/ExitCode.php`.

The initial command handlers should be `src/Command/CheckCommand.php` and `src/Command/SyncCommand.php`. Future commands, such as an `init` command, should be added as new command handlers and separate use cases rather than expanding `Application.php` with command-specific branching.

Alternatives considered:

- Put command behavior directly in the executable. This is simpler at first but makes unit testing and future changes harder.
- Put `Application.php` under `src/Cli/`. This works while there are only CLI concerns, but the application object is better treated as the package entrypoint that wires CLI primitives to command handlers.
- Add Symfony Console now. Symfony Console would provide robust command definitions, help rendering, option parsing, and interactive features, but the initial command surface only needs simple command dispatch, deterministic output, and documented exit codes. A small internal command layer keeps the package lighter while leaving a future Symfony Console adapter possible if CLI complexity grows.

### Explicit configuration model

Decision: `src/Config/ScopeLoader.php` should parse YAML and validate shape, accepted tool keys, required arrays, and supported value types. It should return `src/Config/ScopeConfig.php`. `src/Config/EffectiveScope.php` should compute `src/Config/ToolScope.php` instances only for tools listed in the `tools` map.

Alternatives considered:

- Pass associative arrays through all layers. This reduces file count but hides invariants and spreads validation assumptions.
- Let each renderer merge global and tool-specific scope independently. This duplicates precedence rules and increases drift risk between tools.

### Renderer namespace and strategy interface

Decision: renderers belong under `src/Renderer/`, not `src/Tool/`, because their responsibility is rendering managed block text, not executing QA tools. `src/Renderer/Renderer.php` should define the common contract. Implementations should be `PhpCodeSnifferRenderer.php`, `PhpStanRenderer.php`, and `PhpCsFixerRenderer.php`.

Alternatives considered:

- Use `ToolRenderer` under a `Tool` namespace. This is less precise and suggests command execution behavior.
- Use one renderer class with branches per tool. This centralizes code but blurs target-specific formatting and escaping rules.

### Root-relative PHPCS selection and hidden-path discovery

Decision: the PHPCS renderer should emit `<file>.</file>` and an `extensions` argument for recursive `.php` discovery. Global `<exclude-pattern type="relative">` entries should limit selected files to effective includes, prune directories that cannot contain an included path, and apply configured excludes. The root entry gives every recursively discovered path the same project-relative basis. Directory exclude patterns should use PHPCS's trailing `/*` form so excluded subtrees are pruned. For example, `src/Foo/**` must exclude `src/Foo` without excluding `tests/Foo`.

During recursive discovery PHPCS skips dotfiles but can enter hidden directories, whereas PHPStan and PHP-CS-Fixer use Symfony Finder's default behavior to skip both. A PHPCS compatibility pattern should prune hidden directories unless they are an explicitly included directory or an ancestor needed to reach one. For an explicitly included `.php` file inside a hidden path, the renderer should add a direct `<file>` entry because PHPCS cannot discover that file from `<file>.</file>`. PHPCS evaluates relative exclusions against each direct file entry rather than the project root, so the renderer must omit a direct entry whenever a configured exclude matches that file. Root-relative exclusions still govern the copy encountered through recursive discovery. PHPStan should keep directory and file entries in `paths`; PHP-CS-Fixer should keep Finder's `ignoreDotFiles(true)` for directory traversal and append explicit files. A configured exclude always wins.

Alternatives considered:

- Emit one `<file>` entry per effective include. PHPCS evaluates relative exclusion patterns from each entry's base directory, so the same relative filename under `src` and `tests` becomes indistinguishable to a root-relative YAML exclude.
- Use absolute exclusion patterns. This would embed machine-specific project paths in synchronized XML and make the result non-portable.

The README should warn that native recursive discovery differs across tools and that `sync` may add hidden-directory and include-selection exclusions to PHPCS's managed block even when the YAML `exclude` lists are empty. Renderer and integration tests should cover ordinary files, dotfiles, hidden descendant directories, explicitly included hidden files and directories, root-relative subtree excludes, and exclude precedence.

### Generic managed block location

Decision: use `src/Sync/ManagedBlock.php` to locate and validate managed marker ranges in raw file text for every target. The target-specific marker syntax and file path belong in `src/Sync/TargetFile.php`.

Alternatives considered:

- Build a separate reader for each native configuration file. This would imply parsing XML, NEON, or PHP policy that the package intentionally does not own.
- Parse full native configuration formats. This would increase dependencies and could accidentally rewrite unrelated user policy.

### Shared per-target inspection for check and sync

Decision: load and validate `php-qa-scope.yml` and calculate managed tool scopes before visiting native targets. Then visit each managed target independently. A shared inspection service renders the expected managed block, reads the native file, validates its markers, and compares the current block with the expected content. The service returns the target's status and the data needed for that target alone. It must not retain prior targets' file contents. Marker validation completes before comparison reports a valid status or `sync` writes that target. Comparison may stop at the first difference after validation.

`check` uses inspection only to report `OK` or `OUT-OF-SYNC`; it does not construct a complete replacement file. `sync` constructs replacement content only for a divergent, valid target, writes it, reports `UPDATED`, and releases that target's file data before moving on. Matching targets report `OK` without replacement work. The shared service keeps comparison semantics identical across commands while allowing their memory and write needs to differ.

Alternatives considered:

- Implement unrelated inspection flows in both commands. This risks inconsistent marker validation and comparison.
- Let renderers write directly. This mixes formatting, comparison, and file operations.

### Independent target processing and command result

Decision: each command handles a target-local rendering, read, marker validation, or write failure inside its target loop. It reports `ERROR <target>: <reason>` and continues with later managed targets. A failure while loading or validating project scope configuration, including failure to determine effective scopes, is command-wide: the command reports the error and exits `2` before processing any target. After the loop, either command exits `2` if any target failed. Otherwise `check` exits `1` if any target is out of sync and `0` if all match; `sync` exits `0` if every target was already synchronized or successfully updated. Each visited target gets its own result even when the final exit code is `2`.

Alternatives considered:

- Abort the whole command at the first native-target error. This hides later target states and prevents independent valid updates.
- Treat scope configuration failures as target-local. This is unsound when the managed target set or effective scopes cannot be determined.

### Conservative per-target file update boundary

Decision: synchronization replaces only the located managed block content and preserves all outside bytes. A target must have exactly one valid start marker and one valid end marker with the required syntax, order, and indentation before that target can be updated. The writer prepares a temporary file, preserves the original file mode and line endings, checks for concurrent changes immediately before replacement, and cleans up temporary files on failure. It processes one target at a time. A failed target is left untouched; completed updates to other targets remain in place. A later invocation re-inspects every managed target, so previously updated targets report `OK` and are not rewritten.

Alternatives considered:

- Recreate complete configuration files. This would overwrite user policy and contradict the package scope.
- Create missing markers automatically. This could put managed blocks in the wrong location for a user's native tool configuration.

### PHPUnit test suite

Decision: add PHPUnit as the test framework and organize tests into unit and integration suites. Unit tests should cover configuration, effective scope, pattern compilation, renderers, managed block validation, and planning. Integration tests should cover CLI behavior, exit codes, status reporting, and file preservation.

Alternatives considered:

- Keep a custom PHP test runner. This limits assertions, tooling integration, and contributor familiarity.
- Use a behavior framework. This adds an additional abstraction that is not needed for a small Composer package.

## Risks / Trade-offs

- Renderer output can become overly coupled to tool-specific formatting quirks -> Mitigate with dedicated renderer tests and integration fixtures for each supported target.
- PHPCS has no global include pattern and evaluates relative exclusions from each `<file>` base -> Use one project-root entry for recursive discovery, add direct entries only for explicitly included files that recursion cannot find, and verify configured excludes against both paths.
- Hidden-path defaults differ between native tools -> Prune hidden directories during PHPCS recursion while preserving explicitly included hidden paths, and test those cases separately.
- The portable exclude pattern language is intentionally smaller than full glob syntax -> Mitigate with explicit validation errors and tests for every supported and rejected form.
- Preserving bytes outside managed blocks limits the package's ability to repair malformed native files -> Mitigate by returning exit code `2` for invalid targets and documenting that markers must be added by the user.
- Independent target updates can leave a run with both successful updates and errors -> Report every target result and return `2` if any target fails; document retry behavior.
- Holding an inspected file longer than its target loop defeats the intended memory bound -> Use target-scoped data and measure peak memory with inflated fixtures.
- A file may change between inspection and replacement -> Compare its current contents with the inspected input immediately before the rename and report a target-local error if they differ.

## Migration Plan

1. Add PHPUnit configuration and Composer test wiring.
2. Add the source architecture under `src/` and wire the executable to the CLI application.
3. Implement behavior in small vertical slices: configuration loading, scope calculation, pattern compilation, rendering, per-target inspection, writing, and reporting.
4. Add unit tests alongside each source area.
5. Add integration tests for CLI behavior, mixed target results, retries, and managed file preservation.
6. Reconcile README command behavior, exit code documentation, and the hidden-path compatibility warning with the per-target contract.
7. Measure peak memory with inflated target fixtures and record fixture sizes and measurements.
8. Run OpenSpec validation and package QA commands before considering implementation complete.

## Open Questions

None.
