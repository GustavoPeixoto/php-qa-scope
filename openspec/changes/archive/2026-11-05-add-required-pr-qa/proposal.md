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
- Retain each check's available reports, diagnostics, and outcomes for the current workflow attempt, subject to the configured retention period. A rerun may make earlier-attempt artifacts unavailable; preserving them across attempts is not required. Native execution, report validation, and required artifact upload determine each job's result. No aggregate job or artifact-download gate is needed.
- Require the seven emitted `QA (<id>)` checks individually in the existing `main` ruleset alongside `Validate Release Branch`. All required checks must be present and completed with `success`, `skipped`, or `neutral`; every other state or conclusion blocks merge. Preserve release checks and protections and record dated remote activation evidence separately from local verification.
- Verify remaining eligibility, enforcement, and cache cases in an independent disposable public laboratory seeded from `9d5588a`. Accept authenticated original configuration plus equivalent laboratory enforcement with explicit limitations: no real fork, emitted neutral conclusion, or direct failed-check probe against original main. No test refs, commits, PRs, runs, or caches may be written to the original repository.

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

## Completion and integration

The accepted 2026-11-05 closure sequence is update, apply, sync, and archive within the existing PR #6. Task 4.1 covers the implementation already published at `9d5588a` and its observed seven successful independent QA checks. Archive records implementation completion; it does not claim that PR #6 has merged. Final documentation publication, fresh checks for that new commit, and any later merge remain separate Git/GitHub steps with operation-specific authorization. This explicitly supersedes the earlier decision to keep task 4.1 open until integration. The laboratory repository was deleted manually by the user and subsequently returned authenticated HTTP 404; exported evidence and its local checkout remain preserved.

## Open Questions

The accepted laboratory scope and limitations are settled. The 2026-11-03 laboratory decision changed acceptance evidence without changing functional requirements; the separate 2026-11-05 retention decision below explicitly narrows preservation across attempts. Intentional fixtures were restricted to the disposable laboratory after operation-specific authorization. A second owner is unavailable, so a real fork test is explicitly excluded. No original-repository mutation, merge, review approval, release, or tag is included in laboratory validation. **High-priority execution prerequisite:** every Git/GitHub mutation batch, including laboratory creation, instrumentation, cancellation/rerun, PR changes, and final deletion, requires concrete review and specific authorization. Tasks 4.3 and 4.5 are complete under their accepted laboratory criteria. The subsequent 2026-11-05 closure decision defines task 4.1 as published implementation verification, not completion of the merge. Integration remains a separately authorized GitHub step.

**Accepted retention policy (2026-11-05):** require available reports from the current workflow attempt, subject to the configured retention period, and accept that a rerun may make earlier-attempt artifacts unavailable. All seven first-attempt artifact IDs returned HTTP 404 after the authorized same-run rerun despite a future expiration date; all prior ZIPs were exported locally, and the rerun published seven fresh artifacts. This decision resolves the earlier retention review through an explicit requirement revision, not a proven root cause or a workflow change. Upload after success/failure and failure of the job on a failed required upload remain mandatory. Cancelled required checks blocked the laboratory PR, satisfying cancellation acceptance without another remote native-tool interruption probe. See the dated evidence in `verification.md`.

No relevant implementation questions remain. The accepted coverage limits and current-attempt retention trade-off are settled decisions. Publishing these final artifacts and merging PR #6 remain pending operations, not unresolved implementation requirements.
