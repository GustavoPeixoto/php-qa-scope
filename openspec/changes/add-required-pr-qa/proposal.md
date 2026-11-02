# Proposal

## Why

The seven full-scope pre-push validations currently protect local pushes, but ordinary GitHub pull requests have no equivalent QA gate. Running those validations on each proposed integration closes that gap, while sharing Node/OpenSpec tooling between development and CI prevents independently maintained version declarations.

## What Changes

- Add a GitHub Actions QA workflow for every pull request, including drafts, forks, release branches, and documentation-only changes, without branch or path filters.
- Validate the pull request's temporary merge commit against its target branch, using seven independent checks: QA Scope, PHPCS, PHP CS Fixer, PHPMD, PHPStan, PHPUnit, and OpenSpec.
- Reuse the pre-push command definitions, native report validators, complete configuration scopes, and report options without invoking its dev-only coordinator.
- Add `tooling -> development` stages to `docker/dev/Dockerfile`: share the existing Node reference, Corepack, and pinned OpenSpec installation; retain interactive tooling and configuration in `development`.
- Reuse the PHP/Composer `tooling` target and locked development dependencies for the six PHP checks; move the existing `unzip` utility into that shared stage so Composer can extract dependency distributions.
- Cache Docker tooling layers and Composer package downloads in GitHub Actions without coupling the seven checks. Keep each locked install and native validation mandatory; cache misses and restore/save failures must not become QA failures.
- Retain each check's available reports, diagnostics, and outcomes; its native execution, report validation, and required artifact upload determine its own job result. No aggregate job or artifact-download gate is needed.
- Require the seven emitted `QA (<id>)` checks individually in the existing `main` ruleset alongside `Validate Release Branch`. All required checks must be present and completed with `success`, `skipped`, or `neutral`; every other state or conclusion blocks merge. Preserve release checks and protections and record dated remote activation evidence separately from local verification.

## Capabilities

### New Capabilities

- `repository-pr-qa`: Full-scope pull request QA, shared development/CI tooling and validation contracts, retained diagnostic evidence, and individual required-check activation on `main`.

### Modified Capabilities

None. Existing hook runtime policies and release eligibility, validation, and publication requirements remain applicable; their required behavior does not change.

## Impact

- Affected implementation: GitHub Actions workflows, a small Python CI adapter, shared helpers in `tools/git_hooks/qa.py` and `tools/git_hooks/reports.py`, development image stages, and focused automation tests.
- Affected operations: the existing `Protect main` ruleset and contributor environment, hook-parity, artifact, and release activation documentation. Existing release workflows and the `Validate Release Branch` check retain their identities and behavior.
- No changes to the package's public PHP API, Composer commands, supported PHP versions, managed scopes, or release/tag permissions. Merge queue support, extra PHP-version matrices, publishing images, dependency upgrades, and implementing the full dev-container hook runtime in Actions are outside scope.
- Existing version values remain unchanged. Sharing stage definitions prevents configuration drift but does not promise byte-for-byte reproduction of mutable upstream image tags or registries.
- Risks include registry availability, repeated cold-cache matrix setup, cache storage/transfer costs, CI report-path permissions, and inability to verify repository administration remotely. Cache entries are optional accelerators, never validation evidence. Missing remote access blocks activation verification rather than permitting an unverified completion claim.
- Consulted durable sources: `conventions/workflow.md`, `conventions/environment.md`, `conventions/git-hooks.md`, `conventions/artifacts.md`, `conventions/releases.md`, the existing `repository-git-hooks` and `release-tagging` specifications, native QA scripts, Dockerfiles, and release workflows. The decisions needed to implement this change are recorded in its own artifacts.

## Open Questions

No unresolved product or design questions. The accepted 2026-11-01 revision removes only the aggregate gate and its exclusive code, retaining the seven checks and updating the same PR #6. The native required-check list is explicit; future checks must be registered separately. Conditional release checks may be skipped in ordinary PRs. No merge, review approval, or intentional remote failure probe is authorized. **High-priority activation prerequisite:** authenticated rule inspection is available, but publication and protection updates each still require their concrete authorization and latest-revision verification. Missing enforcement evidence leaves remote acceptance incomplete.
