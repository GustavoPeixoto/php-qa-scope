# Design

## Context

See `proposal.md` for the consumer problem and change scope. The default application currently registers `CheckCommand` and `SyncCommand`. Input and registry errors hard-code `Usage: php-qa-scope <sync|check>`. `TargetRegistry` already owns the exact three tool-to-filename mappings, marker syntax, and required indentation.

`ScopeLoader` validates YAML and `EffectiveScope` calculates the listed tools' scopes without requiring included directories to exist. `TargetInspector` loads these scopes, renders expected blocks, and rejects native symlinks and invalid markers. `ManagedBlock::locate()` requires exactly one correctly positioned pair; it must remain strict. `SyncWriter` accepts an existing located block and replaces it with temporary-file, permission, line-ending, and concurrent-change safeguards. It cannot directly create a pair in a marker-free file.

The existing renderers can fill all three inserted blocks. In particular, `PhpCsFixerRenderer` produces a `$finder` assignment and does not wire it with `setFinder()`. Runtime dependencies are PHP and Symfony YAML; no XML, NEON, or PHP AST parser is declared as a package dependency.

## Goals / Non-Goals

The design separates marker placement from scope rendering and reuses synchronization so generated content stays identical to a normal `sync`. It preserves strict validation and per-target failure isolation while providing enough change information to print the final warning accurately.

The insertion routines recognize bounded conventional layouts. They do not evaluate arbitrary configuration programs or promise full native-format semantic validation. Existing scope settings outside the new block are intentionally left for consumer review, as specified in `specs/scope-initialization/spec.md`.

## Decisions

### 1. Use a two-phase initialization coordinator

Add an `InitCommand` registered by `Application::default()` and update usage text in input parsing and registry errors. Inject collaborators for default YAML creation, native marker preparation, and synchronization. Preserve the CLI's current no-extra-arguments behavior.

Execution order is:

```text
discover exact native root files
  --> create absent YAML or preserve and load existing YAML
  --> calculate effective scopes for listed tools
  --> prepare empty marker pairs for all listed targets
  --> invoke shared sync workflow once for prepared targets
  --> print final review warning when any native file changed
  --> return 0, or 2 when any phase failed
```

Configuration-level failures stop before preparation. Target-level failures are collected and processing continues. Successfully prepared targets include targets whose valid markers were already present. A target that failed preparation is reported once and is excluded from that invocation's synchronization phase; the error remains part of the final aggregate result. There is no transaction or rollback across files or between preparation and synchronization.

This follows the requested flow exactly: the initializer creates and persists empty pairs, then calls synchronization to fill them. It does not render content during preparation. A separate consumer `sync` command is not necessary to fill the initial blocks.

Alternative considered: fill blocks directly during insertion. Rejected because it merges two responsibilities and duplicates synchronization orchestration. Launching the CLI as a child process is also unnecessary and would complicate aggregation and error reporting.

### 2. Reuse a small shared synchronization coordinator

Group `TargetFile`, `TargetRegistry`, `TargetInspector`, and `TargetInspection` in `src/Target/` under the `GustavoPeixoto\PhpQaScope\Target` namespace. Native target definitions and inspection are shared across initialization, synchronization, and checking. Keep synchronization coordination in `src/Synchronizer/`, native file operations in `src/Target/`, and managed-block handling in `src/Block/`, with explicit imports between the namespaces. Preserve the class names and the public YAML `tools` key.

Inject `Synchronizer` into `SyncCommand` and `Initializer`. `Application::default()` creates one instance with the shared inspector and writer and passes it to both workflows; `InitCommand` receives the composed `Initializer`.

Extract the existing `SyncCommand` target loop into a narrowly scoped collaborator, provisionally `Synchronizer`. It accepts already calculated tool scopes and uses the existing inspector and writer. Both `SyncCommand` and `Initializer` call that same workflow. Normal `sync` still loads its own scopes, visits every listed target, emits the same `OK`, `UPDATED`, and `ERROR` messages, and returns the same codes.

Return structured synchronization results containing whether any native file was successfully changed and whether any target failed. Initialization combines these with preparation results. Avoid inferring successful changes by parsing buffered output or treating an attempted write as a successful update. Leave `CheckCommand` and renderer behavior unchanged.

Alternative considered: directly call the current `SyncCommand::execute()` and inspect its output for `UPDATED`. Its integer result cannot distinguish a no-op from actual changes, and output parsing would couple warning behavior to presentation. The small extraction supplies that information explicitly while still invoking the existing synchronization workflow.

### 3. Generate YAML only when absent

Keep default generation and create-only persistence in `ScopeInitializer`. Its `create($root, $tools)` method calls private `validate($root)` and `contents($tools)` helpers. Validation rejects real and dangling symlinks, returns false when the YAML already exists, and checks creation preconditions only for absent destinations; `create()` returns early for an existing YAML without changing its bytes or inode. The creator receives the discovered `array<string, TargetFile>` from the command instead of depending on `TargetRegistry` or repeating discovery; `contents()` uses the tool keys to build the default scope entries. The atomic create-only link remains the safeguard against a destination appearing concurrently. Remove the former `Init\ScopeInitializer` setup coordinator; `Initializer` performs native discovery once, invokes `create()` unconditionally, loads the YAML through `ScopeLoader`, and calculates scopes through `EffectiveScope`. Discovery remains mandatory even when the YAML already exists. Missing native configuration errors take precedence over YAML symlink errors; when discovery succeeds, the creator rejects YAML symlinks before loading or modifying files.

Reuse `TargetRegistry` mappings for root discovery instead of maintaining a second set of filenames. Expose the registered target list if necessary. Detect only the agreed filenames; neither Composer dependencies nor alternate native filenames participate in detection.

For a new YAML, serialize a deterministic mapping with global `include: [src]`, empty global excludes, and detected tools with empty local arrays. Use the existing Symfony YAML dependency and normal file permissions. A conventional tool order matching the registry makes the output stable.

For existing YAML, first reject symlinks, then load it with `ScopeLoader`. Preserve its bytes and use only its listed tools. Detected but unlisted native files remain unmanaged. Missing listed targets are local preparation errors. An empty `tools` map remains valid under the current schema and results in no managed targets, provided discovery found a supported root file.

Use create-only file semantics that cannot replace a YAML appearing concurrently. A failed creation must clean up only artifacts owned by that creation attempt. Do not repurpose the native replacement writer to overwrite an existing YAML. Serialize and validate the intended configuration before committing it; creation failures stop before native writes.

### 4. Keep marker classification strict

For each target, read its bytes and reject symlinks. Count occurrences of both marker edges before insertion. If neither is present, find an insertion position and build only the empty pair. If either is present, delegate validation to `ManagedBlock::locate()`; never repair a partial pair or append another pair.

Validate a generated pair using the same locator before committing the preparation write. The fixed indentation is four spaces for PHPCS and PHPStan and zero for PHP-CS-Fixer. The unchanged strict locator protects ordinary `sync` and `check` as well as the synchronization phase of `init`.

### 5. Recognize bounded insertion anchors without rewriting the document

Keep the `InsertionLocator` interface and its implementations in `src/InsertionLocator/`, following the organization of `src/Renderer/`. Use `PhpCodeSnifferInsertionLocator`, `PhpStanInsertionLocator`, and `PhpCsFixerInsertionLocator` for the three native formats. Resolve strategies through an injected `InsertionLocatorRegistry`, with a constructor accepting the strategy map, `get($tool)`, and `default()` providing the built-in implementations. `TargetInitializer` belongs in `src/Target/`; its `insert()` method validates existing pairs or persists an absent empty pair through `TargetWriter`. `Application::default()` supplies the default registry through the marker inserter instead of the inserter constructing concrete locators.

Implement one insertion strategy per native format. Strategies return an offset and the small inserted text, preserving every original byte around it. Use the file's existing newline convention, adding separators when needed without reformatting original content.

- PHPCS: recognize the first actual non-self-closing `ruleset` opening element, skipping comments, processing instructions, and other non-element text; account for quoted attributes when finding the end of the opening tag. Insert immediately after that tag. Unsupported or ambiguous structures produce manual-placement errors instead of document reserialization.
- PHPStan: recognize an unambiguous top-level block-form `parameters:` line, allowing a trailing comment. Insert at the beginning of its indented body. Reject unsupported inline or ambiguous forms and an absent section; do not create a second `parameters` section or merge existing paths and exclusions.
- PHP-CS-Fixer: use PHP's built-in tokenization to locate a conventional PHP opening tag and the end of required leading semicolon-form declarations, especially `declare(strict_types=1)`. Insert before existing executable configuration code. Recognize comments and whitespace without executing the file. Unsupported namespace, mixed-content, or declaration layouts receive manual-placement guidance rather than an unsafe insertion.

The bounded recognition is substantially smaller than migrating existing XML/NEON scopes or arbitrary PHP Finder expressions. A full parser or AST transformation adds dependencies without removing the agreed manual integration step. Do not widen accepted layouts with untested textual guesses; consumers can place markers themselves and retry.

### 6. Share safe replacement mechanics where appropriate

Preparation needs to replace a whole native file because it introduces a new block. Extract the reusable native replacement mechanics into `TargetWriter`, which accepts original and replacement bytes. Inject this writer directly into `Synchronizer`, keeping the drift check there and obtaining replacement bytes from `TargetInspection::replacement()`. Remove the redundant `SyncWriter` adapter. Marker preparation uses the same native writer for its empty-pair insertion. Preserve the existing synchronization safeguards and tests.

Both phases must preserve native permissions and line endings, reject symlinks, compare current content with inspected bytes immediately before replacement, and remove temporary files after errors. Each phase records a successful write only after replacement succeeds. Existing valid native blocks are not rewritten during preparation, and already synchronized blocks are not rewritten during synchronization.

This preserves the current per-target safety behavior while supporting insertion. It does not claim an atomic multi-file operation or eliminate every operating-system race. The new YAML's create-only behavior remains a separate responsibility.

### 7. Make review guidance accurate and reachable

At the end of target processing, print the exact three-line warning specified in the initialization spec to standard error when preparation or synchronization successfully changed at least one native file. Print it even if another target failed or synchronization failed after empty markers were successfully inserted. Creating only YAML is insufficient to trigger a native-file modification warning. The warning itself does not force an error exit code.

Keep ordinary statuses on standard output and target failures on standard error. Emit actionable insertion errors naming the file and the manual remedy. The warning URL is `https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks`, addressing the package's public documentation rather than a consumer-local `README.md`.

Extend the existing `Managed Blocks` section instead of changing its anchor. Document review of old PHPCS file/exclusion elements, duplicate PHPStan keys, overridden Finder variables, and manual `setFinder($finder)` integration. Explain that a zero exit code establishes package synchronization, while native QA correctness still depends on the consumer's review.

## Risks / Trade-offs

- Existing native scope settings can conflict with the newly filled block -> preserve them as requested, emit the review warning, and give concrete reconciliation examples in the linked section.
- Conservative insertion strategies reject unusual valid configurations -> return a local error with manual marker instructions and continue with other targets.
- A synchronization error may leave a successfully inserted empty pair -> retain completed writes, warn that files changed, and make retries idempotent using strict marker validation.
- Extracting synchronization or replacement helpers could change established commands -> keep the refactor narrow and run existing status, partial-failure, line-ending, permission, and concurrent-change regressions.
- Executable PHP before `declare(strict_types=1)` would invalidate a native configuration -> locate the preamble using tokens and test that generated Finder code appears after the declaration.
- `src` may not exist when scaffolding -> keep the requested default and document that consumers must adapt scope before running tools.

## Migration Plan

This is an additive CLI capability. Existing consumers may continue using `sync` and `check` without running `init`. Existing valid YAML is never rewritten by initialization. Consumers who run `init` review its file changes and reconcile old native settings before running QA tools; after review, `check` can verify synchronization.

Implementation must update the existing CLI and marker-validation requirements through the supplied delta, leaving unrelated main requirements intact. To undo an initialization in a consumer project, restore reviewed native configuration changes and remove the generated YAML only if it was newly created and is no longer wanted; no automatic rollback command is introduced.

### Initialization workflow extraction

Move discovery, YAML setup, scope calculation, marker insertion, target-local error reporting, and shared synchronization from `InitCommand` to `src/Initializer/Initializer.php`. Transfer all six workflow collaborators to its constructor. `initialize(string $root, Output $output): InitializerResult` keeps the existing output collaborator, matching `Synchronizer`; it returns `hasErrors` aggregated across marker insertion and synchronization, and `changed` aggregated across successful native writes in both phases. YAML creation alone does not set `changed`. Command-wide setup exceptions continue to propagate to `Application`, while target-local failures continue to permit other tools to proceed.

Keep `InitCommand` as the CLI adapter: it injects `Initializer`, passes the project root and output, emits the existing review warning when `changed` is true, and maps `hasErrors` to the CLI exit code. Keep all empty-marker insertion attempts before the single synchronization pass. Update application wiring to share the same synchronizer instance with `SyncCommand` and the initializer. Existing integration tests retain the same CLI expectations; direct initializer tests verify aggregated results for successful writes, unchanged retries, and marker-only writes followed by synchronization errors.

### Responsibility-based namespace organization

Organize the package by responsibility, preserving current method signatures, behavior, CLI output, YAML format, ordering, and write safeguards. Move all classes from `Config` to `Scope`, retaining their class names. Move and rename these collaborators:

| Current class | Final class |
| --- | --- |
| `Sync\ScopeSynchronizer` | `Synchronizer\Synchronizer` |
| `Sync\SyncResult` | `Synchronizer\SynchronizerResult` |
| `Init\ScopeFileCreator` | `Scope\ScopeInitializer` |
| `Init\Initializer` | `Initializer\Initializer` |
| `Init\InitResult` | `Initializer\InitializerResult` |
| `Sync\LocatedBlock` | `Block\LocatedBlock` |
| `Sync\ManagedBlock` | `Block\ManagedBlock` |
| `Init\MarkerInserter` | `Target\TargetInitializer` |
| `Sync\NativeFileWriter` | `Target\TargetWriter` |

`ScopeInitializer::create()` initializes or preserves the scope YAML. `TargetInitializer::insert()` initializes or validates native marker pairs. `TargetWriter::read()` and `write()` remain the shared native file operations. `Initializer::initialize()` coordinates the full setup and returns `InitializerResult`; `Synchronizer::synchronize()` returns `SynchronizerResult`. Keep the review warning and exit-code mapping in `InitCommand`, and keep one synchronizer shared with `SyncCommand` through application composition. Update all source imports, PHPDoc references, test references and matching test class/file names, and final architectural descriptions. Existing regressions and package QA establish behavior preservation; this structural refactoring needs no additional behavior tests.
