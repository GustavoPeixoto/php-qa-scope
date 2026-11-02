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
- [x] 2.3 Retain CI-specific per-check outcomes, remove aggregate mode and its exclusive helpers/tests, and require the check/image/revision CLI arguments; test valid check dispatch plus rejection of removed flags, unknown IDs, and incomplete inputs.
- [x] 2.4 Test adapter execution, missing commands, preparation/startup failures, catchable cancellation, and preservation of available stdout/stderr; run existing hook Python tests to verify helper reuse does not alter hook runtime, reports, or command scopes.
- [x] 2.5 Document CI evidence paths/outcomes in `conventions/artifacts.md` and per-check command/report parity in `conventions/git-hooks.md`; remove central-download/aggregate requirements and verify CI records remain separate from local pre-push evidence.

## 3. Pull request workflow

- [x] 3.1 Keep the dedicated unfiltered PR events and exact temporary-merge checkout; update workflow tests for one matrix job without an aggregate checkout and verify persisted credentials remain disabled.
- [x] 3.2 Add the seven-entry matrix with fail-fast disabled, per-PR superseded-run cancellation, and a 30-minute per-check timeout; verify matrix membership against the shared registry and independence when one check fails.
- [x] 3.3 Build only the appropriate shared tooling image per entry, install locked development dependencies for PHP jobs, and invoke the CI adapter; verify no independent tool-version pins, local env files, Compose services, dev bootstrap, secrets, or write credentials are required.
- [x] 3.4 Keep always-attempted per-check uploads, remove the aggregate job/downloads, and test that all seven stable `QA (<id>)` names are emitted while validation and upload failures are not masked.
- [x] 3.5 Run real-image smoke execution of all seven checks against a disposable clean checkout, verify each successful outcome/report and tested revision independently, preserve native findings/startup/cancellation evidence, and confirm tracked files and lock remain unchanged.
- [x] 3.6 Test unchanged release-workflow identity/skip behavior and update `conventions/releases.md` with the seven individually required checks, native success/skipped/neutral acceptance, explicit future-check registration, and the existing release/tag authorization model.
- [x] 3.7 Add SHA-pinned Buildx and optional GitHub cache restore/save steps for separate PHP/Node tooling layers, keyed by format/OS/architecture/family/Dockerfile; preserve shell logs and local image loading, rotate successful local exports, and publish before native validation without masking real preparation failures.
- [x] 3.8 Cache only Composer downloads for PHP jobs with runtime/manifest/lock keys and same-runtime fallback; mount the writable cache while preserving temporary Composer home, runner ownership, mandatory locked installs, and no cached vendor/credentials/results.
- [x] 3.9 Verify cold/warm local layer reuse, current-lock installation and invalidation contracts, optional cache failures, and fatal build/install/check/upload behavior; run the PR QA suite, Actionlint, and Zizmor, and document cache scope and limitations in the environment convention and dated verification evidence.

## 4. Rollout and remote acceptance

- [ ] 4.1 Update the same PR #6 through an additional specifically authorized commit/push/body edit, observe the seven latest-revision check results without an aggregate, and retain the infrastructure integration task as incomplete until actual integration is authorized and completed.
- [x] 4.2 Prepare the live main ruleset amendment adding all seven emitted `QA (<id>)` contexts with their observed integration alongside every existing check; apply only after specific authorization, then reread and verify the native acceptance policy, up-to-date enforcement, zero approvals, empty bypass, and unchanged main/tag protections.
- [ ] 4.3 Record remote ordinary/documentation/draft/fork/release eligibility and required-check enforcement evidence; distinguish success/skipped/neutral from missing, pending, failed, cancelled, timed-out, or other results, and leave missing proof explicit without intentional remote failure probes or extra PRs.
- [x] 4.4 Add dated `verification.md` evidence distinguishing local tests, remote rule inspection, live check behavior, and limitations; leave activation tasks incomplete whenever access or enforcement proof is missing, and verify the documented rollback preserves existing protections.
- [ ] 4.5 After specifically authorized publication to PR #6, observe real cold/warm GitHub cache behavior, restored layers/downloads, timings, and all seven latest-revision checks without artificial commits or failure probes; keep missing observations explicitly pending.

## 5. Final consistency

- [x] 5.1 Audit proposal/design/spec/task parity and references to temporary or unversioned material; verify all requirements and implementation decisions remain understandable from durable artifacts alone.
- [x] 5.2 Run `openspec validate add-required-pr-qa --strict --no-interactive` and `openspec validate --all --strict --no-interactive --json`; verify success and distinguish completed implementation from any still-incomplete remote activation before handoff or archive.
