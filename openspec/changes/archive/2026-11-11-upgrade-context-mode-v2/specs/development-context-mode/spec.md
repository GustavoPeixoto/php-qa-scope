# Spec Delta

## Purpose

Provide reproducible context-mode tooling and a small official-setup adapter for the repository's persistent Codex development environment.

## ADDED Requirements

### Requirement: Pinned development installation

The development image SHALL provide context-mode 2.1.8 through the global package installation and verify its CLI version during construction. It SHALL retain the existing Node runtime and extension-provided Codex executable without a marketplace plugin or separately installed Codex CLI.

#### Scenario: New development image
- **WHEN** the development image is built
- **THEN** its context-mode CLI reports 2.1.8 and supports SQLite and MCP initialization
- **AND** Codex continues to resolve through the existing extension launcher

### Requirement: Official setup delegation

Bootstrap SHALL perform Codex readiness checks and then replace its process with `context-mode setup --yes --agents codex`, inheriting the environment including `CODEX_HOME`. The official package SHALL own configuration, hooks, skills, trust, backups, rollback and concurrency protection. Bootstrap SHALL NOT implement local configuration edits, snapshots, rollback, data deletion or setup locking.

#### Scenario: Ready Codex executable
- **WHEN** readiness succeeds
- **THEN** the official setup receives the inherited environment and exact noninteractive Codex arguments
- **AND** its exit status and termination signals reach the caller

#### Scenario: Official setup fails or rejects a concurrent run
- **WHEN** the official process fails, including a lock-contention error
- **THEN** its diagnostic and failure status reach the caller
- **AND** the adapter does not retry setup or perform its own recovery

### Requirement: Repeated setup preserves state

Normal bootstrap SHALL delegate setup without clearing context-mode history. Repeated successful setup of a v2 installation SHALL preserve managed configuration and unrelated preferences, MCP servers, hooks, trust, skills, credentials and history under the pinned package's behavior.

#### Scenario: Existing v2 installation
- **WHEN** setup runs again after a successful v2 setup
- **THEN** its managed configuration remains unchanged and history and unrelated state remain present
- **AND** no reset or legacy cleanup occurs

### Requirement: Supported bootstrap arguments

Bootstrap SHALL accept only normal invocation and `--wait-for-codex SECONDS`, with a positive integer duration. It SHALL reject `--reset`, other unknown arguments and invalid durations before readiness or setup. No replacement project reset command SHALL be provided.

#### Scenario: Unsupported reset or invalid duration
- **WHEN** a caller passes `--reset`, an unknown option, a noninteger duration or a nonpositive duration
- **THEN** bootstrap returns an argument error before invoking Codex or official setup

### Requirement: Bounded readiness and diagnostics

Waiting SHALL retry only missing Codex executables or launcher exit 127, polling every two seconds with a monotonic deadline and probes limited to five seconds or the remaining budget. Other errors and probe timeouts SHALL surface immediately. Expiry SHALL fail with reconnect/manual retry instructions without changing configuration or data. Without waiting, readiness SHALL remain fail-fast.

#### Scenario: Delayed extension binary
- **WHEN** the executable becomes ready within the configured budget
- **THEN** bootstrap proceeds to official setup

#### Scenario: Deadline or actual error
- **WHEN** readiness expires, a probe times out or Codex returns an error other than 127
- **THEN** bootstrap fails with a diagnostic and does not invoke setup
- **AND** a manual invocation without waiting does not retry a missing executable

### Requirement: Extension-dependent automatic initialization

Post-create SHALL repair volume ownership and install Git hooks without requiring Codex. `waitFor` SHALL remain `postCreateCommand`. Post-attach SHALL invoke `setup-codex-context-mode --wait-for-codex 180` so the editor can connect and install its extensions before setup finishes.

#### Scenario: New container without extensions
- **WHEN** post-create runs before the Codex extension is available
- **THEN** post-create completes independently of Codex and the editor can connect
- **AND** post-attach waits for extension delivery and completes official setup without manual extension installation

### Requirement: Operational verification and guidance

The context-mode convention SHALL document v2 tools, thin official setup, bounded readiness, delegated recovery/concurrency and version-pinned activation. A clean installation SHALL pass doctor. Real activation SHALL include a fresh Codex session verifying v2 tools and hooks. Future destructive cleanup SHALL be separately scoped maintenance.

#### Scenario: Contributor verifies an installation
- **WHEN** the pinned package and extension are available
- **THEN** doctor passes and the MCP listing shows context-mode enabled
- **AND** a fresh session exposes the v2 tools and working hooks
