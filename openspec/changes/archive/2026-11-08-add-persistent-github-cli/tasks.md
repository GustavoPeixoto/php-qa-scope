# Tasks

## 1. Development image

- [x] 1.1 Preserve development-stage GitHub CLI provisioning and rebuild the revised image; verify `gh --version` as dev and existing Node/OpenSpec and development-tool checks.
- [x] 1.2 Initialize both configuration directories with dev ownership, retaining `0700` for GH only in the image; verify matching UID/GID and non-root writing in fresh disposable volumes.

## 2. Shared persistent configuration

- [x] 2.1 Declare both dev-only Compose volumes, remove the separate Codex mount and post-create chmod while retaining ownership/setup commands; verify resolved Codex volume identity matches the active `php-qa-scope_codex` mount without duplicates.
- [x] 2.2 Run actual-image persistence coverage for both directories across two disposable containers; verify configuration readback, unchanged synthetic account-file digests/modes, and owned-resource cleanup, then update the environment convention.

## 3. Final integration

- [x] 3.1 Run relevant PR QA/runtime suites, strict selected/all OpenSpec validation, and whitespace checks; verify no package, tooling-stage, workflow, lock, or archived-QA changes.
- [x] 3.2 Append dated verification that supersedes prior setup details without erasing evidence; audit artifact consistency and confirm HEAD, index, stash, active services, and existing volume identity are preserved before sync/archive and commit review.
