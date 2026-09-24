## Purpose

Synchronizes managed file-scope blocks for supported PHP QA tools from one project-level YAML configuration while preserving each tool's native policy configuration outside those blocks.

## ADDED Requirements

### Requirement: Scope configuration loading
The system SHALL load `php-qa-scope.yml` from the project root and validate the scope configuration before checking or synchronizing any native tool configuration.

#### Scenario: Valid scope configuration
- **WHEN** `php-qa-scope.yml` contains global `include`, global `exclude`, and a `tools` map with accepted tool keys
- **THEN** the system SHALL continue with only the tools listed in `tools`

#### Scenario: Unknown tool key
- **WHEN** `php-qa-scope.yml` contains a tool key other than `phpcs`, `phpstan`, or `php-cs-fixer`
- **THEN** the command SHALL fail with exit code `2`

#### Scenario: Missing listed tool arrays
- **WHEN** a listed tool omits either `include` or `exclude`
- **THEN** the command SHALL fail with exit code `2`

#### Scenario: Command-wide scope failure
- **WHEN** invalid YAML, an invalid scope schema, or an unsupported scope pattern prevents the managed tools or their effective scopes from being determined
- **THEN** the command SHALL exit with code `2` before inspecting or writing any native target

### Requirement: Managed tool selection
The system SHALL treat the `tools` map as the explicit declaration of which supported tools are managed for a project.

#### Scenario: Tool key is present
- **WHEN** a supported tool key is present in `tools`
- **THEN** the system SHALL check or synchronize that tool's native configuration target

#### Scenario: Tool key is absent
- **WHEN** a supported tool key is absent from `tools`
- **THEN** the system SHALL skip that tool without reading, rendering, reporting, or modifying that tool's native configuration target

### Requirement: Effective scope calculation
For each managed tool, the system SHALL compute the effective scope as global includes plus tool-specific includes, minus global excludes plus tool-specific excludes.

#### Scenario: Tool-specific includes add paths
- **WHEN** global `include` contains `src` and `tools.phpstan.include` contains `tests`
- **THEN** the effective PHPStan include set SHALL contain both `src` and `tests`

#### Scenario: Excludes win
- **WHEN** an included path also matches a global or tool-specific exclude
- **THEN** the generated managed block SHALL prevent that path from being selected, with no re-inclusion

#### Scenario: Subtree exclude is relative to the project root
- **WHEN** both `src` and `tests` are included and `src/Foo/**` is excluded
- **THEN** the generated configurations SHALL exclude descendants of `src/Foo` while leaving descendants of `tests/Foo` selectable

### Requirement: Hidden-path discovery
For directory includes, the system SHALL render tool configurations whose recursive `.php` discovery skips files and directories with a path segment beginning with `.`. An explicit include of a hidden `.php` file or hidden directory SHALL remain selectable, subject to configured excludes. The system SHALL document that tool-native hidden-path behavior may require a compatibility exclusion in a generated managed block even when YAML `exclude` is empty.

#### Scenario: Hidden file found during recursion
- **WHEN** `src` is included and `src/.hidden.php` is not separately included
- **THEN** the generated configurations SHALL leave that file out of recursive discovery for PHPCS, PHPStan, and PHP-CS-Fixer

#### Scenario: Hidden descendant directory found during recursion
- **WHEN** `src` is included and `src/.internal/Visible.php` exists without a separate include for `src/.internal`
- **THEN** the generated configurations SHALL leave that file out of recursive discovery for all three tools, including PHPCS

#### Scenario: Explicit hidden path
- **WHEN** a hidden `.php` file or hidden directory is explicitly included
- **THEN** the generated configurations SHALL select the explicit file or recursively discover `.php` files beneath the explicit directory, except for its hidden descendants and paths matched by configured excludes

#### Scenario: Configured exclude overrides explicit include
- **WHEN** an explicitly included hidden path also matches a global or tool-specific exclude
- **THEN** the generated configurations SHALL exclude that path

### Requirement: Supported exclude pattern language
The system SHALL accept only the documented portable exclude pattern forms and SHALL reject unsupported glob features.

#### Scenario: Supported exclude patterns
- **WHEN** excludes use a specific file, specific subtree, recurring directory, recurring directory under a root, or file suffix pattern
- **THEN** the system SHALL render equivalent exclusions for each managed tool

#### Scenario: Unsupported exclude pattern
- **WHEN** an exclude uses unsupported syntax such as single-segment wildcards, character classes, brace alternatives, negation, or regular expressions
- **THEN** the command SHALL fail with exit code `2`

### Requirement: Native target mapping
The system SHALL map each managed tool to its native configuration file and marker syntax.

#### Scenario: PHP_CodeSniffer target
- **WHEN** `phpcs` is listed in `tools`
- **THEN** the system SHALL target `phpcs.xml` and XML comment markers

#### Scenario: PHPStan target
- **WHEN** `phpstan` is listed in `tools`
- **THEN** the system SHALL target `phpstan.neon` and `#` comment markers

#### Scenario: PHP-CS-Fixer target
- **WHEN** `php-cs-fixer` is listed in `tools`
- **THEN** the system SHALL target `php-cs-fixer.dist.php` and `//` comment markers

### Requirement: Managed block validation
For each managed target, the system SHALL require exactly one valid start marker and one valid end marker, in the required syntax, order, and indentation, before reporting a valid status or writing that target. Validation of one target SHALL be independent of other native targets.

#### Scenario: Missing native configuration file
- **WHEN** a tool is listed in `tools` and its native configuration file does not exist
- **THEN** the command SHALL report `ERROR <target>: <reason>` for that target, continue with later managed targets, and exit with code `2` after visiting them

#### Scenario: Missing or duplicated marker
- **WHEN** a managed target has missing or duplicated `php-qa-scope:start` or `php-qa-scope:end` markers
- **THEN** the command SHALL report an error for that target, leave it unchanged, continue with later managed targets, and exit with code `2`

#### Scenario: Reversed or malformed marker block
- **WHEN** a managed target has reversed, incomplete, or malformed markers
- **THEN** the command SHALL report an error for that target, leave it unchanged, continue with later managed targets, and exit with code `2`

### Requirement: Check command
The `check` command SHALL inspect every managed target independently, validate its markers completely, and report `OK`, `OUT-OF-SYNC`, or `ERROR <target>: <reason>` for each target. It SHALL determine status without writing native files or constructing a complete replacement file.

#### Scenario: All managed targets are synchronized
- **WHEN** every managed target already contains the expected managed block
- **THEN** `check` SHALL report `OK` for each managed target and exit with code `0`

#### Scenario: At least one managed target differs
- **WHEN** a valid managed target's block differs from the expected managed block and no target fails
- **THEN** `check` SHALL report `OUT-OF-SYNC` for the differing target and exit with code `1`

#### Scenario: Invalid first target followed by a divergent target
- **WHEN** the first managed target has invalid markers and a later managed target is valid but divergent
- **THEN** `check` SHALL report `ERROR` for the first target and `OUT-OF-SYNC` for the later target, leave both files unchanged, and exit with code `2`

#### Scenario: Invalid later target after a synchronized target
- **WHEN** an earlier managed target is synchronized and a later managed target fails validation
- **THEN** `check` SHALL report `OK` for the earlier target and `ERROR` for the later target and exit with code `2`

### Requirement: Sync command
The `sync` command SHALL inspect and process managed targets one at a time. It SHALL update only the managed block content of each valid divergent target, report that target's result, and continue after a target-local error. A completed update SHALL remain in place if another target fails.

#### Scenario: Managed target requires update
- **WHEN** a managed target's block differs from the expected managed block
- **THEN** `sync` SHALL validate that target, replace only that block's content, report `UPDATED` for the target, and exit with code `0` if no target fails

#### Scenario: Managed target already synchronized
- **WHEN** a managed target already contains the expected managed block
- **THEN** `sync` SHALL leave that target unchanged without rewriting it and report `OK`

#### Scenario: Content outside managed block
- **WHEN** `sync` updates a managed block
- **THEN** all content outside that managed block SHALL remain byte-for-byte unchanged

#### Scenario: Invalid first target followed by a divergent target
- **WHEN** the first managed target is invalid and a later managed target is valid but divergent
- **THEN** `sync` SHALL report `ERROR` for the first target, leave it unchanged, update and report `UPDATED` for the later target, and exit with code `2`

#### Scenario: Invalid later target after an update
- **WHEN** an earlier managed target is valid but divergent and a later managed target is invalid
- **THEN** `sync` SHALL update and report `UPDATED` for the earlier target, report `ERROR` for the later target, leave the later target unchanged, and exit with code `2`

#### Scenario: Mixed target results
- **WHEN** one managed target fails, another is valid but divergent, and a third is synchronized
- **THEN** `sync` SHALL report `ERROR <target>: <reason>`, `UPDATED <target>`, and `OK <target>` for their respective targets and exit with code `2`

#### Scenario: Retry after partial success
- **WHEN** a later `sync` invocation runs after a target-local error is repaired and another target was updated during the earlier invocation
- **THEN** `sync` SHALL re-inspect every managed target, report `OK` for and avoid rewriting the previously updated target, and update only targets still divergent

### Requirement: Per-target write safety
For each updated target, the system SHALL preserve the target's line endings and file permissions, reject symbolic links, detect a change to the file between inspection and replacement, and clean up any temporary file left by a failed write.

#### Scenario: Concurrent native file change
- **WHEN** a target changes after inspection but before its replacement
- **THEN** `sync` SHALL report `ERROR` for that target, SHALL NOT replace its concurrent content, and SHALL continue with later managed targets

#### Scenario: Write preparation failure
- **WHEN** preparing a temporary replacement fails for a target
- **THEN** `sync` SHALL report `ERROR` for that target, leave its native file unchanged, clean up its temporary file, and continue with later managed targets

### Requirement: Rendered tool blocks
The system SHALL render native managed block content that represents the effective scope for each managed tool.

#### Scenario: PHP_CodeSniffer rendering
- **WHEN** PHPCS is managed
- **THEN** the rendered block SHALL use `<file>.</file>` as the common base for recursive directory selection, a `.php` extension setting, and root-relative PHPCS-compatible global `<exclude-pattern>` entries that enforce effective includes, configured excludes, and hidden-directory discovery behavior

#### Scenario: Explicit hidden PHP file in PHPCS
- **WHEN** an explicitly included `.php` file lies in a hidden path and no configured exclude matches it
- **THEN** the PHPCS block SHALL add that file as a direct `<file>` entry so it is selected despite PHPCS's recursive dotfile behavior

#### Scenario: Excluded explicit hidden PHP file in PHPCS
- **WHEN** an explicitly included `.php` file lies in a hidden path and a configured exclude matches it
- **THEN** the PHPCS block SHALL NOT add a direct `<file>` entry for that file

#### Scenario: PHPStan rendering
- **WHEN** PHPStan is managed
- **THEN** the rendered block SHALL express the effective include and exclude selection using PHPStan-compatible NEON entries

#### Scenario: PHP-CS-Fixer rendering
- **WHEN** PHP-CS-Fixer is managed
- **THEN** the rendered block SHALL express the effective include and exclude selection using PHP-CS-Fixer Finder-compatible PHP code

### Requirement: CLI errors and usage
The CLI SHALL provide deterministic exit codes for success, drift, and invalid usage or operational errors. After visiting all managed targets, target errors SHALL take precedence over drift: exit code `2` if any target failed, otherwise `1` for `check` if any target is out of sync, otherwise `0`.

#### Scenario: Invalid command
- **WHEN** the CLI receives any command other than `check` or `sync`
- **THEN** the command SHALL fail with exit code `2`

#### Scenario: Target-local rendering, read, or write failure
- **WHEN** rendering, reading, or writing one managed target fails
- **THEN** the command SHALL report `ERROR <target>: <reason>`, SHALL continue with later managed targets, and SHALL exit with code `2` after reporting their results

#### Scenario: Error and drift together
- **WHEN** `check` finds a target-local error and an out-of-sync valid target in the same invocation
- **THEN** `check` SHALL report both target results and exit with code `2`
