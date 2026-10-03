# Design

## Context

See `proposal.md` for motivation and compatibility scope. `RendererRegistry` and `InsertionLocatorRegistry` already accept supplied maps and provide factories. `TargetRegistry` constructs three target definitions in its constructor, and `CommandRegistry` indexes supplied command instances. `TargetInspector::default()` currently delegates to a constructor that creates missing collaborators. Other constructors use instantiated objects as parameter defaults.

`ScopeConfig::TOOLS` repeats the canonical tool strings used by registries. Tool selectors, `TargetFile::$tool`, and configuration tool lists currently use strings. Associative scope and target maps preserve insertion order, which influences generated YAML, discovery, and command output. The package supports PHP 8.3 or newer, so backed enums require no platform change.

`CommandRegistry::get()` and `Input::fromArgv()` both hard-code `Usage: php-qa-scope <init|sync|check>`. The application currently registers commands in `check`, `sync`, `init` order, so simply deriving names from its map would change the default usage text and leave invalid argument counts using a different source.

## Goals / Non-Goals

**Goals:**

- Give PHP callers a closed, typed vocabulary for supported tools.
- Make the supplied collaborator graph authoritative and independently constructible.
- Provide convenient standalone defaults while allowing the application to share collaborators explicitly.
- Preserve every existing CLI and native-file behavior while migrating PHP callers in one change.
- Name the scope calculator, managed-block locator, and console writer after their operational responsibilities.
- Separate the console-writing contract from buffered output storage so internal commands can accept supplied writers.
- Compose a `Console` facade in the executable and pass it explicitly to each application invocation.
- Align service-reference names with their responsibilities while preserving clear names for result data, registries, streams, and writer collaborators.
- Record the console's future reading composition without introducing unused reading types today.

**Non-Goals:**

- Offering PHP classes as a supported public programmatic API.
- Renaming existing production types beyond decision 8 and the writer namespace move in decision 9, extracting concrete services beyond the console facade, or changing existing writer method responsibilities.
- Implementing reader interfaces or classes, stdin interaction, defining speculative reading operations, or renaming references unrelated to the three service roles specified in decision 10.
- Global singletons, static collaborator caches, a container, or a plugin registration mechanism.
- Enum methods that construct renderers, locators, or targets.
- Factories for data-only objects or blanket factories for classes already requiring explicit collaborators.

## Decisions

### 1. Place tool identity at the package namespace root

Create `src/Tool.php` in `GustavoPeixoto\PhpQaScope` as `enum Tool: string`, declaring `Phpcs = 'phpcs'`, `Phpstan = 'phpstan'`, and `PhpCsFixer = 'php-cs-fixer'` in that order. The enum contains identity only. Native paths, markers, and indentation remain target definitions; rendering and insertion behavior remain registry entries.

The package root expresses that scope, targets, renderers, and insertion locators all depend on this concept. A `Scope`-specific enum would misrepresent ownership. Constants would centralize spelling but leave arbitrary string arguments valid; a backed enum also supplies the PHP type contract.

### 2. Use enums for selectors and canonical strings for array keys

Change tool selectors in `ScopeConfig::tool()`, each native registry's `get()`, `TargetInspector::target()` and `inspect()`, `TargetInitializer::insert()`, and the synchronizer's target helper to `Tool`. Change `TargetFile::$tool` to `Tool`. `ScopeConfig::managedTools()` returns `list<Tool>` in the existing YAML key order.

Keep scope, discovered-target, renderer, locator, and target maps keyed by the enum's string value. PHP cannot use enum objects as array keys. Lookup uses `$tool->value`, and diagnostics interpolate that value rather than the enum object. APIs returning maps retain their existing canonical string keys; PHPDoc specifies the value types and allowed key vocabulary.

`ScopeLoader` validates the tools map shape and each key's string type before calling `Tool::tryFrom()`. Reject a failed conversion with the existing `tools: unknown key '<key>'.` diagnostic. Build configuration entries under the accepted case's value. Remove `ScopeConfig::TOOLS`; derive the allowed vocabulary from enum cases instead of introducing another literal list. `ScopeConfig` construction must also reject unsupported supplied keys, so callers cannot create a configuration whose `managedTools()` would later leak an unexpected `ValueError`.

Command and synchronizer loops that consume canonical string-keyed scope maps convert each validated key to a case before invoking typed operations. `ScopeInitializer` serializes canonical string values and never enum objects. YAML fixtures, filenames, Composer command strings, and user-facing documentation retain their existing strings; the refactoring targets identity literals rather than every textual occurrence of a tool name.

Keep both existing orders: default target discovery is `phpcs`, `phpstan`, `php-cs-fixer`, while managed configuration processing follows YAML insertion order. Iterating all enum cases must not replace iteration over selected configuration keys.

### 3. Make registries independent immutable mappings

Change `TargetRegistry` to accept a required `array<string, TargetFile>` and store it without constructing entries. Its `default()` creates the three existing definitions using enum values as keys and enum cases as `TargetFile` identities. Preserve native filenames, markers, indentation, and discovery behavior exactly.

Retain supplied-map constructors for renderer and insertion-locator registries. Their factories construct built-in implementations using each implementation's `default()` when it needs collaborators. Use readonly storage where possible. No registry adds a mutation API, singleton accessor, or static instance cache.

`CommandRegistry` keeps its supplied `list<Command>` constructor and name indexing. Command names remain strings. It does not gain a default factory because application wiring owns command construction and the shared graph.

Constructor maps remain keyed by canonical tool values, including custom subsets for tests and callers. Missing registration retains the current exception category and message using the canonical value. A target map entry must agree with the supplied target's enum identity; reject a mismatch immediately rather than discovering or writing a different tool than requested.

### 4. Move collaborator creation into factory boundaries

Remove instantiated parameter defaults and nullable construction fallbacks from:

- `TargetInspector`: required `ScopeLoader`, `ScopeCalculator`, `RendererRegistry`, `TargetRegistry`, and `BlockLocator`.
- `TargetInitializer`: required `InsertionLocatorRegistry`, `TargetRegistry`, `BlockLocator`, and `TargetWriter`.
- `Initializer`: required `Synchronizer`, `TargetInitializer`, `ScopeInitializer`, `TargetRegistry`, `ScopeLoader`, and `ScopeCalculator`.
- `ScopeCalculator` and the three native renderers: required `PatternCompiler`.
- `TargetRegistry`: required target definitions as described above.

Retain unaffected parameter names. Decision 10 specifies the service-reference parameter renames and migration of named callers. Constructors can validate or index their inputs, but they do not create or substitute collaborator objects.

Add or revise zero-argument static `default(): self` factories for these classes. Each factory creates a fresh, complete usable graph. Within `Initializer::default()`, explicitly wire one loader, effective-scope calculator, target registry, managed-block locator, writer, inspector, and synchronizer into the marker preparer and initializer so initialization and synchronization use the same collaborators. A standalone `TargetInspector::default()` or `TargetInitializer::default()` creates its own complete graph.

Do not add redundant factories to `Synchronizer`, commands, `CommandRegistry`, or data-only types. They already support explicit construction; the enclosing composition factory constructs them. Leaf collaborators without constructor dependencies, such as `PatternCompiler`, remain directly constructible.

### 5. Keep application-local sharing explicit

`Application::default()` builds one loader, effective-scope calculator, target registry, managed-block locator, writer, scope initializer, renderer registry, insertion-locator registry, inspector, marker preparer, initializer, and synchronizer for that application. It supplies the same loader, scope calculator, and target registry to the inspector and initializer; the marker preparer also receives that target registry and managed-block locator. Marker preparation and synchronization receive the same writer.

Construct commands using the shared inspector, synchronizer, and initializer, then pass them to `CommandRegistry`. Factories may use explicit constructors to assemble this graph; requiring nested `default()` calls would hide sharing and create unwanted duplicate subgraphs. Standalone factories and application wiring use the same built-in definitions and implementation choices.

Different calls to `Application::default()` and registry `default()` produce independent object graphs. Reusing instances inside one graph avoids unnecessary construction without introducing process-global lifetime or coupling custom test implementations across graphs. This is preferable to singleton registries, which would restrict independent supplied mappings and complicate tests.

### 6. Derive command usage once and format it with sprintf

Add public `CommandRegistry::usage(): string`, documented as the usage text for the commands in that registry. Build the text with `sprintf('Usage: php-qa-scope <%s>', implode('|', array_keys($this->commands)))`. Use `sprintf` rather than string concatenation. The command map is the sole source of the supported-name list; no second list or sorting step is introduced.

`CommandRegistry::get()` throws its existing `RuntimeException` with `$this->usage()` for an unknown command, including the empty command representing an absent name. `Application::run()` supplies `$this->commands->usage()` to input parsing. Change the parser signature to `Input::fromArgv(array $argv, string $usage, ?string $root = null): self`; it throws the existing `RuntimeException` with the supplied text only when `count($argv) > 2`, preserving the rejection of extra arguments. Update the application call to `Input::fromArgv($argv, $this->commands->usage(), $root)` and migrate other PHP call sites. Input parsing has no dependency on `CommandRegistry` and no default hard-coded usage string.

After resolving the project root with the existing logic, input parsing returns `new self($argv[1] ?? '', $resolvedRoot)`. An empty argv list or a list containing only the executable name therefore produces an input with an empty command. A supplied unknown name is also retained unchanged. The parser does not check command registration; the application forwards the parsed name to the registry, which owns missing- and unknown-command errors. Keep root-resolution failures in the parser and reject extra arguments before resolving the root or dispatching a command. Update the input type's documentation so that it does not claim the command name has already been validated.

Construct default commands in `init`, `sync`, `check` order. Dispatch still resolves commands by name, so this registration-order change preserves execution behavior while producing the exact existing default usage text. A custom registry advertises only its supplied commands in map insertion order for missing commands, unknown commands, and extra arguments. Keep the application's `ERROR ` prefix and exit code `2` unchanged.

Keeping the existing duplicate strings would allow parser and registry messages to diverge. Passing the registry object into `Input` would introduce an unnecessary dependency on command dispatch. Passing the already formatted string keeps the formatter and command vocabulary with the registry while leaving parsing responsible for extra-argument validation. Retaining `count($argv) !== 2` would make the missing-command fallback unreachable; removing argument-count validation entirely would silently accept extra arguments, so the parser rejects only counts greater than two.

### 7. Keep consumer documentation focused on supported interfaces

CLI commands and YAML configuration are the supported consumer interfaces. The PHP classes, including public methods, are internal implementation details; PHP visibility enables composition and testing without promising a supported programmatic API.

Remove the `PHP API` section from `README.md`. Keep its CLI, YAML, managed-file behavior, and contributor entrypoint guidance. Record the reusable rules for tool identity, required collaborator injection, standalone `default()` factories, independent registries, application-local sharing, and input/command responsibilities in `conventions/php-composition.md`, indexed by `AGENTS.md`. Clarify the same consumer boundary in `conventions/repository.md`.

Retain change-specific migration details here: internal selectors now require `Tool`; `ScopeConfig::TOOLS` is replaced by enum-derived values; affected constructors require explicit collaborators or factory construction; and `Input::fromArgv()` receives usage text before the optional root. These changes require updating internal call sites and tests, not consumer YAML or CLI invocations.

Documenting all classes as a consumer API would imply a compatibility commitment outside the current product scope. Moving the entire README section into a convention would also preserve release-specific migration instructions as permanent rules, so distill only durable composition guidance.

### 8. Name the three services after their responsibilities

The completed rename stage retained the existing `GustavoPeixoto\PhpQaScope` namespace root and subnamespaces and renamed only the three production types below with their corresponding PSR-4 files. The table records the identities reached at that stage; decision 9 moves the intermediate `Cli\ConsoleWriter` identity to its final `Console` namespace.

| Existing type and file | Final type and file |
| --- | --- |
| `Scope\EffectiveScope` in `src/Scope/EffectiveScope.php` | `Scope\ScopeCalculator` in `src/Scope/ScopeCalculator.php` |
| `Block\ManagedBlock` in `src/Block/ManagedBlock.php` | `Block\BlockLocator` in `src/Block/BlockLocator.php` |
| `Cli\Output` in `src/Cli/Output.php` | `Cli\ConsoleWriter` in `src/Cli/ConsoleWriter.php` |

`ScopeCalculator` calculates per-tool scopes from `ScopeConfig` and still returns the existing string-keyed `ToolScope` map. It retains the injected `PatternCompiler`, `calculate()`, and standalone `default()` factory.

`BlockLocator` locates and validates existing managed marker pairs and still returns `LocatedBlock`. It retains `locate()` and the current diagnostics for missing, repeated, reversed, or invalidly indented markers. It remains distinct from `InsertionLocator`, which finds a position for inserting absent markers.

`ConsoleWriter` writes stdout/stderr lines and retains both in-memory buffers and optional stream mirrors. It retains its constructor options and `line()`, `errorLine()`, `stdout()`, and `stderr()` methods, including operation without attached console streams. It does not become a wrapper that requires direct terminal access.

Replace references in imports, type declarations, factory wiring, tests, PHPDoc, and `conventions/php-composition.md`. Rename a test type and its file when they directly name a renamed subject, such as `ManagedBlockTest` to `BlockLocatorTest`; do not rename unrelated tests. The completed class-rename stage preserved method and parameter names apart from their type references and removed the old production files without compatibility aliases. Decision 10 governs the subsequent service-reference renames; method names remain unchanged.

Keep all other production names, including `LocatedBlock`, `ToolScope`, `TargetInspection`, `ScopeInitializer`, `TargetInitializer`, and `TargetFile`. No new data type, service extraction, behavioral change, CLI/YAML change, or dependency is required.

The old names suggest represented values while the objects process caller-supplied data. The selected names state their roles, and their existing namespaces supply the domain context without repeating it in every name.

### 9. Introduce a console-writing contract and an explicitly supplied facade

Move `Cli\ConsoleWriter` to `Console\ConsoleWriter`, keeping the package namespace root, and move its PSR-4 file from `src/Cli/ConsoleWriter.php` to `src/Console/ConsoleWriter.php`. Add `src/Console/ConsoleWriterInterface.php` in `GustavoPeixoto\PhpQaScope\Console` with exactly two methods:

```php
public function line(string $line): void;
public function errorLine(string $line): void;
```

The concrete writer implements that interface and preserves its optional stream constructor arguments, newline behavior, accumulated stdout/stderr buffers, and `stdout(): string` and `stderr(): string` getters. The getters belong only to the concrete writer; alternate writers do not have to implement buffering. This is an internal composition contract, not a supported consumer API.

Change writing parameters in `Command::execute()`, its implementations and helpers, `Initializer`, and `Synchronizer` to `ConsoleWriterInterface`. Update test command implementations, imports, and PHPDoc consistently. No writing consumer may require the concrete writer or call its buffer getters. Tests that inspect buffered output retain a concrete `ConsoleWriter` reference.

Add `src/Console/Console.php` in `GustavoPeixoto\PhpQaScope\Console` as a final facade implementing `ConsoleWriterInterface`. Its constructor requires a `ConsoleWriterInterface` collaborator, stored as a readonly property, and constructs no dependency. `line()` and `errorLine()` each delegate once to the corresponding method of that supplied writer with the unchanged argument. The facade adds no buffers, newline formatting, stream management, or buffer getters. Tests inspect the injected concrete writer when they need buffered output. Both the writer and facade remain explicitly constructible; this extension adds no `default()` factories for them.

Change the application signature to `public function run(array $argv, Console $console, ?string $root = null): int`. The parameter is the concrete facade, not `ConsoleWriterInterface`. Remove the stream parameters and internal writer construction. Pass the supplied facade directly to command execution, which still accepts the writing interface, and report caught errors through the same facade. Do not replace the facade or its writer, clear buffers, attach streams, store invocation output in the application graph, or cache console objects globally. The caller owns console lifetime: separate supplied graphs remain isolated, while explicitly reusing the same concrete writer retains its accumulated output.

After successful autoloading, `bin/php-qa-scope` constructs the facade and writer and invokes the application as follows, using the planned `Console` namespace imports:

```php
$console = new Console(new ConsoleWriter(STDOUT, STDERR));
exit(Application::default()->run($_SERVER['argv'] ?? [], $console));
```

The executable is the stream-composition boundary. Keep the existing autoload search paths and the direct `fwrite(STDERR, ...)` missing-autoload diagnostic and exit code `2`; the package classes are unavailable on that error path. Migrate all internal `run()` calls and tests to supply a facade, then the optional root, instead of the former root and stream arguments. This internal signature change does not change the consumer CLI invocation.

`Console` is the common access point for console operations. Its facade role preserves a place to compose writing and eventual reading behind one application-facing object, while each collaborator owns its operations. Reading remains deferred until an actual interactive operation requires it. Do not add an empty interface, speculative reading methods, or an unused reader dependency in this change.

When reading becomes necessary, follow the proposed composition in the same `GustavoPeixoto\PhpQaScope\Console` namespace: `ConsoleReaderInterface` declares the required reading operations; `ConsoleReader` implements that interface; and `Console` implements both `ConsoleReaderInterface` and `ConsoleWriterInterface`, receives collaborators through those interfaces by constructor injection, and delegates each operation to the corresponding reader or writer. Reading behavior belongs to the reader, and writing behavior remains with the writer. Keep `Cli\Input` responsible for argv parsing, which is distinct from interactive console reading. This direction is durable composition guidance, not authorization or a commitment to implement a reader now.

Decision 8 records the already completed renames. Its `Cli\ConsoleWriter` mapping is the intermediate implemented identity; decision 9 defines the final writer namespace. The completed console stage retained command/workflow parameter names while adding the explicitly named `$console` application parameter. Decision 10 now defines the subsequent reference-name revision. Keep the old `Cli` writer file removed without a compatibility alias.

Verify facade delegation and substitution with a recording implementation of the writing interface that has no buffer getters, exercising real command/workflow output and application error handling. Verify that the same supplied facade reaches command execution and caught-error reporting, separately composed consoles remain isolated, and explicit writer reuse preserves buffers. Existing buffer and stream tests cover concrete writer compatibility, and executable/CLI integrations cover output, usage diagnostics, exit codes, and autoload behavior. Update `conventions/php-composition.md` during application to describe the final namespace, facade injection, executable stream composition, and deferred reading responsibility.

### 10. Name references after the collaborator's responsibility

Apply these type-directed substitutions to local variables, properties, and parameters in `src/` and `tests/`, including promoted constructor properties, factory wiring, PHPDoc, named arguments, and reflection-based composition assertions:

| Referenced service | Existing names | Final name |
| --- | --- | --- |
| `Console`, `ConsoleWriterInterface`, or concrete `ConsoleWriter` | `$output` | `$console` |
| `ScopeCalculator` | `$scopes`, `$effectiveScope` | `$scopeCalculator` |
| `BlockLocator` | `$blocks`, `$managedBlock` | `$blockLocator` |

In particular, update calculator/locator locals in `Application::default()` and `Initializer::default()`, calculator properties in `Initializer` and `TargetInspector`, locator properties in `TargetInspector` and `TargetInitializer`, and writing parameters in `Command::execute()`, its implementations/helpers, `Initializer`, and `Synchronizer`. Migrate all corresponding test construction and named arguments such as `scopes:`, `effectiveScope:`, `blocks:`, and `managedBlock:` when they select these collaborators. Reflection-based tests must refer to the new property names so they continue to verify the same sharing relationships.

Do not globally replace words or match names without examining their types and use. Preserve `$scopes` for calculated scope maps and `$block` for a `LocatedBlock` result. Keep `$targets` for `TargetRegistry`, `$stdout`/`$stderr` for buffers or resources, and `$writer` or subject-specific writer names where they clearly identify the injected writer or a concrete writer whose buffers are inspected. Keep method names, result types, CLI text, YAML keys, and runtime behavior unchanged. Naming by responsibility does not require a variable to copy its class name.

The previous parameter-name preservation statements describe the completed class-rename and console stages; this decision intentionally supersedes them for the listed references only. These are internal parameter names, so migrate package callers and tests together without aliases or named-argument fallbacks. Keep all other collaborator names unchanged.

Update `conventions/php-composition.md` during application with the reusable responsibility-based naming rule and the conditional future reader composition from decision 9. Keep the concrete old-to-new mappings here as change-specific migration details. The README continues to document supported CLI/YAML usage.

## Risks / Trade-offs

- [Renaming data accidentally or leaving stale named/reflection callers] -> Apply the substitutions by service type and role, preserve result-map and buffer/resource names, migrate PHPDoc and named arguments with declarations, and rerun existing composition tests against the same shared graph.
- [Conditional reader guidance interpreted as current implementation scope] -> Document the future injected reader/writer composition explicitly while keeping all reader code and speculative operations out of this change.
- [Internal PHP interface break] -> Migrate all package tests and PHP call sites together, document required dependencies, and provide zero-argument defaults for the affected service classes. No transitional nullable fallbacks remain.
- [Enum serialization or interpolation failure] -> Keep array and YAML keys as backing values, explicitly convert at selectors, and retain literal external fixtures and output expectations.
- [Selection or discovery order changes] -> Preserve insertion-ordered maps and retain the existing discovery-combination and scope-selection tests.
- [Generic enum errors replacing configuration diagnostics] -> Validate string keys with `tryFrom()` and retain the configuration error messages and CLI error precedence.
- [Default graph drift] -> Exercise the CLI's default graph and standalone inspector, marker, and initializer factories with the same behavior coverage; review the explicit shared wiring.
- [Accidental fallback instead of supplied dependency] -> Retain failing/custom renderer and locator tests and add focused isolation coverage where existing tests do not cover separate registry instances.
- [Usage text changes or missing/extra arguments follow the wrong validation path] -> Register default commands in `init`, `sync`, `check` order, verify direct parsing of missing and unknown command names, and verify that the application rejects missing/unknown commands through the registry while parsing rejects extra arguments using the same registry-derived text.

- [Stale names after renaming] -> Update PSR-4 filenames, declarations, imports, wiring, PHPDoc, tests, and the composition convention together. Audit final source and documentation references; old names may remain only in explicit migration mappings or historical evidence in this change.

## Migration Plan

1. Introduce the enum and migrate tool selectors, configuration boundaries, map conversions, and PHPDoc together. Keep string fixtures and serialized configuration unchanged.
2. Add the injectable target registry and normalize built-in native registries without changing mapping order or metadata.
3. Replace constructor defaults and fallbacks with required collaborators and standalone factories. Rewire the default application graph explicitly.
4. Centralize usage formatting in `CommandRegistry::usage()` with `sprintf`, pass that text through the application to input parsing, normalize missing command names to empty strings, reject only extra arguments in the parser, and preserve the default command-list order.
5. Update every affected test construction and PHP call site; add meaningful coverage for direct configuration validation, custom target mappings, factory usability, registry isolation, and consistent custom/default command usage.
6. Rename the three internal services and matching subject-specific tests, migrate all type references, and update the composition convention to the final names without changing methods or behavior.
7. Move the console writer to `src/Console/`, add its two-method writing interface and injected-writer facade, migrate writing consumers and test command implementations, and require `Console` in `Application::run()`. Compose it in the executable, migrate all run callers, and verify delegation, supplied-instance handling, and buffer/stream compatibility. Update the composition convention without expanding the README's consumer interface boundary.
8. Apply the type-directed service-reference renames in decision 10, migrate PHPDoc, named arguments and reflection-based tests, and update the composition convention with responsibility-based naming and conditional reader composition.
9. Run existing unit/integration coverage and package QA through the PHP environment, verify CLI configuration compatibility, and validate the OpenSpec change. Keep durable PHP composition rules in the indexed convention and retain this change's migration details here; keep the README focused on CLI and YAML usage.

This is an atomic source/API refactoring with no persisted-state migration. If reverted, restore the prior code and its internal composition documentation together; existing consumer YAML and native configurations need no conversion or rollback.
