# Spec Delta

## Purpose

Define internal PHP tool identity, construction, service-reference naming, console composition, conditional future reading guidance, and command usage contracts for composition and testing while retaining compatible YAML configuration and default CLI behavior. These internal contracts do not establish a supported public programmatic API.

## ADDED Requirements

### Requirement: Supported consumer interfaces and documentation

The package SHALL treat CLI commands and YAML configuration as its supported consumer interfaces. PHP classes and methods SHALL remain internal implementation details without a supported public programmatic API commitment. The README SHALL document consumer usage without a PHP API section. Durable PHP composition rules SHALL be recorded in an indexed repository convention, and refactoring-specific migration details SHALL remain in the change artifacts.

#### Scenario: Consumer documentation

- **WHEN** a package consumer reads the README
- **THEN** it SHALL explain installation, CLI commands, YAML configuration, and managed-file behavior
- **AND** it SHALL NOT present internal PHP classes as a supported public API

#### Scenario: Contributor composition guidance

- **WHEN** a contributor consults the conventions index in `AGENTS.md`
- **THEN** it SHALL link to `conventions/php-composition.md`
- **AND** that convention SHALL describe tool identities, explicit collaborator injection, default factories, independent registries, application-local sharing, and parsing/dispatch responsibilities
- **AND** change-specific migration instructions SHALL remain in this change's design rather than becoming permanent composition rules

### Requirement: Internal service names describe their operations

The package SHALL use `GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator`, `GustavoPeixoto\PhpQaScope\Block\BlockLocator`, and `GustavoPeixoto\PhpQaScope\Console\ConsoleWriter` as the final identities of the existing scope calculation, managed-block location, and buffered console output services. Their PSR-4 files, declarations, references, and composition guidance SHALL use those names. The rename and writer namespace move SHALL preserve existing concrete method contracts and behavior, remove the old production types and intermediate `Cli\ConsoleWriter` without compatibility aliases, and retain all other existing production type names. Writing consumers SHALL use the new interface specified below.

#### Scenario: Scope calculator identity and contract

- **WHEN** the internal application or a test constructs `ScopeCalculator` with its compiler or through `default()`
- **THEN** `calculate()` SHALL return the existing canonical string-keyed map of `ToolScope` values in selected configuration order
- **AND** calculation, validation, injected-collaborator, and independent-factory behavior SHALL remain unchanged

#### Scenario: Managed-block locator identity and contract

- **WHEN** the internal target workflow calls `BlockLocator::locate()` with native file content and a target definition
- **THEN** it SHALL return the existing `LocatedBlock` result
- **AND** marker validation, offsets, content, line endings, and error messages SHALL remain unchanged
- **AND** insertion position strategies SHALL retain their existing `InsertionLocator` names

#### Scenario: Buffered console writer identity and contract

- **WHEN** an internal command uses `ConsoleWriter` with optional stdout/stderr stream mirrors
- **THEN** `line()` and `errorLine()` SHALL retain the existing line-writing behavior
- **AND** `stdout()` and `stderr()` SHALL retain the accumulated in-memory output, including when no streams are supplied
- **AND** default CLI output, usage text, and exit codes SHALL remain unchanged

### Requirement: Console writing depends on a focused interface

The package SHALL define `GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface` in `src/Console/ConsoleWriterInterface.php` with only `line(string $line): void` and `errorLine(string $line): void`. `Console\ConsoleWriter` SHALL implement it. Command execution, command helpers, `Initializer`, and `Synchronizer` SHALL accept that interface in their writing parameters instead of requiring the concrete writer. The application entrypoint SHALL accept the `Console` facade as specified below. Buffer getters SHALL remain on the concrete writer and SHALL NOT be required by the interface. This contract SHALL remain internal to composition and testing.

#### Scenario: Supplied writer without buffering

- **WHEN** a caller supplies an implementation of `ConsoleWriterInterface` with no `stdout()` or `stderr()` methods to a command or workflow that emits messages
- **THEN** execution SHALL send normal messages through `line()` and errors through `errorLine()` on the supplied instance
- **AND** the consumer SHALL NOT replace that instance or require buffer inspection

#### Scenario: Concrete writer remains compatible

- **WHEN** a caller constructs `Console\ConsoleWriter` with or without stdout/stderr stream mirrors
- **THEN** its existing constructor options, newline behavior, buffered contents, and `stdout()` and `stderr()` getters SHALL remain unchanged
- **AND** it SHALL satisfy the writing interface without requiring attached streams

#### Scenario: Per-invocation application output

- **WHEN** an application runs with a supplied `Console` facade
- **THEN** it SHALL pass that exact facade to commands through the writing interface
- **AND** caught errors SHALL use the same facade and its injected writer
- **AND** existing CLI messages, usage diagnostics, and exit codes SHALL remain unchanged
- **AND** the application SHALL NOT construct, replace, reset, or cache the supplied console graph

#### Scenario: Console namespace and current scope

- **WHEN** the console-writing extension is applied
- **THEN** source, tests, and composition guidance SHALL use `Console\Console`, `Console\ConsoleWriter`, and `Console\ConsoleWriterInterface`
- **AND** `Cli\ConsoleWriter` SHALL be removed without a compatibility alias
- **AND** this change SHALL NOT introduce a reader interface, reader implementation, or unused reader dependency
- **AND** `Cli\Input` SHALL retain argv parsing responsibilities

### Requirement: Console facade injection at the executable boundary

The package SHALL define `GustavoPeixoto\PhpQaScope\Console\Console` in `src/Console/Console.php` as a facade implementing `ConsoleWriterInterface`. Its constructor SHALL require and retain a supplied writer through a readonly property, without constructing a fallback. Each writing method SHALL delegate once to the corresponding method on that writer with its unchanged argument. The facade SHALL NOT add buffers, buffer getters, formatting, or stream management. `Application::run()` SHALL have the signature `run(array $argv, Console $console, ?string $root = null): int`, requiring the concrete facade rather than the writing interface or stream parameters.

#### Scenario: Supplied writer delegation

- **WHEN** a facade receives a writer implementing only `line()` and `errorLine()` and either method is called
- **THEN** it SHALL forward the supplied string exactly once to the corresponding writer method
- **AND** it SHALL NOT add a newline or inspect buffered output
- **AND** the supplied writer SHALL remain authoritative

#### Scenario: Executable composes stream output

- **WHEN** `bin/php-qa-scope` successfully loads the Composer autoloader
- **THEN** it SHALL construct `Console` with `ConsoleWriter(STDOUT, STDERR)` and pass the facade to the application alongside argv
- **AND** the application SHALL NOT receive stdout/stderr resources as run arguments
- **AND** the existing CLI invocation, messages, and exit codes SHALL remain unchanged

#### Scenario: Missing autoload remains reportable

- **WHEN** the executable cannot find a Composer autoload file in its existing search paths
- **THEN** it SHALL retain the existing direct stderr diagnostic and exit code `2`
- **AND** that error path SHALL NOT require package console classes to be available

#### Scenario: Caller owns output lifetime

- **WHEN** callers run an application with separately composed consoles and writers
- **THEN** each invocation's output SHALL reach only its supplied writer
- **AND** neither console graph SHALL affect the other's buffered or streamed output
- **AND** explicitly reusing the same concrete writer across calls SHALL retain its accumulated buffers without an application reset

### Requirement: Conditional future console reading guidance

The durable PHP composition convention and this change's design SHALL explain that `Console` is the common access point for writing and eventual reading. Reading interfaces and implementations SHALL be introduced only when a concrete interactive operation requires them. The documented future composition SHALL use `ConsoleReaderInterface` for required reading operations, `ConsoleReader` as its implementation, and `Console` implementing both reading and writing interfaces with reader/writer collaborators injected through their interfaces and operations delegated to the corresponding collaborator. This change SHALL record that conditional design and SHALL NOT implement reading, add an empty reader interface, or define speculative reading methods. Argv parsing SHALL remain with `Cli\Input`.

#### Scenario: Current reading scope

- **WHEN** the application needs only the currently implemented console-writing operations
- **THEN** it SHALL retain the existing writing interface, writer, and facade
- **AND** no reader type or unused reader dependency SHALL be added
- **AND** documentation SHALL retain the proposed future reader composition

#### Scenario: Contributor consults future reading direction

- **WHEN** a contributor consults the composition guidance before introducing a required interactive reading operation
- **THEN** the guidance SHALL specify `ConsoleReaderInterface`, `ConsoleReader`, and `Console` implementing both reading and writing interfaces
- **AND** it SHALL specify reader/writer injection through their contracts and delegation to the appropriate collaborator
- **AND** it SHALL require reading methods to follow the concrete operation's needs rather than an empty or speculative contract

### Requirement: Service-reference names express responsibilities

Within `src/` and `tests/`, locals, properties, and parameters referring to the specified services SHALL use responsibility-based names: writing objects currently called `$output` SHALL become `$console`; `ScopeCalculator` references called `$scopes` or `$effectiveScope` SHALL become `$scopeCalculator`; and `BlockLocator` references called `$blocks` or `$managedBlock` SHALL become `$blockLocator`. PHPDoc, named argument callers, and reflection-based composition assertions SHALL migrate with those references. The revision SHALL preserve behavior and method names. The durable convention SHALL record the naming principle without requiring every variable to repeat its class name; change-specific substitution mappings SHALL remain in the design.

#### Scenario: Calculator and locator collaborators

- **WHEN** application factories or services construct, receive, store, or use the specified calculator and locator collaborators
- **THEN** those references SHALL be named `$scopeCalculator` and `$blockLocator`, respectively
- **AND** named argument callers and reflection-based sharing assertions SHALL use the corresponding new parameter/property names
- **AND** the same supplied and shared collaborator instances SHALL remain authoritative

#### Scenario: Console-writing references

- **WHEN** a command, writing workflow, or test refers to a `Console`, `ConsoleWriterInterface`, or `ConsoleWriter` instance currently named `$output`
- **THEN** the reference and its PHPDoc SHALL use `$console`
- **AND** command/workflow named callers and implementations SHALL remain consistent with the revised signatures
- **AND** writing messages, buffering, error handling, and exit codes SHALL remain unchanged

#### Scenario: Data and other clear references retain their names

- **WHEN** `$scopes` contains the calculated map, `$block` contains a `LocatedBlock`, or `$targets` refers to `TargetRegistry`
- **THEN** those names SHALL remain unchanged
- **AND** stdout/stderr buffer/resource names and clear injected or inspected writer names SHALL remain unchanged
- **AND** references outside the specified service-role substitutions SHALL NOT be renamed by a blanket text replacement

### Requirement: Typed tool identity

Internal PHP interfaces SHALL expose a string-backed tool enum with exactly three supported cases. Tool-selection parameters and native target identities SHALL use that enum. Its backing values SHALL remain the canonical external identifiers, and identity SHALL NOT construct native-tool collaborators.

#### Scenario: Supported identities

- **WHEN** a caller enumerates `GustavoPeixoto\PhpQaScope\Tool::cases()`
- **THEN** the cases SHALL be `Phpcs`, `Phpstan`, and `PhpCsFixer`, in that order
- **AND** their values SHALL be `phpcs`, `phpstan`, and `php-cs-fixer`, respectively

#### Scenario: Typed selection

- **WHEN** a caller resolves a native target, renderer, insertion locator, or managed scope using internal PHP interfaces
- **THEN** the selector SHALL accept the corresponding tool enum case
- **AND** a plain string SHALL NOT satisfy the selector's parameter type

### Requirement: Configuration identity boundary

Loaded and directly constructed PHP scope configurations SHALL reject unsupported tool keys and expose selected tools as enum cases in supplied key order. Associative maps and serialized YAML SHALL retain canonical string keys. Loading invalid YAML SHALL preserve existing configuration diagnostics.

#### Scenario: Selected tool order

- **WHEN** a valid configuration lists `php-cs-fixer` before `phpcs` and omits `phpstan`
- **THEN** its managed-tool list SHALL contain the PHP-CS-Fixer case followed by the PHPCS case
- **AND** it SHALL NOT add the omitted PHPStan case
- **AND** the configuration's associative scope map SHALL retain the two canonical string keys

#### Scenario: Unknown YAML tool

- **WHEN** the YAML tools map contains the key `unknown-tool`
- **THEN** loading SHALL fail with the diagnostic `tools: unknown key 'unknown-tool'.`
- **AND** the CLI SHALL report the existing configuration error with exit code `2`

#### Scenario: Unknown tool supplied directly

- **WHEN** a PHP caller constructs a scope configuration with an unsupported tool key
- **THEN** construction SHALL reject that key with a configuration validation error
- **AND** it SHALL NOT defer rejection to enum enumeration or leak an enum conversion error

#### Scenario: Canonical YAML output

- **WHEN** initialization creates configuration for supported discovered targets
- **THEN** YAML tool keys SHALL remain strings using the enum backing values
- **AND** no serialized enum object or case name SHALL appear in the configuration

### Requirement: Supplied native registry mappings

PHP callers SHALL be able to construct native registries from supplied mappings keyed by canonical tool values. Resolution SHALL use the supplied entry without substituting a built-in implementation. Missing registrations SHALL retain the existing registry-specific error behavior. Supplied target keys SHALL agree with their target identities.

#### Scenario: Custom implementation

- **WHEN** a caller supplies a custom renderer or insertion locator for a supported tool and selects that tool case
- **THEN** resolution SHALL return the supplied instance
- **AND** subsequent rendering or insertion SHALL use that instance

#### Scenario: Custom target definition

- **WHEN** a caller supplies a native target definition for the PHPStan case under the `phpstan` key
- **THEN** selecting PHPStan SHALL return that definition
- **AND** discovery SHALL use its supplied path

#### Scenario: Missing custom registration

- **WHEN** a caller supplies a registry containing only PHPCS and requests PHPStan
- **THEN** resolution SHALL fail using the existing registry-specific exception and canonical tool identifier
- **AND** it SHALL NOT resolve PHPStan from a default or another registry

#### Scenario: Inconsistent target identity

- **WHEN** a caller supplies a target whose enum identity disagrees with its map key
- **THEN** registry construction SHALL reject the inconsistent entry before discovery or file access

### Requirement: Explicit collaborator injection

Service constructors SHALL require their collaborators as non-null arguments and SHALL use the supplied instances. Constructors SHALL NOT create collaborator defaults or replace supplied collaborators. This contract SHALL NOT require factories for data-only objects or services already using explicit construction.

#### Scenario: Missing required collaborator

- **WHEN** a caller omits a required collaborator when constructing an affected service directly
- **THEN** PHP SHALL reject the call rather than silently create the dependency

#### Scenario: Supplied collaborator remains authoritative

- **WHEN** a caller supplies a custom renderer registry, insertion-locator registry, or scope calculator to a service
- **THEN** the service SHALL execute using that supplied collaborator
- **AND** it SHALL NOT substitute the corresponding built-in collaborator

### Requirement: Independent default construction

Affected services that lose implicit collaborator construction SHALL provide zero-argument `default()` factories that return fully usable instances. Native registry factories SHALL provide the existing three built-in registrations. Each factory call SHALL construct an independent graph without global instance caching.

#### Scenario: Standalone defaults

- **WHEN** a caller obtains a default scope calculator, native renderer, inspector, marker preparer, or initializer
- **THEN** the returned service SHALL be usable without additional dependency setup
- **AND** it SHALL use the same built-in behavior as the default application

#### Scenario: Independent native registries

- **WHEN** a caller invokes the same native registry's default factory twice
- **THEN** the returned registries SHALL be distinct objects with independently constructed entries
- **AND** a separately supplied custom registry SHALL NOT influence either default registry

#### Scenario: Default discovery order

- **WHEN** all three supported native configuration files are present and the default target registry discovers them
- **THEN** its result SHALL retain the order `phpcs`, `phpstan`, `php-cs-fixer`
- **AND** paths, marker formats, and indentation SHALL retain the existing definitions

### Requirement: Application-local composition

Default applications SHALL share collaborators within their own command graph and remain independent across separate constructions. Command registries SHALL receive already constructed commands. Initialization and synchronization within one application SHALL use the same target definitions, scope calculation, marker handling, and writer collaborators.

#### Scenario: Consistent initialization and synchronization

- **WHEN** the default application initializes and synchronizes native targets
- **THEN** preparation and synchronization SHALL operate through the shared application collaborators
- **AND** their behavior SHALL satisfy the existing initialization and synchronization contracts

#### Scenario: Independent applications and commands

- **WHEN** a caller constructs two applications with separately supplied command graphs
- **THEN** each application SHALL dispatch its own supplied commands
- **AND** execution of either application SHALL NOT replace or affect the other's collaborator registrations

#### Scenario: Fresh default application graphs

- **WHEN** a caller invokes the application's default factory twice
- **THEN** the application graphs SHALL be independently constructed
- **AND** no registry or collaborator SHALL be obtained from a process-global singleton cache

### Requirement: Parsed command names

Input parsing SHALL represent an absent command as an empty string and preserve supplied command names without checking their registration. It SHALL retain project-root resolution and extra-argument validation. The application SHALL forward the parsed command name to its command registry for selection and rejection of missing or unknown commands.

#### Scenario: Missing command normalizes to an empty string

- **WHEN** a PHP caller supplies an empty argument list or only the executable name, a usage text, and a valid project root to input parsing
- **THEN** parsing SHALL return an input whose command is an empty string and whose root is the supplied root
- **AND** parsing SHALL NOT throw a missing-command usage error

#### Scenario: Unknown name is retained for registry selection

- **WHEN** a PHP caller supplies the executable name followed by an unknown command, a usage text, and a valid project root to input parsing
- **THEN** parsing SHALL return an input containing that supplied command name
- **AND** command registration SHALL be checked when the application selects the command from its registry

### Requirement: Registry-derived command usage

Command registries SHALL expose usage text listing their registered command names in registration order. Missing-command, unknown-command, and extra-argument errors SHALL use the same registry-derived text. Input parsing SHALL accept the supplied usage text for extra arguments without depending on command registries. The default CLI usage text, error prefix, and exit code SHALL remain unchanged.

#### Scenario: Custom command list

- **WHEN** a caller supplies a command registry containing `sync` followed by `check` and requests its usage text
- **THEN** the usage text SHALL be `Usage: php-qa-scope <sync|check>`
- **AND** it SHALL NOT list an unregistered `init` command

#### Scenario: Unknown command uses registered names

- **WHEN** an application using that custom registry receives an unknown command with an otherwise valid argument count
- **THEN** it SHALL report `ERROR Usage: php-qa-scope <sync|check>` on its error output
- **AND** it SHALL exit with code `2`

#### Scenario: Missing command is rejected by the registry

- **WHEN** the same application receives no command
- **THEN** it SHALL select the empty command name through its registry and reject that name
- **AND** it SHALL report the same `ERROR Usage: php-qa-scope <sync|check>` text
- **AND** it SHALL exit with code `2`

#### Scenario: Extra arguments use registered names

- **WHEN** the same application receives extra arguments
- **THEN** it SHALL report the same `ERROR Usage: php-qa-scope <sync|check>` text
- **AND** it SHALL exit with code `2`
- **AND** it SHALL NOT dispatch a command

#### Scenario: Default usage stays compatible

- **WHEN** the default application receives an unknown command, no command, or extra arguments
- **THEN** it SHALL report `ERROR Usage: php-qa-scope <init|sync|check>`
- **AND** it SHALL exit with code `2`

#### Scenario: Extra-argument validation uses supplied text

- **WHEN** a PHP caller supplies usage text directly to input parsing and the argument list contains more than the executable name and one command
- **THEN** parsing SHALL reject the arguments using that exact supplied text
- **AND** it SHALL NOT substitute a built-in command list
