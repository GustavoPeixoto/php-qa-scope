# Design

## Context

The dev image already has a development-only APT transaction and a configurable dev user. Compose supplies the dev service to the Dev Container. Codex persistence is currently a separate Dev Container mount, while GitHub CLI and its credentials were installed manually and disappeared on recreation. Existing runtime probes inspect terminated containers before collecting logs and removing them.

## Goals / Non-Goals

Make the CLI and persistent configuration work in both Compose entrypoints. Keep Node/OpenSpec tooling and the archived QA implementation unchanged. Do not recreate the active dev environment, authenticate an account, change Git state, or modify PR #6 without the corresponding separate authorization.

## Decisions

### Install through the existing distribution package transaction

Add `gh` to development's APT package list, following existing OS utility provisioning. This avoids a second package repository, architecture-specific downloads, and a new independently maintained version pin. Record the actual distribution version during runtime validation. Shared tooling remains the same parent stage.

### Compose-owned configuration volumes

Declare `github-cli` and `codex` at Compose's top level with default project-scoped naming, mounted only in dev at `/home/dev/.config/gh` and `/home/dev/.codex`. The Dev Container inherits both instead of declaring another mount. The active Codex mount is `php-qa-scope_codex`, labeled with project `php-qa-scope` and volume key `codex`; the new declaration resolves to that exact name, reusing the same data without copying, renaming, or deleting the volume.

Set `GH_CONFIG_DIR=/home/${USERNAME}/.config/gh` in the development image. Create `.config` and `.codex` with dev ownership, and the `gh` directory with dev ownership and mode `0700`, so fresh named volumes inherit usable metadata. Retain Dev Container post-create ownership repair for both paths to handle user-ID adjustment. Do not repeat chmod there: the gh mode is established by image initialization and retained by the volume. Preserve existing files and their modes.

### Manual authentication in the retained directory

The image has no configured keyring service. Document the installed CLI's file storage and verify the stored location during a later authorized login. The volume is not an encryption service: local account files must remain private, and no credential is baked into the image, passed through build arguments, printed, or committed. Do not automate `gh auth login`, `gh auth setup-git`, SSH key provisioning, scope refreshes, or destructive volume cleanup. Existing SSH remote usage stays unchanged.

### Validate persistence without authenticating

Extend actual-image runtime coverage to verify `gh`, directory ownership, and two disposable named volumes across two containers. Write a CLI configuration marker and synthetic GitHub/Codex account files, then compare their digests after recreation with networking disabled. Confirm GH directory mode `0700` and preserved account-file modes. Use uniquely named test resources and the existing completion/log-collection helper; remove only owned test resources. Separately inspect Compose's resolved Codex name against the existing active mount, without mounting real state into any probe.

## Risks / Trade-offs

- Distribution package and base-image updates can change the installed version; report it rather than promising a latest release or byte-for-byte reproducibility.
- Volume credentials are sensitive local files; keep the directory private and omit their content from evidence. Persistence ends on explicit logout/removal or credential invalidation.
- A real active-environment rebuild and browser login can interrupt this session; they remain separate rollout gates. Disposable runtime proofs do not claim a real account login was exercised.

## Migration Plan

Implement and validate locally on the existing PR #6 branch, complete the implementation checklist, sync the specification, and archive this change before preparing the commit. Present staging, commit, push, and PR edits separately under the Git convention. Rebuild/recreate the active dev environment only in a coordinated authorized step, then perform one authorized browser login and verify account identity and configuration location without revealing the token. Retain the volume during later rebuilds. A rollback can remove the mount and package declaration while leaving the volume for the user; never delete existing credential volumes automatically.
