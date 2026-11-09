# development-github-cli Specification

## Purpose

Provide GitHub CLI tooling in the development environment and preserve its local account configuration across container replacement without embedding credentials in build artifacts.

## Requirements

### Requirement: Development CLI availability

The built development image SHALL provide `gh` on PATH for the normal dev user. Installation SHALL occur in the development stage without introducing GitHub credentials or additional bootstrap requirements into the shared tooling stage.

#### Scenario: Fresh development container
- **WHEN** a development container is created from the built image
- **THEN** the dev user SHALL be able to run `gh --version` without installing packages or authenticating

#### Scenario: Shared tooling build
- **WHEN** CI builds the existing shared tooling target
- **THEN** that target SHALL retain its existing Node/OpenSpec contract without requiring GitHub CLI installation or credentials

### Requirement: Persistent shared CLI configuration

The dev service SHALL persist its GitHub CLI configuration in one project-scoped named volume, shared by direct Compose use and the Dev Container. `GH_CONFIG_DIR` SHALL identify the mounted directory. The directory SHALL be owned by the dev user, writable without root, and restricted to that user. Initialization SHALL preserve existing configuration contents.

#### Scenario: Recreated dev container
- **WHEN** a dev container is replaced while its configuration volume is retained
- **THEN** the replacement SHALL read the same configuration and stored account files
- **AND** initialization SHALL NOT replace existing credentials

#### Scenario: Empty volume initialization
- **WHEN** a new volume is first mounted in the built dev image
- **THEN** the dev user SHALL be able to write configuration without sudo
- **AND** the directory SHALL have permission mode `0700`

#### Scenario: Compose and Dev Container access
- **WHEN** the environment is started directly through Compose or through its Dev Container configuration
- **THEN** both entrypoints SHALL use the same dev-service volume and configuration directory
- **AND** the Dev Container SHALL NOT introduce a second mount for that directory

#### Scenario: Existing Codex volume reuse
- **WHEN** the Codex state mount is moved from Dev Container configuration into Compose
- **THEN** the dev service SHALL retain the same project-scoped `codex` volume identity and `/home/dev/.codex` target
- **AND** both entrypoints SHALL inherit that mount without duplication
- **AND** fresh Codex state SHALL be writable by dev while existing state remains intact

### Requirement: Explicit authentication lifecycle

Authentication SHALL remain a separately authorized, manual browser operation after environment recreation. Credentials SHALL NOT be placed in image layers, build arguments, versioned files, or diagnostic output. Provisioning SHALL NOT log in automatically, reconfigure Git authentication, or generate or upload SSH keys.

#### Scenario: Image construction and initialization
- **WHEN** the development image is built or its configuration directory initialized
- **THEN** no real account login or GitHub account mutation SHALL occur
- **AND** existing SSH configuration and Codex state SHALL remain intact

#### Scenario: Credential lifecycle
- **WHEN** a user retains the volume across rebuilds
- **THEN** stored authentication SHALL remain available while the credential is valid
- **AND** documentation SHALL explain that revocation, expiration, logout, or volume removal can require a new login
