---
id: php-composition
title: PHP Composition Convention
when: Whenever creating, changing, testing, or documenting internal PHP tool identities, service constructors, factories, registries, application graphs, console composition, or CLI parsing and dispatch responsibilities.
---

# PHP Composition Convention

## Scope

CLI commands and YAML configuration are the supported consumer interfaces. PHP classes and public methods serve internal composition and testing; they are not a supported public programmatic API.

Keep consumer usage in `README.md`, durable composition rules here, and refactoring-specific migration details in the corresponding OpenSpec change artifacts. Documentation boundaries are defined in [conventions/repository.md](repository.md).

## Tool Identity

Use `GustavoPeixoto\PhpQaScope\Tool` for internal tool-selection parameters and native target identities. Its supported cases, in order, are:

- `Tool::Phpcs`, with backing value `phpcs`.
- `Tool::Phpstan`, with backing value `phpstan`.
- `Tool::PhpCsFixer`, with backing value `php-cs-fixer`.

Keep associative map keys, serialized YAML, and user-facing diagnostics as canonical backing-value strings. Validate configuration map shapes and key types before converting keys to enum identities, and reject unsupported keys with the configuration-specific diagnostic.

Use `$toolName` for a canonical tool string and `$tool` for a `Tool` instance, including configuration boundaries and tests. Keep conversion explicit so keys and enum selectors remain distinguishable.

The enum represents identity only. Keep filenames, marker formats, and indentation in target definitions, and native behavior in renderer and insertion-locator implementations.

Preserve selected configuration order without adding omitted tools. Default native target discovery retains the order `phpcs`, `phpstan`, `php-cs-fixer`.

## Service Responsibilities

`Scope\ScopeCalculator` calculates the effective per-tool scopes and returns `ToolScope` values. `Block\BlockLocator` locates and validates an existing managed block and returns `LocatedBlock`; insertion locators find positions for inserting absent marker pairs.

`Console\ConsoleWriter` writes stdout/stderr lines, retains in-memory buffers, and optionally mirrors them to supplied streams. It remains usable without attached streams.

## Reference Names

Name local variables, properties, and parameters after the collaborator's responsibility. Use clear service names such as `$scopeCalculator`, `$blockLocator`, and `$console` when a reference performs those operations. A name does not have to repeat the complete class name: `$console` and `$targets` are appropriate references to console-writing objects and a target registry.

Choose names that identify the collaborator's operation rather than the artifacts it operates on. An initializer, compiler, inspector, or writer should be recognizable as a service; names for markers, patterns, or files belong to the corresponding data. Test doubles should identify both their type and relevant behavior, such as a failing renderer. Qualify alternate instances when the distinction matters.

Distinguish collaborators from their results. Keep `$scopes` for a calculated scope map and `$block` for a located-block result. Retain clear names for stdout/stderr buffers or resources and injected or inspected writers. Do not rename unrelated data just because it shares a word with a service reference.

When changing a reference name, migrate its declaration, uses, PHPDoc, named argument callers, and reflection-based composition tests together. Keep method names and runtime behavior stable unless the change explicitly requires otherwise. Concrete migration mappings belong in the corresponding change artifacts.

## Console Composition

`Console\ConsoleWriterInterface` defines only `line(string $line): void` and `errorLine(string $line): void`. Command execution, command helpers, the initializer, and the synchronizer depend on this writing contract. Buffer inspection through `stdout()` and `stderr()` belongs to the concrete writer; alternate writers do not have to implement buffering or those getters.

`Console\Console` implements the writing interface and receives a required writer collaborator in its constructor, stored in a readonly property. It delegates each line unchanged to the corresponding writer method exactly once. The facade adds no buffering, formatting, stream management, or buffer getters, and constructs no fallback dependencies.

The executable composes `new Console(new ConsoleWriter(STDOUT, STDERR))` after loading the Composer autoloader. `Application::run(array $argv, Console $console, ?string $root = null): int` requires that concrete facade and passes the same instance to commands through the writing interface. Caught application errors use the same console. The application does not accept stream arguments, construct replacement console objects, reset supplied buffers, or store output in its command graph.

The caller owns console lifetime. Separate writer graphs stay isolated; explicitly reusing a writer retains its accumulated output. The writer and facade remain explicitly constructible without redundant `default()` factories or global caches. Tests may retain the concrete writer to inspect buffers, or supply another writing implementation through the facade.

`Console` is the common access point for writing and eventual reading, with each collaborator responsible for its own operations. Introduce reading only when an actual interactive operation requires it; do not add an empty interface, speculative reading methods, or an unused reader dependency.

When reading becomes necessary, follow the same composition in the `Console` namespace: `ConsoleReaderInterface` defines the required reading operations, `ConsoleReader` implements that contract, and the `Console` facade implements both `ConsoleReaderInterface` and `ConsoleWriterInterface`. Inject reader and writer through those contracts in the facade's constructor, and delegate each operation to the corresponding collaborator. Reading behavior belongs to the reader and writing behavior stays with the writer. This conditional design does not require a reader implementation before a concrete need exists.

Keep the executable's missing-autoload error on its direct stderr path because package classes are unavailable then. Argv parsing remains with `Cli\Input` and is separate from interactive console reading.

## Collaborator Injection And Factories

Service constructors require complete, non-null collaborator arguments and use the supplied instances. Do not construct missing collaborators through object parameter defaults, nullable fallbacks, or constructor bodies. Configuration validation and map indexing may occur in constructors.

Services that need a built-in standalone graph expose a zero-argument `default()` factory. Each call creates a complete, independent graph using the supported implementations. Keep data objects and leaf services without collaborator dependencies directly constructible; classes already using explicit construction do not require a redundant factory.

The current standalone factories include `ScopeCalculator`, the three native renderers, `TargetInspector`, `TargetInitializer`, and `Initializer`. Native registries also expose `default()` for their built-in entries.

## Registries

Native registries receive already constructed entries in readonly mappings keyed by canonical tool backing values. Enum selectors resolve those supplied entries without substituting built-in implementations. An omitted registration produces the registry-specific exception using the canonical tool identifier.

Each target map key must match the corresponding `TargetFile::$tool` backing value. Reject mismatches during construction before discovery or file access, and use the supplied target path during discovery.

Do not introduce singleton accessors, process-global instance caches, or registry mutation APIs. Separate default registry calls create independent registries and entries; custom mappings do not affect defaults.

`CommandRegistry` receives already constructed commands and indexes their string names. Command construction belongs to the application graph.

## Application Composition

Compose the built-in command graph in `Application::default()`. Share its loader, effective-scope calculator, target registry, marker locator, and file writer across the services that need them.

Initialization and inspection use the same loader, scope calculator, and target definitions. Marker preparation and inspection use the same marker locator; marker preparation and synchronization use the same writer. The commands receive the graph's existing inspector, synchronizer, and initializer instances.

Use explicit constructors when assembling shared graphs so nested standalone factories do not create unintended duplicate collaborators. Each application factory call creates an independent graph.

## CLI Parsing And Dispatch

Command names remain strings. `CommandRegistry::usage()` derives its supported-name list from the registered command keys, preserving registration order, and formats it with `sprintf`:

```php
sprintf('Usage: php-qa-scope <%s>', implode('|', array_keys($this->commands)))
```

The built-in application registers `init`, `sync`, and `check` in that order. Custom registries advertise only their supplied commands.

`Input::fromArgv()` receives the application-supplied usage text and an optional root override. It rejects extra arguments, resolves the project root, preserves unknown command names, and represents an absent command with an empty string. `CommandRegistry::get()` owns validation of missing and unknown command names.

The application supplies the same registry-derived usage text for missing-command, unknown-command, and extra-argument errors. Input parsing receives that text rather than a command registry or a duplicated command list. Preserve the CLI's existing `ERROR ` prefix and error exit code `2`.
