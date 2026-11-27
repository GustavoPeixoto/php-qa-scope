# Tasks

Sections 1-4 record the completed initial inline implementation. Section 5 replaces that loading approach with the approved dedicated script and fixed-revision checkout; earlier no-checkout statements describe historical work.

## 1. Confirm implementation context

- [x] 1.1 Read this change's proposal, design, delta spec, and dynamic apply instructions; reread `AGENTS.md`, `openspec/config.yaml`, the complete main `release-tagging` spec, and applicable release, Git, Git hook, workflow, environment, language, artifact, repository, and context-mode conventions before durable edits. Verify that scope remains infrastructure only and no design question blocks implementation.

## 2. Delimit existing workflow jobs in tests

- [x] 2.1 Add explicit job-section extraction in `tools/release/test_workflows.py`; migrate publisher/validation selectors, step extraction, conditions, checkout checks, and permission assertions to bounded sections. Verify that the selector excludes an adjacent job using a synthetic workflow fixture and that all existing workflow tests still pass without weakening their security assertions.

## 3. Publish and recover GitHub Releases

- [x] 3.1 Expose publisher job outputs from the unchanged `authority` step and add `github-release` with its exact display name, `needs: publish`, normal success-dependent scheduling, and job-local `contents: write`. Verify through workflow assertions and a dependency-aware fixture that successful tag publication supplies the original tag/SHA and failed, canceled, or skipped publication prevents the new job from executing.
- [x] 3.2 Add the no-checkout inline coordinator described in `design.md`, using environment inputs and the runner's GitHub CLI. Verify through execution of the real workflow block that exact lightweight tag/SHA matches proceed, missing/malformed inputs and missing/wrong-type/wrong-SHA tags fail, and no current-main or source-tip value supplies publication authority.
- [x] 3.3 Implement complete paginated Release discovery, fatal lookup errors, normal-published no-op success, and draft/prerelease conflict failure. Verify mocked first/later-page matches, empty successful enumeration, authentication/network/API/404 errors, malformed or repeated/incomplete pages, and unchanged existing Release content and tag refs.
- [x] 3.4 Create absent Releases with the exact repository, integrated target, title, generated-notes, verify-tag, non-draft, and non-prerelease arguments from the design and no asset arguments. Verify actual CLI argument capture for `v0.1.0` and a subsequent stable version and propagate creation failures without tag cleanup.
- [x] 3.5 Extend the stateful fixture pipeline to retain successful publisher outputs and rerun only the Release job after creation failure, including remote success before client failure. Verify successful independent recovery, unchanged refs, no edits on repetition, and zero additional authority, progression, App-token, or create-ref calls during recovery.
- [x] 3.6 Update `conventions/releases.md` for the new stage, generated presentation, automatic source archives, Packagist independence, successful-tag/failed-Release recovery, existing normal Releases, conflicting drafts/prereleases, fatal lookup errors, and platform partial-rerun limits. Verify that examples follow the implemented job flow, preserve existing tag-publication recovery rules, and do not prescribe real publication as infrastructure validation.

## 4. Validate integration and review boundaries

- [x] 4.1 Run `PYTHONPATH=tools python3 -B -m unittest discover -s tools/release -p 'test_*.py'` in `dev`, configuring `RELEASE_TEST_HOST_WORKSPACE` and the documented tooling/development images as required. Verify that the complete suite passes, including Composer fixtures, new job-boundary checks, and all publication/recovery cases, using only simulated GitHub writes.
- [x] 4.2 Audit the full diff and workflow assertions for unchanged existing conditions, check names, permissions, action pins, checkout revisions, concurrency, duplicate-tag rejection, authority outputs, and protected-tag creation. Verify that only the new job receives normal-token write permissions, that it has no checkout/App credentials/PAT/new secrets, and that no new trigger, manifest version, production release object, protection, or Packagist/App setting change is included.
- [x] 4.3 Audit artifact parity and self-sufficiency, run `openspec validate add-automated-github-releases --strict --no-interactive` and `openspec validate --all --strict --no-interactive`, and review the final task state. Verify successful validation and record local evidence separately from unexercised live publication; do not perform Git/GitHub mutations without their separate concrete authorization.

## 5. Extract the Release coordinator

- [x] 5.1 Reread the revised planning artifacts and applicable release conventions, extract the coordinator into `tools/release/github_release.py` with `main()` and standard-library-only imports, add the publisher-pattern checkout at `github.workflow_sha`, and replace inline Python with its isolated single-line invocation. Adapt the existing fixture harness to execute that command from a selected temporary checkout; verify all current publication and recovery tests pass with unchanged environment inputs, diagnostics, CLI arguments, permissions, and outputs.
- [x] 5.2 Verify the new checkout's name, pinned action, exact workflow revision, default workspace, full scope, and disabled credential persistence. Add missing-script and poisoned-candidate/fallback fixtures; verify the job fails before API activity when the selected script is unavailable and never executes another source. Preserve existing job-scoped checkout/security assertions.
- [x] 5.3 Update contributor guidance to describe the dedicated coordinator and fixed-revision checkout while preserving publication and recovery rules. Label prior verification as historical and verify no current design, spec, or guidance still requires inline execution or absence of checkout.
- [x] 5.4 Run the complete release suite in `dev` with the documented host-workspace mapping and images, validate workflow YAML and strict change/project OpenSpec checks, and audit the final diff and artifact parity. Record fresh evidence separately from the initial implementation, verify all tasks complete and no real publication or unauthorized Git/GitHub mutation occurred.
