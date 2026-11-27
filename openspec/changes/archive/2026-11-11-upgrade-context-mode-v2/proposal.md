# Proposal

## Why

The development environment needs context-mode 2.1.8 and its official Codex setup. The upgrade accumulated a 369-line wrapper for selective reset, configuration editing, trust migration, recovery and locking, although upstream already owns provisioning, backups, rollback and concurrency protection.

## What Changes

- Keep the pinned global context-mode 2.1.8 installation and build-time CLI assertion.
- Reduce bootstrap to a standard-library Python adapter that waits for the extension-provided Codex executable, then replaces itself with `context-mode setup --yes --agents codex`.
- Preserve manual fail-fast setup and the bounded `--wait-for-codex SECONDS` interface used by post-attach.
- **BREAKING** for internal tooling: remove `--reset` completely, with no replacement maintenance command. Remove local configuration surgery, trust remapping, snapshots, rollback, deletion checks and locks.
- Delegate file handling, backups, recovery and concurrent-setup rejection to the official package. Preserve the package pin, extension launcher and Dev Container lifecycle.
- Replace reset-specific coverage with focused adapter tests and real-package fresh/existing v2 and cold-lifecycle probes. Reconcile operational guidance and record prior real activation separately from simplification validation.

## Capabilities

### New Capabilities

- `development-context-mode`: pinned provisioning, bounded readiness, thin official-setup delegation and operational verification.

### Modified Capabilities

None. This capability has not yet been archived into the main specs.

## Impact

Changes affect the bootstrap helper, context-mode convention, Python/runtime tests and this existing OpenSpec change. Node remains 26.13.1; the current post-create/post-attach lifecycle and persistent `php-qa-scope_codex` volume remain in place. No package update, reset, data deletion, replacement maintenance tool, active-container recreation, PHP API change, commit or archive is part of the simplification.

Sources: project conventions, the published 2.1.8 setup implementation and [official Codex guide](https://github.com/mksglu/context-mode/blob/v2.1.8/docs/install/codex.md). Relevant behavior and acceptance evidence are recorded in this change, independently of external or temporary inputs.

## Open Questions

No unresolved questions. The user selected complete removal of the project-owned reset. Future destructive cleanup must be a separately scoped maintenance operation.
