# Proposal

## Why

Tool identifiers are repeated across configuration validation and native registries, while dependency construction mixes explicit injection, constructor defaults, and nullable fallbacks. A typed tool identity, consistent composition factories, and class names that describe operational responsibilities will make the internal PHP interface easier to customize and test while preserving the CLI and configuration formats.

## What Changes

- Introduce the string-backed `GustavoPeixoto\PhpQaScope\Tool` enum in `src/Tool.php`, with `Phpcs = 'phpcs'`, `Phpstan = 'phpstan'`, and `PhpCsFixer = 'php-cs-fixer'`.
- **BREAKING**: replace string tool parameters and `TargetFile::$tool` with `Tool`, return enum cases from `ScopeConfig::managedTools()`, and replace `ScopeConfig::TOOLS` with values derived from the enum.
- Convert YAML tool keys at the configuration boundary while retaining canonical string keys for associative arrays and serialized YAML.
- **BREAKING**: make collaborator dependencies required constructor arguments; move built-in construction into static `default()` factories.
- Make `TargetRegistry` accept supplied target definitions and expose `default()`, matching the existing renderer and insertion-locator registry pattern.
- Keep registries independently constructible and share instances within each application graph. Factories create fresh graphs rather than process-global singletons.
- Keep `CommandRegistry` accepting already constructed commands, with command wiring in `Application::default()`.
- Add `CommandRegistry::usage()` to derive usage text from registered command names with `sprintf` and `implode('|', array_keys($this->commands))`; use that same text for missing or unknown commands and extra arguments.
- **BREAKING**: make `Input::fromArgv()` receive the usage text supplied by the application, reject only extra arguments, and normalize an absent command to an empty string with `$argv[1] ?? ''`. Command-name validation, including the missing-command error, belongs to `CommandRegistry`.
- Register default commands in `init`, `sync`, `check` order to preserve the existing default usage text while custom registries advertise their own commands in registration order.
- Rename the internal services `Scope\EffectiveScope` to `Scope\ScopeCalculator`, `Block\ManagedBlock` to `Block\BlockLocator`, and `Cli\Output` to `Cli\ConsoleWriter`, keeping the existing package namespace root. Update their files, imports, type declarations, factory wiring, tests, PHPDoc, and internal documentation while preserving methods and behavior. Other existing production types keep their names.
- Move the implemented writer from `Cli\ConsoleWriter` to `Console\ConsoleWriter` in `src/Console/ConsoleWriter.php` and add `Console\ConsoleWriterInterface` in `src/Console/ConsoleWriterInterface.php`. The writing contract declares only `line(string $line): void` and `errorLine(string $line): void`; commands and services that emit messages depend on this interface. Buffer inspection remains on the concrete writer.
- Add `Console\Console` in `src/Console/Console.php` as a facade implementing `ConsoleWriterInterface`, with a required injected writer and delegation of `line()` and `errorLine()` to it. Preserve buffer-only operation and optional stdout/stderr stream mirrors in the concrete writer. Defer reader abstractions; do not introduce an empty reader interface or an unused injected reader.
- Document `Console` as the common access point for writing and eventual reading. Reading types are introduced only when an actual interactive operation needs them; when introduced, `ConsoleReaderInterface` defines those operations, `ConsoleReader` implements the contract, and `Console` implements both reading and writing interfaces with injected reader/writer collaborators and delegation. This change records that direction without implementing reading.
- Rename service references in local variables, properties, and parameters across `src/` and `tests/`: writing objects currently named `$output` become `$console`; `ScopeCalculator` references named `$scopes` or `$effectiveScope` become `$scopeCalculator`; `BlockLocator` references named `$blocks` or `$managedBlock` become `$blockLocator`. Migrate PHPDoc, named arguments, and reflection-based composition tests. Preserve `$scopes` for calculated maps, `$block` for `LocatedBlock`, `$targets` for `TargetRegistry`, and buffer/stream names. Document responsibility-based naming without requiring every variable to repeat its class name.
- **BREAKING**: change the application entrypoint to `run(array $argv, Console $console, ?string $root = null): int`. `bin/php-qa-scope` constructs `new Console(new ConsoleWriter(STDOUT, STDERR))` after autoloading and passes it directly to the application. Commands still accept `ConsoleWriterInterface`; dispatch and caught-error reporting use the supplied facade without creating or replacing it. Keep the missing-autoload diagnostic on its existing direct `fwrite()` path.
- Preserve tool names, native paths, markers, discovery and execution order, default CLI output, exit codes, and file safety behavior.

- Treat CLI commands and YAML configuration as the supported consumer interfaces. PHP classes and their public methods remain internal implementation details without a supported programmatic compatibility contract.
- Remove the README's `PHP API` section, record durable composition rules in `conventions/php-composition.md`, and retain refactoring-specific migration details in this change's design. Index the convention in `AGENTS.md` and clarify the consumer boundary in `conventions/repository.md`.

## Capabilities

### New Capabilities

- `library-composition`: the internal PHP interface contract for typed tool identity, custom registries, explicit dependency injection, default construction, application-local sharing, responsibility-based service and reference names, console-writing abstraction and facade injection at the executable boundary, documented deferred reader composition, and usage text derived from supplied commands.

### Modified Capabilities

None. The requirements of `managed-scope-sync` and `scope-initialization` remain unchanged; their existing scenarios are regression acceptance criteria.

## Impact

- Affects `bin/php-qa-scope`, `src/Tool.php`, `Application`, `CommandRegistry`, `Cli/Input`, scope configuration/loading/initialization, `ScopeCalculator`, `BlockLocator`, `Console/ConsoleWriter`, the new `Console/ConsoleWriterInterface` and `Console/Console` facade, target definitions and operations, the three native renderers, renderer and insertion-locator registries, `Initializer`, command tool loops, and `Synchronizer`.
- Changes PHP constructor, tool-selection, and input-parsing APIs. This compatibility break is accepted for the change; existing PHP callers and tests must migrate to enum cases, explicit injection or `default()`, and application-supplied usage text. Direct parsing without a command returns an input containing an empty command instead of throwing a usage error; the application still rejects that command through its registry.
- Documentation changes affect `README.md`, `AGENTS.md`, `conventions/php-composition.md`, and `conventions/repository.md`.
- Requires no new dependency or PHP minimum-version change; Composer already requires PHP 8.3 or newer.
- The completed stages renamed three production types, moved the writer to the `Console` namespace, introduced a writing interface and facade, and changed `Application::run()` to require that facade before the optional root. The reference-name revision changes only the specified service-reference names and internal parameter names, with named callers, PHPDoc, and composition tests migrated together; no compatibility aliases are required for these internal names. Result and value types, methods, other namespaces, and consumer interfaces retain their current names and behavior. Reading guidance is documentation of a conditional future design, not an implementation task.
- Tests must retain string-based YAML/native-file fixtures and exercise custom collaborator isolation alongside existing CLI integration coverage.
- Out of scope: new tools, command-name enums, global caching, a dependency-injection container, moving native metadata into the enum, changing native-file behavior, implementing reader interfaces or classes, stdin interaction, renaming unrelated references or data variables, inventing future reading methods, or implementing this proposal during planning.
- Principal risks are missed string-to-enum boundaries, changed target order, altered error messages, and accidentally constructing separate collaborators where the application should share them, and leaving stale class imports, file paths, or type declarations during the three renames. The design and tasks include focused regression checks for these risks.
- Consulted durable context: `AGENTS.md`, `README.md`, applicable conventions, both existing capability specs, current source, and unit/integration tests. This proposal and its dependent artifacts contain the decisions needed to continue without the exploration conversation.

## Open Questions

No blocking open questions remain. The internal PHP interface compatibility break is accepted; the CLI and YAML remain compatible. Concrete constructor signatures and graph wiring are specified in `design.md`.
