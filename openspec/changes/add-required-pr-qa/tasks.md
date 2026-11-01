# Tasks

## 1. Shared tooling images

- [x] 1.1 Read this change's proposal, design, and spec together with `conventions/environment.md`, `conventions/git-hooks.md`, and `conventions/artifacts.md` before durable edits; confirm the shared runtime and output contracts against the current Dockerfiles and hook helpers.
- [x] 1.2 Refactor the dev Dockerfile into `tooling -> development`, keeping the existing Node reference, Corepack, and OpenSpec 1.14.0 install in tooling and workspace/user/bootstrap configuration in development; verify the tooling target builds without development arguments and reports the pinned OpenSpec version.
- [x] 1.3 Move existing `unzip` provisioning into PHP tooling for locked Composer installs, without changing PHP/Composer versions or Xdebug isolation; verify a real `composer install --no-interaction --no-ansi --prefer-dist --no-progress` succeeds in that image without platform exemptions or lock changes.
- [x] 1.4 Add focused runtime tests comparing Node/OpenSpec versions between tooling and development, and PHP/Composer versions with their existing shared declarations; verify the default dev build still provides user/workspace behavior, Lefthook, assistant tools, scripts, and OpenSpec workflow configuration.
- [x] 1.5 Update `conventions/environment.md` with the shared Node/OpenSpec stage, standalone builds, default development behavior, and retained mutable-tag limitation; verify the documented commands against the built images.

## 2. CI validation adapter and evidence

- [x] 2.1 Read `qa.command`, the shared report registry/validators, their nearby Python tests, and the artifact convention before adding `tools/pr-qa` and `tools/pr_qa/`; implement check mode with ID/revision validation, argv-only native execution in the selected image, matching absolute checkout mounts, writable runner-owned outputs, and catchable container cleanup.
- [x] 2.2 Reuse the existing report helpers to capture and validate all seven report formats under `logs/pr-qa/`, preserving diagnostics, native nonzero codes, and unknown startup outcomes; verify representative genuine zero/nonzero reports and empty, malformed, semantically invalid, or foreign-root reports through the actual validators.
- [x] 2.3 Implement CI-specific outcomes and aggregate mode requiring exactly seven successful current-revision outcomes and valid retained reports; test missing, duplicate, unknown, failed, skipped, cancelled, foreign-revision, invalid-report, and successful evidence sets, including rejection of outcome-controlled arbitrary paths.
- [x] 2.4 Test adapter execution, missing commands, preparation/startup failures, catchable cancellation, and preservation of available stdout/stderr; run existing hook Python tests to verify helper reuse does not alter hook runtime, reports, or command scopes.
- [x] 2.5 Document CI evidence paths/outcomes in `conventions/artifacts.md` and shared command/report parity in `conventions/git-hooks.md`; check that CI records remain separate from local pre-push schemas and ownership evidence.

## 3. Pull request workflow

- [x] 3.1 Add the dedicated workflow for opened, reopened, synchronized, ready-for-review, and edited PR events without branch/path/origin/draft filters; test its event configuration and exact temporary-merge SHA checkout with persisted credentials disabled.
- [x] 3.2 Add the seven-entry matrix with fail-fast disabled, per-PR superseded-run cancellation, and a 30-minute per-check timeout; verify matrix membership against the shared registry and independence when one check fails.
- [x] 3.3 Build only the appropriate shared tooling image per entry, install locked development dependencies for PHP jobs, and invoke the CI adapter; verify no independent tool-version pins, local env files, Compose services, dev bootstrap, secrets, or write credentials are required.
- [x] 3.4 Add always-attempted per-check uploads and the `QA Required` aggregate job, requiring successful upstream execution and exact valid evidence; test upload failure, upstream skips/cancellation, missing evidence, and complete success without `continue-on-error` masking failures.
- [x] 3.5 Run a real-image smoke execution of all seven checks and the aggregate against a disposable clean checkout, retaining reports and the tested revision; also verify native findings remain failures with diagnostics and that the checkout's tracked files and lock are unchanged.
- [x] 3.6 Test compatibility with existing release workflow contracts, including unchanged `Validate Release Branch` identity and skip rules; update `conventions/releases.md` with the new aggregate check and preserve its current release/tag authorization model.

## 4. Rollout and remote acceptance

- [ ] 4.1 Integrate the tested infrastructure through the existing PR/check process, subject to the repository's Git-operation authorization requirements; observe and record `QA Required` on the intended merge revision without creating a release or changing the package version.
- [ ] 4.2 Inspect the live main ruleset and check integration, then add the emitted `QA Required` requirement alongside all existing required checks; verify an authenticated reread preserves up-to-date enforcement, zero approvals, the empty bypass list, and all main/tag protections.
- [ ] 4.3 Record remote workflow evidence covering ordinary, documentation-only, draft, fork, and release PR eligibility, including platform approval limitations where applicable; verify failed QA blocks main merge and successful QA remains eligible alongside an emitted skipped ordinary release check, using approved probes or explicitly recording unverified enforcement.
- [x] 4.4 Add dated `verification.md` evidence distinguishing local tests, remote rule inspection, live check behavior, and limitations; leave activation tasks incomplete whenever access or enforcement proof is missing, and verify the documented rollback preserves existing protections.

## 5. Final consistency

- [x] 5.1 Audit proposal/design/spec/task parity and references to temporary or unversioned material; verify all requirements and implementation decisions remain understandable from durable artifacts alone.
- [x] 5.2 Run `openspec validate add-required-pr-qa --strict --no-interactive` and `openspec validate --all --strict --no-interactive --json`; verify success and distinguish completed implementation from any still-incomplete remote activation before handoff or archive.
