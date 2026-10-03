# Spec Delta

## Purpose

Help package consumers establish the scope YAML and managed native configuration blocks with one command, while requiring manual review of the initial QA setup.

## ADDED Requirements

### Requirement: Root configuration discovery
The `init` command SHALL discover only the exact native filenames `phpcs.xml`, `phpstan.neon`, and `php-cs-fixer.dist.php` in the project root, mapping them to `phpcs`, `phpstan`, and `php-cs-fixer` respectively. It SHALL fail with exit code `2` before writing files when none of these native files exists.

#### Scenario: Supported files found in the root
- **WHEN** the root contains `phpcs.xml` and `phpstan.neon` but not `php-cs-fixer.dist.php`
- **THEN** discovery SHALL identify `phpcs` and `phpstan`
- **AND** it SHALL NOT identify `php-cs-fixer`

#### Scenario: No supported root file
- **WHEN** the root contains no supported native filename, including when only alternate filenames or configurations in subdirectories exist
- **THEN** `init` SHALL report an error and exit with code `2`
- **AND** it SHALL NOT create the YAML or modify any native file

### Requirement: Default scope YAML creation
When `php-qa-scope.yml` is absent, `init` SHALL create it with global `include` containing only `src`, global `exclude` empty, and a `tools` map containing exactly the discovered tool keys. Each tool SHALL contain empty `include` and `exclude` arrays. The command SHALL NOT infer paths or exclusions from existing native scope settings.

#### Scenario: All supported tools discovered
- **WHEN** the YAML is absent and all three supported native files exist
- **THEN** the new YAML SHALL contain global `include: [src]` and `exclude: []`
- **AND** `tools` SHALL contain `phpcs`, `phpstan`, and `php-cs-fixer`, each with empty local arrays

#### Scenario: One supported tool discovered
- **WHEN** only `phpstan.neon` exists and the YAML is absent
- **THEN** the new YAML SHALL list only `phpstan` under `tools`

#### Scenario: Source directory does not exist yet
- **WHEN** a supported native file exists but the project does not yet contain a `src` directory
- **THEN** the generated global include SHALL still contain only `src`
- **AND** YAML creation SHALL NOT depend on physical existence of included paths

### Requirement: Existing scope YAML preservation
When the scope YAML already exists, `init` SHALL preserve its bytes, validate it using the existing scope schema, and prepare only its listed tools using their effective scopes. It SHALL NOT add discovered tools to existing YAML. A YAML read, validation, or creation failure SHALL stop initialization before native-file writes.

#### Scenario: Existing YAML selects a subset
- **WHEN** all supported native files exist but valid existing YAML lists only `phpstan` with a custom scope
- **THEN** `init` SHALL leave the YAML, PHPCS, and PHP-CS-Fixer files unchanged
- **AND** it SHALL initialize and synchronize PHPStan using that custom effective scope

#### Scenario: Invalid existing YAML
- **WHEN** existing YAML cannot be read or fails parsing or schema validation
- **THEN** `init` SHALL report an error and exit with code `2` before preparing any native file
- **AND** it SHALL leave the YAML unchanged

#### Scenario: YAML creation fails
- **WHEN** the default YAML cannot be created safely
- **THEN** `init` SHALL report an error and exit with code `2`
- **AND** it SHALL NOT write any native target

### Requirement: Empty marker preparation
For each listed target, `init` SHALL insert an empty managed marker pair only when neither marker is present. It SHALL validate an existing pair without inserting another pair. A missing single marker, duplicated marker, reversed pair, malformed syntax, or invalid indentation SHALL produce a target error and leave that file unchanged during preparation. Empty pairs SHALL be persisted before the synchronization phase fills them.

#### Scenario: Both markers absent
- **WHEN** a managed target has neither marker and a supported insertion location exists
- **THEN** preparation SHALL add exactly one start marker and one end marker with no managed configuration content between them
- **AND** the pair SHALL use the target's existing supported syntax and required indentation

#### Scenario: Existing valid pair
- **WHEN** a target already contains exactly one valid pair
- **THEN** preparation SHALL preserve that target's bytes
- **AND** the target SHALL remain eligible for the subsequent synchronization phase

#### Scenario: Invalid marker state
- **WHEN** a target has an incomplete, duplicated, reversed, malformed, or invalidly indented pair
- **THEN** `init` SHALL report `ERROR <target>: <reason>` and leave the target unchanged
- **AND** it SHALL continue preparing later targets

### Requirement: PHPCS insertion location
For a supported conventional XML configuration, `init` SHALL insert the empty marker pair immediately inside the first actual non-self-closing `ruleset` opening element. Markers SHALL use XML comments with four spaces of indentation. The command SHALL preserve existing XML elements outside the inserted block.

#### Scenario: Ruleset with attributes and existing settings
- **WHEN** `phpcs.xml` contains a recognizable `ruleset` opening element with attributes and existing file or rule elements
- **THEN** the new pair SHALL appear after that opening element and before its existing contents
- **AND** the existing elements SHALL remain unchanged

#### Scenario: Tag-like text in a comment
- **WHEN** an XML comment contains `<ruleset>` before the actual opening element
- **THEN** initialization SHALL NOT insert the pair inside that comment

#### Scenario: Unsupported ruleset location
- **WHEN** a supported non-self-closing `ruleset` opening element cannot be recognized safely
- **THEN** `init` SHALL leave `phpcs.xml` unchanged and report a target error directing the consumer to manual marker placement

### Requirement: PHPStan insertion location
For a supported conventional NEON configuration, `init` SHALL insert the empty pair immediately under the top-level block-form `parameters:` declaration using `#` comments with four spaces of indentation. It SHALL preserve existing parameters and SHALL NOT create a new `parameters` section when the insertion location is absent or unsupported.

#### Scenario: Existing parameters block
- **WHEN** `phpstan.neon` contains a recognizable top-level block-form `parameters:` declaration
- **THEN** the pair SHALL appear inside that section before its existing parameters
- **AND** existing paths, excludes, levels, and other settings SHALL remain unchanged

#### Scenario: Parameters declaration cannot be used
- **WHEN** the file has no top-level parameters block or uses an unsupported inline, nested, or ambiguous layout
- **THEN** `init` SHALL leave the target unchanged and report a target error with manual placement guidance

### Requirement: PHP-CS-Fixer insertion location
For a supported conventional PHP configuration, `init` SHALL insert the empty pair near the beginning of the PHP code after the opening tag and any required initial declarations, including `declare(strict_types=1)`. Markers SHALL use unindented `//` comments. Initialization SHALL NOT execute the configuration, remove old Finder code, or connect the generated `$finder` to the returned configuration.

#### Scenario: Conventional unnamespaced PHP file
- **WHEN** `php-cs-fixer.dist.php` starts with a PHP opening tag and has a recognizable top-level insertion location
- **THEN** the pair SHALL appear before the file's existing executable configuration code
- **AND** the existing configuration and Finder assignments SHALL remain unchanged

#### Scenario: Strict types declaration
- **WHEN** the file begins with `declare(strict_types=1)` after the opening tag and optional comments or whitespace
- **THEN** the pair SHALL be inserted after that declaration
- **AND** synchronization SHALL NOT place the generated `$finder` assignment before the declaration

#### Scenario: Unsupported PHP layout
- **WHEN** a safe insertion location cannot be established, including an unsupported namespace or mixed PHP and non-PHP layout
- **THEN** `init` SHALL leave that target unchanged and report a target error with manual placement guidance

### Requirement: Synchronization within initialization
After preparing markers, `init` SHALL invoke the existing synchronization workflow once in the same command execution, using the effective YAML scopes. The synchronization phase SHALL process targets that completed preparation, including targets with pre-existing valid markers, and SHALL NOT retry targets whose preparation already failed. The command SHALL return code `2` if preparation or synchronization has any target error, otherwise code `0`; it SHALL NOT use code `1` for initialization.

#### Scenario: Fresh initialization completes
- **WHEN** supported configurations have no markers and their marker preparation and synchronization succeed
- **THEN** one execution of `init` SHALL leave their managed blocks filled with the content produced by the existing renderers
- **AND** the consumer SHALL NOT need to run a separate `sync` command to fill those blocks
- **AND** `init` SHALL exit with code `0`

#### Scenario: Existing divergent block
- **WHEN** existing YAML is valid and a target already has a valid but divergent managed block
- **THEN** preparation SHALL NOT add markers
- **AND** the synchronization phase SHALL update that block using the existing `sync` behavior

#### Scenario: PHP-CS-Fixer block filled by synchronization
- **WHEN** PHP-CS-Fixer marker preparation succeeds
- **THEN** synchronization SHALL generate the existing `$finder` code within the pair
- **AND** initialization SHALL NOT add a `setFinder()` call outside the block

#### Scenario: Preparation failure followed by a valid target
- **WHEN** one target cannot be prepared and a later target can be prepared and synchronized
- **THEN** `init` SHALL report the first target's error and still synchronize the later target
- **AND** it SHALL exit with code `2` while retaining successful writes

#### Scenario: Synchronization fails after markers were inserted
- **WHEN** the empty pair was written but that target's synchronization fails
- **THEN** `init` SHALL report the target error and preserve completed preparation writes
- **AND** later targets SHALL still be processed
- **AND** the consumer SHALL be able to retry after fixing the reported problem

#### Scenario: Repeated successful initialization
- **WHEN** `init` is repeated with valid unchanged YAML and already synchronized managed targets
- **THEN** it SHALL NOT rewrite YAML, add duplicate markers, or rewrite native files
- **AND** it SHALL return code `0`

### Requirement: Initialization write safety
Initialization SHALL preserve original bytes outside insertion and managed replacement regions, use the target's existing line endings for inserted content, preserve native file permissions, reject symbolic links, detect concurrent changes before replacing native files, and clean up temporary replacement files after failure. YAML creation SHALL NOT overwrite a file that appears after the absence check.

#### Scenario: CRLF and permissions preserved
- **WHEN** initialization inserts and fills a pair in a target that uses CRLF line endings and a particular permission mode
- **THEN** inserted and rendered lines SHALL use CRLF
- **AND** original bytes outside the added or replaced block and the permission mode SHALL remain unchanged

#### Scenario: Native target changes concurrently
- **WHEN** a target changes after inspection and before a preparation or synchronization replacement
- **THEN** initialization SHALL NOT overwrite the concurrent content
- **AND** it SHALL report a target error, clean up its temporary file, and continue with later targets

#### Scenario: Symbolic link encountered
- **WHEN** the scope YAML is a symbolic link or a listed native target is a symbolic link
- **THEN** initialization SHALL NOT write through or replace that link
- **AND** a YAML link SHALL cause a command-wide error, while a native link SHALL cause a target-local error

#### Scenario: Scope YAML appears concurrently
- **WHEN** another process creates `php-qa-scope.yml` after initialization found it absent but before creation commits
- **THEN** initialization SHALL NOT overwrite that YAML
- **AND** it SHALL report a command-wide error before native-file writes

### Requirement: Consumer review warning
Whenever marker preparation or synchronization changes at least one native QA file, `init` SHALL emit the following three-line warning exactly once at the end of processing, on standard error, even if another target failed. The warning SHALL NOT change the command's exit code by itself:

```plaintext
WARNING: QA configuration files were modified.
Review the changes and complete any required manual setup before running your QA tools.
Setup instructions: https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks
```

#### Scenario: Native files changed
- **WHEN** any managed native file changes during `init`
- **THEN** the final warning SHALL contain the exact text and documentation URL above
- **AND** normal synchronization statuses SHALL remain on standard output

#### Scenario: Partial success changed a file
- **WHEN** one native file was changed and a later target failed
- **THEN** the warning SHALL still be emitted after target results
- **AND** the command SHALL exit with code `2`

#### Scenario: YAML created but native files already synchronized
- **WHEN** the YAML is created but all native targets already have matching managed blocks
- **THEN** the native-file warning SHALL NOT be emitted

#### Scenario: No-op retry
- **WHEN** neither preparation nor synchronization changes a native file
- **THEN** the native-file warning SHALL NOT be emitted

### Requirement: Public initialization guidance
The public README SHALL document `init` usage and its automatic synchronization, the default YAML, preservation of existing YAML, supported insertion locations, local failures, retries, and the consumer's manual review responsibilities. The `Managed Blocks` section SHALL remain accessible through the `#managed-blocks` repository anchor used by the warning.

#### Scenario: Consumer follows the warning link
- **WHEN** a consumer opens the warning's documentation link
- **THEN** the linked section SHALL explain how to reconcile old PHPCS scope elements, duplicated PHPStan paths or excludes, and existing PHP-CS-Fixer Finder definitions
- **AND** it SHALL explain connecting `$finder` with `setFinder()` and manually placing markers in unsupported layouts
- **AND** it SHALL state that successful synchronization does not prove that the QA tools' native configurations are ready to execute
