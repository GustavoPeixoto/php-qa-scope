## MODIFIED Requirements

### Requirement: Shared development and CI tooling
Development and PR QA SHALL obtain PHP and Composer from the existing PHP Dockerfile `tooling` stage and Node and OpenSpec from a new development Dockerfile `tooling` stage. Version declarations SHALL remain in these Dockerfiles rather than being independently maintained in workflow configuration. Existing version values SHALL be preserved. The development Dockerfile SHALL provide `tooling -> development`, with Corepack and the pinned OpenSpec installation inherited by `development`. Both tooling targets SHALL build without development workspace arguments, local environment files, running Compose services, or development bootstrap scripts. Locked PHP development dependencies SHALL be installed without updating the lock or ignoring platform requirements.

#### Scenario: Standalone CI build
- **WHEN** either tooling target is built from the repository root without local development configuration
- **THEN** the required runtime and package manager SHALL be available for the corresponding CI checks
- **AND** the Node tooling target SHALL provide the same OpenSpec version as development

#### Scenario: Development compatibility
- **WHEN** the dev image is built through the existing Compose or Dev Container entrypoint
- **THEN** it SHALL retain its configured user, workspace behavior, Lefthook, Codex launcher, context-mode, Git hook bootstrap, and OpenSpec workflow configuration
- **AND** the final default image SHALL remain the development environment

#### Scenario: Development without Headroom
- **WHEN** the updated development image and Dev Container bootstrap are used
- **THEN** Headroom, its setup/startup helpers, and its dedicated installation directory SHALL be absent
- **AND** container startup SHALL NOT configure or wait for a Headroom proxy
- **AND** the remaining context-mode and Git hook bootstrap SHALL complete without Headroom
