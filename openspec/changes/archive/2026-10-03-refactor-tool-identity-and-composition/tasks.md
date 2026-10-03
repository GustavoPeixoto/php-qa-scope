# Tasks

## 1. Typed tool identity and configuration boundary

- [x] 1.1 Read this change's proposal, design, and library-composition delta, both existing capability specs, and the applicable language, repository, workflow, PHPDoc, environment, Git, and artifact conventions before editing implementation files; verify that the implementation scope matches the accepted internal PHP interface break and unchanged CLI/YAML contracts.
- [x] 1.2 Add `src/Tool.php` with the specified namespace, three cases, backing values, order, and enum PHPDoc; verify the enum's internal contract with focused tool-identity coverage in the PHP test environment.
- [x] 1.3 Migrate tool-selection methods, `TargetFile::$tool`, native registry lookups, command/synchronizer loops, `ScopeConfig::tool()`, and `managedTools()` to enum identities while keeping canonical string map keys; update affected call sites and PHPDoc, and verify typed lookup and existing target/renderer tests with enum arguments.
- [x] 1.4 Replace `ScopeConfig::TOOLS`, validate YAML keys with `tryFrom()` after map/key-shape checks, and reject unsupported keys in directly constructed scope configurations; update `ScopeLoaderTest` and configuration tests to verify unchanged diagnostics, selected-tool ordering, omitted-tool behavior, and direct-construction rejection.
- [x] 1.5 Keep YAML generation and externally visible strings unchanged; verify `ScopeInitializerTest`, `ScopeSelectionTest`, and initialization configuration fixtures, and document internal enum identities in `conventions/php-composition.md` with names and backing values matching implementation.

## 2. Injectable native registries

- [x] 2.1 Make `TargetRegistry` accept supplied target mappings, reject key/identity mismatches, and move the existing built-in definitions into `default()` using enum identities; migrate callers and verify `TargetRegistryTest` for the existing discovery combinations/order, a custom target path, an inconsistent identity, and a missing registration.
- [x] 2.2 Normalize renderer and insertion-locator defaults to enum backing-value keys, keep readonly supplied mappings and independent factory calls, and preserve canonical missing-entry messages; verify custom subset registries, supplied-instance resolution, and isolation from default registries with focused registry tests.
- [x] 2.3 Document required registry construction and supplied mappings in `conventions/php-composition.md`; verify that canonical enum keys, supplied instances, and independent defaults match implementation without introducing a singleton accessor or mutation API.

## 3. Explicit constructors and default composition

- [x] 3.1 Require `PatternCompiler` in the scope calculator and the three native renderers, add their zero-argument `default()` factories, and adapt renderer-registry defaults; migrate relevant tests and verify `PatternCompilerTest`, `RendererTest`, scope calculations, and the supplied compiler contract.
- [x] 3.2 Remove nullable fallbacks and object parameter defaults from `TargetInspector`, `TargetInitializer`, and `Initializer`; add complete standalone factories while retaining existing parameter names where practical, and migrate direct callers to complete injection or factories. Verify standalone inspection, marker insertion, initialization, and supplied custom/failing collaborator behavior in the affected unit and integration tests.
- [x] 3.3 Rewire `Application::default()` around shared loader, scope calculator, target registry, marker locator, writer, inspector, synchronizer, and initializer instances; keep `CommandRegistry` indexing supplied commands and verify `CliTest`, `CommandIntegrationTest`, and initialization integrations, including separate application/custom command graph isolation.
- [x] 3.4 Complete internal composition guidance in `conventions/php-composition.md` for `default()` usage and explicit construction, and complete PHPDoc for changed parameters, returns, and factories; verify documented contracts against implemented signatures and keep README CLI/YAML examples unchanged.
- [x] 3.5 Audit the affected constructors and factories for object parameter defaults, nullable construction fallbacks, built-in registry creation in constructors, and process-global caches; verify that all supplied collaborators remain authoritative and that repeated native registry/default application construction is independent, adding focused coverage only where existing tests leave a contract unverified.

## 4. Registry-derived command usage

- [x] 4.1 Add documented `CommandRegistry::usage(): string` using `sprintf('Usage: php-qa-scope <%s>', implode('|', array_keys($this->commands)))`, and reuse it when rejecting missing or unknown command names; verify focused registry coverage for an empty command selector, supplied command subsets, and registration order, and review that formatting uses `sprintf` rather than concatenation.
- [x] 4.2 Change `Input::fromArgv()` to receive required usage text before the optional root argument, reject only `count($argv) > 2`, and return `new self($argv[1] ?? '', $resolvedRoot)` after the existing root-resolution logic; pass registry-derived usage from `Application::run()`, migrate other call sites, and register default commands in `init`, `sync`, `check` order. Extend `CliTest` and direct parsing coverage to verify that empty lists and executable-only lists produce an empty command, unknown names survive parsing, the registry rejects missing/unknown commands, and extra arguments are rejected before dispatch with identical custom/default usage messages and unchanged exit codes.
- [x] 4.3 Document `usage()` and `fromArgv()` responsibilities in `conventions/php-composition.md` and affected PHPDoc, including parsed names versus registry-validated commands; verify against implementation and ensure input parsing receives a string for extra-argument errors without depending on a command registry or keeping a hard-coded fallback list.

## 5. Integration and change verification

- [x] 5.1 Run the full unit/integration suite with `composer test` through the prescribed PHP environment; verify existing command outputs, exit codes, target order, partial-success handling, marker preparation, and file-write safety against the unchanged baseline capability scenarios.
- [x] 5.2 Run `composer sniffer-check`, `composer stan-check`, and `composer fixer-check -- --allow-risky=yes` through the PHP environment; verify success without changing the project's Fixer policy or adding package dependencies.
- [x] 5.3 Review the implementation diff for missed tool-string selectors, enum serialization, unconverted direct constructors, duplicated command-list strings, usage formatting/order drift, graph wiring drift, and unrelated changes; verify the proposal/design/spec/task parity and self-sufficiency, and run `openspec validate refactor-tool-identity-and-composition --strict` before handing the implementation off for review.

## 6. Consumer interface and documentation boundaries

- [x] 6.1 Remove the README's PHP API section, create the durable PHP composition convention, index it in `AGENTS.md`, and clarify CLI/YAML consumer boundaries in the repository convention.
- [x] 6.2 Reconcile proposal, design, spec, and tasks with the supported CLI/YAML interfaces and internal PHP classes; retain migration-specific details in the design and keep artifacts self-sufficient.
- [x] 6.3 Review the documentation diff and local links, confirm source and public CLI/YAML examples remain unchanged by the documentation revision, and run strict OpenSpec validation.

## 7. Responsibility-based internal service names

- [x] 7.1 Rename `Scope\EffectiveScope` and its PSR-4 file to `Scope\ScopeCalculator`; update declarations, imports, type references, factory wiring, and affected tests/PHPDoc while preserving `calculate()`, `default()`, injected compiler behavior, selected-tool ordering, and the `ToolScope` result map.
- [x] 7.2 Rename `Block\ManagedBlock` and its PSR-4 file to `Block\BlockLocator`; migrate its callers and PHPDoc, and rename `ManagedBlockTest` and its file to `BlockLocatorTest`. Verify existing marker-validation errors, offsets, line endings, and replacement behavior while keeping `LocatedBlock` and insertion-locator types unchanged.
- [x] 7.3 Rename `Cli\Output` and its PSR-4 file to `Cli\ConsoleWriter`; migrate command/application signatures, imports, construction, tests, and PHPDoc. Preserve constructor options, method and parameter names, buffer-only operation, optional stream mirrors, line endings, stdout/stderr contents, CLI messages, and exit codes.
- [x] 7.4 Update `conventions/php-composition.md` and audit final planning references for the three service names; keep old names only in explicit migration mappings or historical evidence. Verify that only the three production types and directly corresponding test types were renamed, without compatibility aliases, dependency changes, or changes to other models/helpers.
- [x] 7.5 Run the full unit/integration suite and PHPCS, PHPStan, and PHP-CS-Fixer through the prescribed PHP environment, using the existing Fixer override and any required temporary runtime overrides. Review the complete rename diff and CLI/YAML compatibility, check artifact parity and self-sufficiency, and run `openspec validate refactor-tool-identity-and-composition --strict`.

## 8. Console-writing abstraction and facade injection

- [x] 8.1 Move `Cli\ConsoleWriter` and its PSR-4 file to `Console\ConsoleWriter` in `src/Console/ConsoleWriter.php`; migrate imports and construction in source/tests, remove the old file without an alias, and preserve constructor options, buffering, stream mirrors, newline behavior, and concrete buffer getters.
- [x] 8.2 Add documented `Console\ConsoleWriterInterface` in `src/Console/ConsoleWriterInterface.php` with only `line(string $line): void` and `errorLine(string $line): void`; make the concrete writer implement it. Migrate `Command::execute()`, command implementations/helpers, `Initializer`, `Synchronizer`, and test command implementations to the interface, updating PHPDoc while retaining their existing parameter names.
- [x] 8.3 Add documented `Console\Console` in `src/Console/Console.php`, implementing the writing interface with a required readonly writer collaborator and exact delegation. Change `Application::run()` to `run(array $argv, Console $console, ?string $root = null): int`, remove stream parameters/internal writer construction, and use the supplied facade for dispatch and caught errors. Compose `new Console(new ConsoleWriter(STDOUT, STDERR))` in `bin/php-qa-scope` after autoloading; migrate all run callers/tests, preserve the existing autoload search and direct missing-autoload diagnostic, and introduce no reader abstractions or default factory fallbacks.
- [x] 8.4 Add meaningful delegation and substitution coverage using a recording writer implementing only the two writing methods; exercise real command/workflow output and application caught errors through a supplied facade. Verify exact forwarding without extra newlines, supplied facade identity at dispatch, independent console graphs, retained buffers on explicit writer reuse, existing buffer/stream behavior, executable/CLI messages, usage diagnostics, exit codes, and missing-autoload behavior. Reuse existing coverage where it already verifies these contracts.
- [x] 8.5 Update `conventions/php-composition.md` with the final console namespace, writing interface, facade delegation, concrete buffering, executable stream composition, application facade injection, and deferred reading support. Audit source/tests/conventions for stale `Cli\ConsoleWriter` references, outdated run signatures/calls, and concrete writer requirements in writing consumers; retain historical migration mappings in this change's artifacts and keep README consumer documentation unchanged.
- [x] 8.6 Run the full unit/integration suite and PHPCS, PHPStan, and PHP-CS-Fixer through the prescribed PHP environment with the existing Fixer override and any required temporary runtime overrides. Review the console facade/interface/namespace and executable changes, unchanged CLI/YAML behavior, artifact parity and self-sufficiency, run strict OpenSpec validation and the whitespace diff check, and record verification evidence for this extension separately from the completed rename evidence.

## 9. Deferred reading guidance and service-reference names

- [x] 9.1 Update `conventions/php-composition.md` to explain `Console` as the common writing/eventual-reading access point. Document that actual reading needs trigger `ConsoleReaderInterface`, `ConsoleReader`, and a facade implementing both interfaces with injected collaborators and delegation; add no reader code or speculative methods. Record responsibility-based reference naming without requiring class-identical variable names, keeping change-specific migration mappings in the design and consumer README content unchanged.
- [x] 9.2 Rename `ScopeCalculator` locals/properties/parameters called `$scopes` or `$effectiveScope` to `$scopeCalculator`, and `BlockLocator` references called `$blocks` or `$managedBlock` to `$blockLocator` throughout source and tests. Update promoted properties, factories, uses, PHPDoc, corresponding named arguments, and reflection-based composition assertions together. Preserve scope-map `$scopes`, result `$block`, registry `$targets`, unrelated references, method names, and collaborator sharing.
- [x] 9.3 Rename `$output` references identifying `Console`, `ConsoleWriterInterface`, or `ConsoleWriter` to `$console` across source and tests, including command/workflow parameters, helpers, local references, PHPDoc, implementations, and any corresponding named callers. Preserve stdout/stderr buffers/resources, clear injected/inspected writer names, messages, interface methods, and runtime behavior.
- [x] 9.4 Review the type-directed naming diff and documentation against decisions 9–10, audit stale service-reference names, named callers, PHPDoc, and reflection-based assertions, and run existing affected unit/integration coverage plus the full suite and PHP QA through the prescribed environment. Use the existing Fixer override and temporary runtime overrides if needed, verify unchanged CLI/YAML behavior and no reader implementation, check artifact parity/self-sufficiency and whitespace, run strict OpenSpec validation, and record new evidence separately from the completed console stage.

## Implementation status

Tasks 1.1–9.4 are completed. The implemented console stage includes a writing interface, concrete buffered writer, and facade constructed by the executable and required by `Application::run()`. The composition convention now records the conditional future reader design and responsibility-based reference naming; source and tests use the specified collaborator names. Reader implementation and unrelated naming changes remain outside this change. Earlier evidence is historical; the final naming/guidance verification appears below.

## Verification of completed work before service renames

The evidence below covers the implementation and documentation-boundary revision before the service renames. The final results for tasks 7.1–7.5 appear under Verification after service renames.



- The full suite passed with 103 tests and 650 assertions.
- PHPCS, PHP-CS-Fixer with the required risky-rule override, and PHPStan passed.
- PHPStan required temporary CLI runtime overrides to enable argument registration, disable Xdebug, and prevent its runtime restart from discarding those overrides. Its complete analysis finished with `[OK] No errors`; package dependencies and repository QA configuration were unchanged.
- The implementation and artifact review passed, and strict OpenSpec validation succeeded.
- The documentation boundary revision passed local-link review (16 links), preserved all README content outside the removed PHP API section, and made no source or test changes. The indexed composition convention and change artifacts consistently identify CLI/YAML as supported consumer interfaces and PHP classes as internal implementation details.

## Verification after service renames

- The full Composer test suite passed with 103 tests and 650 assertions after all three renames.
- PHPCS, PHP-CS-Fixer with `--allow-risky=yes`, and PHPStan passed; the complete PHPStan analysis ended with `[OK] No errors`. Temporary CLI runtime overrides preserved argument registration and disabled Xdebug/runtime restarts without changing package dependencies or QA configuration.
- The 24 changed PHP files matched the original staged contents after applying only the planned class/test-name replacements and import ordering. Methods, parameter names, logic, other production type names, and CLI/YAML examples were unchanged.
- The three old production files and the old block-locator test file were removed. Final source, tests, and conventions contain no stale type references or compatibility aliases; historical migration mappings remain in these change artifacts.
- Strict OpenSpec validation and the whitespace diff check passed.

## Verification after console facade injection

- The full Composer unit/integration suite passed with 109 tests and 690 assertions. Six new console tests cover unchanged delegation, mirrored buffers, real check/sync/init execution with a writer lacking buffer getters, supplied facade identity and caught errors, isolated output graphs and explicit buffer reuse, and the executable's missing-autoload path.
- PHPCS and PHP-CS-Fixer with `--allow-risky=yes` passed. PHPStan's complete analysis of source and tests finished with `[OK] No errors` through `php vendor/bin/phpstan analyse --debug --no-progress` in the PHP service. The Composer static-analysis script was also invoked, but its silent exit was not treated as proof of analysis.
- Temporary CLI runtime overrides enabled argument registration and disabled Xdebug/runtime restart interference during QA. The temporary ini file was removed afterward; package dependencies and repository QA configuration were unchanged.
- The writer's implementation matches the pre-extension version exactly after only the namespace and implemented-interface changes. All six writing consumer files preserve their behavior, with only interface types, imports and related PHPDoc changed. Application and executable changes match the planned facade composition; all run callers were migrated, and consumer CLI/YAML behavior remains covered by existing integration tests.
- Source, tests and conventions contain no stale `Cli\ConsoleWriter` references. The previous file was removed without an alias, the writing interface has only its two methods, and no reader abstractions were introduced. The composition convention and change artifacts agree on concrete facade injection and writing-interface consumers.
- Strict OpenSpec validation, artifact parity/self-sufficiency review and the whitespace diff check passed. Existing staged changes were preserved; no commit, spec synchronization or archive was performed.

## Verification after reading guidance and reference-name revision

- The complete PHPUnit suite passed with 109 tests and 690 assertions, including existing unit/integration coverage for named construction, shared application graphs, reflection-based property assertions, and all CLI workflows. The Composer test script was invoked; its silent exit was not treated as evidence, and the complete suite was verified through `php vendor/bin/phpunit` in the PHP service.
- PHPCS and PHP-CS-Fixer with `--allow-risky=yes` passed. Complete PHPStan analysis through `php vendor/bin/phpstan analyse --debug --no-progress` ended with `[OK] No errors`. Temporary CLI overrides enabled argument registration and disabled Xdebug/runtime restart interference; the temporary ini file was removed after verification without changing permanent QA configuration or dependencies.
- The 18 changed PHP files matched the pre-revision baseline after only the specified reference/PHPDoc/named-argument/reflection substitutions and line wrapping. Scope maps retain `$scopes`, located results retain `$block`, registries retain `$targets`, and buffer/resource and injected writer names remain unchanged. README and the executable were unchanged by this revision.
- Source and tests contain no stale calculator/locator collaborator names, `$output` writing references, or corresponding old named arguments. Shared object graphs and consumer CLI/YAML behavior remain covered by the unchanged tests; no reader implementation or speculative reading methods were added.
- The indexed PHP composition convention describes the common console access point, reading only when required, the future reading interface/implementation with both contracts on the facade, constructor injection/delegation, and naming by responsibility. Change-specific mappings remain in the design. Artifact parity/self-sufficiency review, strict OpenSpec validation, and the whitespace diff check passed; existing staging was preserved.
