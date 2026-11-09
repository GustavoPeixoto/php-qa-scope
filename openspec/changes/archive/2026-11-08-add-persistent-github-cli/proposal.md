# Proposal

## Why

Recreating the dev container removes the manually installed GitHub CLI and its login state. Install the CLI in the development image and persist its configuration so repository work can resume without reinstalling and reauthenticating after every rebuild.

## What Changes

- Install the distribution's `gh` package in the existing development-stage APT transaction.
- Give the dev user a private GitHub CLI configuration directory, with `GH_CONFIG_DIR` pointing to it.
- Mount the project-scoped GitHub CLI volume from the Compose dev service so direct Compose and the Dev Container share the same persistent configuration.
- Declare the existing Codex state volume in Compose as well, removing its separate Dev Container mount while preserving its physical Docker volume identity.
- Keep Dev Container ownership repair for both directories; remove the redundant post-create chmod while retaining mode `0700` for GitHub CLI at image initialization.
- Initialize the Codex directory with dev ownership in the image so a fresh Compose volume is writable without root.
- Document manual browser login, credential storage, volume retention, and separate authorization for real login and active-environment recreation.
- Validate the actual development image and disposable-volume persistence for both directories without real credentials. Confirm that the resolved Codex volume name matches the active mount before any future activation.

## Capabilities

### New Capabilities

- `development-github-cli`: Development CLI availability, shared persistent account configuration, and explicit authentication lifecycle.

### Modified Capabilities

None. The existing `repository-pr-qa` contract retains its tooling/development separation.

## Impact

Changes affect the development Dockerfile, Compose service/volume, Dev Container initialization, runtime tests, and environment convention. They introduce no PHP API, dependency, script, workflow, package-version, or protection changes. The archived QA change remains untouched; this new change is delivered in the same PR #6 on the current branch.

Credentials reside in the local volume as files with private directory permissions, not in the image or repository. Persistence does not prevent credential expiration/revocation or survive deliberate volume deletion. Tests use a separate disposable volume and synthetic data. The active dev container, existing named volumes, stash, and index remain intact until separately authorized operations are presented.

Consulted sources: `conventions/workflow.md`, `conventions/environment.md`, `conventions/git.md`, `conventions/artifacts.md`, current Docker/Compose/Dev Container configuration, image runtime tests, and the existing PR QA specification.

## Open Questions

No relevant implementation questions remain. Recreating the active environment, real browser login, staging, commit, push, PR editing, review approval, and merge are separate operational gates.
