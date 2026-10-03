# Spec Delta

## MODIFIED Requirements

### Requirement: Managed block validation
For each managed target processed by `check` or `sync`, the system SHALL require exactly one valid start marker and one valid end marker, in the required syntax, order, and indentation, before reporting a valid status or writing that target. The marker-preparation phase of `init` SHALL be allowed to create an empty pair when both markers are absent, as defined by scope initialization; the subsequent synchronization phase SHALL use the same complete marker validation as `sync`. Validation of one target SHALL be independent of other native targets.

#### Scenario: Missing native configuration file
- **WHEN** a tool is listed in `tools` and its native configuration file does not exist
- **THEN** the command SHALL report `ERROR <target>: <reason>` for that target, continue with later managed targets, and exit with code `2` after visiting them

#### Scenario: Missing or duplicated marker
- **WHEN** `check` or `sync` encounters a managed target with missing or duplicated `php-qa-scope:start` or `php-qa-scope:end` markers
- **THEN** the command SHALL report an error for that target, leave it unchanged, continue with later managed targets, and exit with code `2`

#### Scenario: Reversed or malformed marker block
- **WHEN** a managed target has reversed, incomplete, or malformed markers
- **THEN** the command SHALL report an error for that target, leave it unchanged, continue with later managed targets, and exit with code `2`

#### Scenario: Initialization creates an absent pair
- **WHEN** `init` encounters a managed target with both markers absent and a supported insertion location
- **THEN** preparation SHALL be allowed to insert an empty pair
- **AND** the synchronization phase SHALL require exactly one valid pair before filling the block

### Requirement: CLI errors and usage
The CLI SHALL accept `init`, `check`, and `sync` and provide deterministic exit codes for success, drift, and invalid usage or operational errors. After visiting all managed targets, target errors SHALL take precedence over drift: exit code `2` if any target failed, otherwise `1` for `check` if any target is out of sync, otherwise `0`. Initialization-specific preparation, configuration creation, and warning behavior SHALL follow the scope-initialization requirements.

#### Scenario: Invalid command
- **WHEN** the CLI receives any command other than `init`, `check`, or `sync`
- **THEN** the command SHALL fail with exit code `2`

#### Scenario: Target-local rendering, read, or write failure
- **WHEN** rendering, reading, or writing one managed target fails
- **THEN** the command SHALL report `ERROR <target>: <reason>`, SHALL continue with later managed targets, and SHALL exit with code `2` after reporting results

#### Scenario: Error and drift together
- **WHEN** `check` finds a target-local error and an out-of-sync valid target in the same invocation
- **THEN** `check` SHALL report both target results and exit with code `2`

#### Scenario: Initialization dispatch
- **WHEN** the CLI receives exactly the `init` command without extra arguments
- **THEN** it SHALL execute scope initialization rather than reject the command

#### Scenario: Usage text lists all supported commands
- **WHEN** invalid usage produces a usage message
- **THEN** it SHALL include `init`, `sync`, and `check`
