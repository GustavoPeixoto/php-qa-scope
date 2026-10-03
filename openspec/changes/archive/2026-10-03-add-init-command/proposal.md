# Proposal

## Why

Consumers currently have to create `php-qa-scope.yml` and position every managed block manually before using the package. An `init` command can establish that starting point and synchronize the new blocks while keeping the consumer responsible for reviewing and completing the initial setup.

## What Changes

- Add `php-qa-scope init`, using the current working directory as the project root.
- When `php-qa-scope.yml` is absent, detect exactly `phpcs.xml`, `phpstan.neon`, and `php-cs-fixer.dist.php` in that root. Generate global `include: [src]`, global `exclude: []`, and only the detected tool keys, each with empty local `include` and `exclude` arrays. Fail with code `2` when none of these native files exists.
- Preserve an existing scope YAML and use its declared tools and effective scopes; initialization does not add tool keys to that file.
- For each managed target without either marker, insert an empty marker pair at a conventional location: inside the first PHPCS `ruleset`, inside PHPStan `parameters`, or near the beginning of the PHP-CS-Fixer PHP code after required initial declarations.
- Validate existing markers rather than adding a second pair. Unsupported insertion locations and invalid markers produce actionable target errors.
- After marker preparation, invoke the existing `sync` workflow in the same `init` execution to fill new blocks and synchronize existing valid blocks. PHP-CS-Fixer synchronization creates `$finder`; connecting it with `setFinder()` remains a manual setup responsibility.
- Preserve content outside the inserted or synchronized blocks. Do not remove or migrate existing native scope settings, Finder assignments, or other tool configuration.
- Whenever a native QA file changes during initialization, print a final review warning with the package repository URL and the `#managed-blocks` anchor, including after partial failure.
- Extend the public README with `init` usage, insertion locations, manual review instructions, and concrete examples of conflicting old settings.
- Extract the initialization workflow into `Initializer\Initializer`, keeping `InitCommand` responsible for the review warning and CLI exit code; aggregate initialization errors and native writes in `InitializerResult`.
- Organize package classes into `Scope`, `Block`, `Target`, `Initializer`, and `Synchronizer` namespaces; align initialization and synchronization result names with their workflows while preserving existing methods and behavior.

## Capabilities

### New Capabilities

- `scope-initialization`: Discover supported configurations, create a default scope YAML, prepare managed markers, invoke synchronization, and guide consumers through manual setup review.

### Modified Capabilities

- `managed-scope-sync`: Accept `init` as a CLI command and scope pre-existing marker requirements to synchronization and checking, allowing the initialization phase to create an absent pair while retaining strict validation of the resulting block.

## Impact

- Native insertion strategies and their interface live in `src/InsertionLocator/`, matching the organization of `src/Renderer/`; the PHPCS implementation is named `PhpCodeSnifferInsertionLocator`.
- CLI registration and usage text in `src/Application.php`, `src/Cli/Input.php`, and `src/Command/CommandRegistry.php`.
- A new initialization command and collaborators for YAML creation, marker insertion, and safe native-file replacement.
- A small extraction of the existing synchronization coordinator so `init` can reuse synchronization and learn which files changed without launching a subprocess or parsing CLI text.
- Reuse of `ScopeLoader`, `EffectiveScope`, `TargetRegistry`, `ManagedBlock`, and the existing renderers. No new runtime dependency is planned.
- CLI, insertion, integration, retry, write-safety, and regression tests using the existing temporary-project fixtures.
- `README.md`, new initialization requirements, and deltas to the existing managed-scope specification.

The inspected sources include the CLI and commands, scope loading and effective-scope calculation, native target definitions, marker validation, synchronization writing, renderers, nearby tests, the public README, and `openspec/specs/managed-scope-sync/spec.md`.

Out of scope: alternate configuration filenames, configuration discovery outside the root, automatic conversion of existing scope settings, automatic `setFinder()` wiring, executing QA tools, and claiming that native configurations are semantically valid after initialization.

Risks: old PHPStan keys may conflict with inserted keys; PHPCS may retain old scope declarations; a later Finder assignment may override the generated `$finder`. These are intentional manual-review responsibilities, described by the warning and linked documentation. Unsupported layouts fail locally, and successful writes remain after a later target fails.

## Open Questions

No blocking open questions remain. Proposed defaults for review are to preserve existing YAML, manage only its listed tools, return code `2` after any target error, and print the review warning on standard error only when a native file actually changed. The detailed design and scenarios make these defaults explicit.
