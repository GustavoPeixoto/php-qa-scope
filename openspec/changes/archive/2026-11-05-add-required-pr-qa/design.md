# Design

## Context

See `proposal.md` for motivation and scope. `tools/git_hooks/qa.py` already builds the seven native command vectors, and `tools/git_hooks/reports.py` owns check identities, report paths, and native/OpenSpec validation. Their pure helpers are reusable without entering hook preflight, allocation, supervision, or Docker lifecycle code. The local gate additionally enforces dev-only Git/runtime policies that do not apply to Actions.

Only release PR validation currently runs before merge; its workflow targets `main`, checks the proposed head SHA, and emits `Validate Release Branch`. It is intentionally skipped for ordinary branches. The new QA workflow is separate and validates the temporary merge revision instead. Existing release semantics remain unchanged.

`docker/php/Dockerfile` already provides `base -> tooling -> development`, with shared PHP/Composer versions. `docker/dev/Dockerfile` is currently one development stage: workspace arguments are mandatory before OpenSpec installation, and Corepack/OpenSpec are mixed with user setup, Lefthook, context-mode, Headroom, and bootstrap configuration.

## Goals / Non-Goals

- Reuse existing validation contracts and runtime declarations while allowing Actions to own job scheduling and lifecycle.
- Keep CI results independently inspectable and require their individual identities through the explicit native main-protection policy.
- Preserve local hook behavior and default development-image behavior.
- Do not reuse the pre-push coordinator, its dev marker, local execution IDs, container evidence schema, or installed contributor hooks in CI.
- Do not expand PHP-version coverage, change dependency versions, adopt merge queues, publish images, or exercise release publication.

## Decisions

### 1. A dedicated PR workflow and individual required checks

Add `.github/workflows/qa.yml`, named `Pull request QA`, using `pull_request` types `opened`, `reopened`, `synchronize`, `ready_for_review`, and `edited`. An edited event reruns QA, including base-branch changes; running again for other edits is acceptable. Omit branch/path filters and draft, fork, or release exclusions. Platform-level fork-run approvals continue to apply; the workflow does not bypass them.

Use `ubuntu-24.04`, workflow permissions `contents: read`, SHA-pinned actions consistent with the release workflows, and checkout with `persist-credentials: false`. Check out `github.sha`, the event's temporary merge commit, rather than a moving merge ref or the PR head. Use the same revision for every matrix entry. Never fall back to the source SHA. A PR without an available merge revision cannot obtain successful required QA.

Use one seven-entry matrix with IDs `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, `test`, and `openspec`, and `fail-fast: false`. Contract tests compare its membership with the shared check registry. Each matrix entry builds only its required tooling image and runs one native check, emitting the stable name `QA (<id>)`. These seven names are required individually through GitHub's native main protection. There is no aggregate job. Only optional cache restore/save steps may use `continue-on-error`; build, install, validation, and required upload failures must remain fatal.

The explicit merge rule is: all required checks must be present and completed with conclusion `success`, `skipped`, or `neutral`. Missing, pending, running, failed, cancelled, timed-out, or any other result blocks merge. `Validate Release Branch` stays required and conditional, so an ordinary PR's skipped release check is accepted. The required list is not a wildcard: future checks must also be registered. Per-check validation still requires native zero and valid evidence to emit success; skipped/neutral acceptance is a deliberate platform-policy choice rather than proof of native execution.

Group workflow concurrency by workflow and PR number, with cancellation of superseded runs. This saves obsolete work without cancelling checks because a sibling failed. A cancelled run never counts as successful. A generous finite job timeout, initially 30 minutes per check, bounds stalled runners rather than importing the hook's cancellation deadline.

Alternative: extending the release job would couple ordinary QA to its release-only eligibility and required-check identity. Running the full pre-push frontend would additionally require dev/Compose/Lefthook infrastructure and inappropriate Git policy checks.

### 2. Share command and report helpers through a small CI adapter

Use the executable Python entrypoint `tools/pr-qa` with standard-library implementation and tests under `tools/pr_qa/`. Its interface is `--check <id> --image <tag> --revision <sha>`, with the current checkout as project root. It returns nonzero on invalid inputs, execution failure, or validation failure. Remove the former `--aggregate`/`--upstream-result` options and their exclusive code/tests. The revision must match the checked-out `HEAD`; check IDs must belong to the shared registry. This is internal repository automation, with no public package API change.

Import and reuse the existing command builder, `CHECKS`, and native/OpenSpec report validators. Do not duplicate their argv, report schemas, or managed-target semantics. Preserve the current helper imports for hook callers and keep hook execution/backend behavior unchanged. A neutral helper extraction is unnecessary for this change; the CI adapter calls only the side-effect-free contract helpers, never the hook check runner or coordinator.

Run the generated argv synchronously in the supplied tooling image via Docker, with init enabled, no stdin/TTY, and argv-based subprocess calls. Capture separate stdout and stderr and preserve the genuine native exit code. Handle catchable interruption by terminating the adapter's own container and returning nonzero; do not manage shared dev services or unrelated containers. Runner loss can prevent finalization and must remain an unsuccessful/incomplete run.

Mount the checkout at the same absolute path on host and container and set that path as the container working directory. This preserves native report paths and allows `valid_openspec` to compare the reported absolute root without rewriting its JSON. The disposable CI checkout is writable for `vendor/`, native caches, and ignored evidence. Use the runner's UID/GID with a writable temporary home for Composer/OpenSpec; do not mount the Docker socket or pass runner credentials into QA containers.

Use `logs/pr-qa/` as the CI evidence root, sharing the existing relative `results/<id>/...` native report paths. For stdout-report checks (QA Scope, Fixer, PHPStan, OpenSpec), validate captured stdout before treating it as the primary report; retain invalid stdout as diagnostics. For file-report checks, retain the report plus console output. Native nonzero findings remain retained reports but fail the check. Empty, malformed, foreign-root, or semantically invalid reports fail even after native zero.

Write a small CI-specific outcome per check containing its identity, merge revision, native exit code (null if unknown), report validity, status, and diagnostic error where applicable. These are CI outcomes, not schema-4 pre-push job records. An outcome cannot be successful without native zero and valid evidence. Tests must exercise the existing validators rather than replace them with success stubs for report acceptance.

### 3. Share both tooling images and install locked dependencies

Refactor `docker/dev/Dockerfile` to begin with the current `mcr.microsoft.com/devcontainers/javascript-node:24-bookworm` reference as `tooling`. Enable Corepack and install `@fission-ai/openspec@1.14.0` there, with a version probe. Then declare `FROM tooling AS development` and retain workspace arguments, OS tools, renamed user, sudo behavior, Git configuration, Lefthook, context-mode, Headroom, copied scripts/configuration, and root/user OpenSpec workflow configuration in that stage. The tooling stage must not run the workflow configuration commands or require workspace arguments. `development` remains last, so the existing Compose build without a target remains compatible.

OpenSpec matrix entries build `docker/dev/Dockerfile --target tooling` and run the shared command inside that image. Do not install Node or OpenSpec independently in the workflow. No dev setup scripts run in CI.

PHP entries build `docker/php/Dockerfile --target tooling` from the same merge checkout. Before validation, install dependencies with the image's Composer using `install --no-interaction --no-ansi --prefer-dist --no-progress`, including development dependencies. Preserve the approved Composer plugin configuration; do not use `update`, ignore platform requirements, or add tool-version pins to YAML. Make distribution extraction available in this shared stage by moving the existing `unzip` installation from PHP development utilities to PHP tooling; retain PHP/Composer versions and Xdebug isolation. This is needed because release validation previously only read manifests, while QA must install packages.

Each PHP matrix job installs its own dependency tree in its isolated checkout. Do not publish images, transfer dependency trees between jobs, or introduce a preparation job. The accepted cache revision below supersedes the original decision to start without caches; the exact lock and platform checks remain authoritative.

The existing mutable Node and PHP image references remain unchanged. This centralizes version declarations; pinning digests or upgrading versions is outside scope.

### 3.1. Optional persistent tooling and Composer caches

Use SHA-pinned official `docker/setup-buildx-action` and `actions/cache/restore`/`save`. BuildKit uses its local importer/exporter; the cache actions persist only the exported layer directory in GitHub's repository cache service. Keep the existing shell build log, build `tooling` with plain progress, and load the result into the runner Docker daemon as `pr-qa-tooling`. No image registry, credentials inside builds, or new job dependency is needed.

Docker cache keys contain a format version, runner OS/architecture, the `php` or `node` family, and that family's Dockerfile hash. The tooling targets consume no checkout files other than their Dockerfile, so ordinary package-source changes do not invalidate these keys. Restore into a runner-temporary directory; import only when its index exists. Export in `mode=max` to a fresh sibling directory, replacing the restored directory only after a successful build. This avoids accumulating obsolete exported blobs. The mutable upstream-reference limitation remains unchanged.

For PHP jobs only, cache Composer downloads under a separate runner-temporary directory. Key by format version, runner OS/architecture, PHP Dockerfile hash, and both Composer manifest/lock hashes; fall back to earlier entries for the same PHP runtime. Bind-mount that directory and set `COMPOSER_CACHE_DIR`, while retaining the temporary `COMPOSER_HOME`, runner UID/GID, and unchanged mandatory locked install. Never cache `vendor/`, credentials, reports, or outcomes. Reusing earlier downloads cannot replace installation or lock/platform validation.

Restore/save failures are warning-only steps. Missing or expired entries build/download normally. Save each newly prepared cache before native validation, and skip saving an exact immutable-key hit. Parallel jobs may all miss initially and do duplicate work; first publication of a key wins, and an existing cache is not a live shared volume. GitHub's native branch/PR cache visibility and eviction apply. Cached content contains no secrets and is not trusted as evidence of successful QA. Record real cold/warm restoration, layer reuse, and timings only after authorized publication. Controlled fixture commits/probes are restricted to the disposable laboratory described below; do not claim a speedup without comparable measurements.

### 4. Retain and validate evidence per check

Each entry uploads a uniquely named `qa-<id>` artifact containing its available native report, stdout/stderr, and outcome, using an always step and the repository's configured artifact retention. Startup/build/install failures must leave available diagnostics; no missing outcome may be synthesized as success. Hard runner loss may prevent upload and does not produce native success. Required artifact-upload failure fails that matrix job, whose individual result is required by main protection.

The accepted 2026-11-05 retention policy covers available artifacts from the current workflow attempt for the configured retention period. A later rerun may make earlier-attempt artifacts unavailable; preserving every attempt is not required. Keep the existing artifact names, action configuration, and upload failure behavior. Laboratory pre-rerun exports preserve this experiment's evidence; they do not introduce a production archival service or a guarantee across attempts. The exact cause of the observed HTTP 404 responses remains unproven.

Keep outcomes as downloadable per-check diagnostic records, rather than merge inputs consumed by a central job. Each check validates its report directly through the shared validators, checks its requested revision against HEAD, and uses registry-owned report paths. Remove artifact downloads, combined inventory validation, and the aggregate-only summary. CI artifacts do not replace local pre-push logs or assert local container ownership/removal facts.

### 5. Extend main protection after the check exists

The current documented `Protect main` ruleset requires `Validate Release Branch` from GitHub Actions and an up-to-date branch, with zero human approvals and no bypass. Treat documented ruleset IDs as discovery hints, not proof of present remote state.

Update the existing PR #6 on `change/release-validation-tooling` through an additional commit; do not rewrite commits or create another PR. Observe the seven emitted `QA (<id>)` checks for its latest revision and confirm their GitHub Actions integration (currently 15368). Prepare their addition to the current main ruleset while retaining `Validate Release Branch` and every other required check/protection. The aggregate is not currently a required context, so there is no aggregate requirement to undo remotely. Do not alter release workflows, App permissions, tag rules, or other target branches' rulesets. The ruleset change is a separately authorized administrative action, never PR code.

Preserve historical aggregate evidence and append dated current evidence to `verification.md`. Verify the native allowlist of `success`, `skipped`, and `neutral`, the configured required identities, the ordinary skipped release result, and all retained protections. Original-repository failure probes and extra PRs remain excluded. The 2026-11-03 decision permits separately authorized intentional laboratory fixtures under the revised acceptance below. Reviews and merges remain excluded. Historical green results cannot certify a different revision.

Document shared tooling in `conventions/environment.md`, validation parity in `conventions/git-hooks.md`, CI evidence in `conventions/artifacts.md`, and the additional required-check activation in `conventions/releases.md`. Keep `README.md` focused on package users. No public PHP API or command changes are required.

### 6. Disposable laboratory acceptance with explicit limitations

Create the independent public repository `GustavoPeixoto/php-qa-scope-validation-20261103`; stop if that name already exists. Materialize all tracked blobs of `9d5588a40f27fd0f60eab3dd527930a797c6e755`, preserving file modes and symlinks, in a separate temporary checkout outside the original repository. Seed an independent main with no copied Git history, tags, remotes, or installed hooks. Record tree and critical-workflow hashes. Do not disable or bypass installed original hooks. Disable only the laboratory's `create-release-tag.yml`; provision no secrets or Apps and never merge or create tags/releases.

After seeding main, reproduce its authenticated original main ruleset as a new laboratory ruleset: all eight contexts bound to Actions integration 15368, strict up-to-date enforcement, zero approvals, empty bypass, and every other applicable rule. Compare normalized mutable payloads after creation. This verifies the copied policy, not a failed-check interaction with original main. Original access remains read-only throughout; preserve PR #6, source branch/index/stash, and existing local evidence edits.

Use exactly two laboratory PRs: `qa/acceptance -> main` and `release/v0.1.0 -> main`. First open the documentation-only acceptance PR as draft and observe all seven QA checks, native reports/outcomes, and skipped release validation with empty repository caches. Mark it ready only after that run finishes; observe warm PHP, Node/OpenSpec, and Composer caches. A second documentation-only commit proves cross-commit reuse and supplies a new revision on which to observe pending/running required-check blocking without the draft restriction.

In the ready acceptance PR, separately instrument and restore: a PHPCS managed-scope mismatch causing genuine QA Scope findings while siblings continue; an omitted test matrix entry with its protection context still required; cancellation of the current active run followed by rerun; and a one-minute test-only job timeout with a controlled wait before native validation. Other job timeouts stay unchanged. Before each observation confirm base freshness, lack of conflicts, zero approval requirements, non-draft state where applicable, and expected check integration. Record native merge eligibility/blocking without attempting merge. Restore production workflow bytes between instrumented cases and verify successful recovery against each current revision. The observed cancelled required checks and blocked PR satisfy cancellation acceptance; interrupting a native tool mid-execution is not an additional remote acceptance requirement.

Change fixture manifest/lock inputs without changing dependency versions to observe a new Composer primary key, restoration by the same-runtime prefix, current-lock installation, and no job-side lock mutation; restore those inputs afterward. The separate canonical release branch uses version 0.1.0 and a coherent lock against the laboratory's empty tag list, and must pass both all seven QA checks and release validation without publishing anything.

Export logs, artifacts, outcome/report checks, source/tested revisions, cache keys/hits/fallbacks, timings, normalized protections, and eligibility observations before cleanup. Preserve findings and available interrupted/timeout diagnostics without inventing native execution. A real fork is unavailable; neutral remains documentary coverage. Accept task 4.3 only with authenticated original configuration, successful reproducible laboratory cases, and explicit acknowledgement of the absent original-main/fork/neutral probes. Task 4.5 needs the complete laboratory cache observations. This changes acceptance evidence, not required runtime behavior. The subsequent 2026-11-05 closure decision makes task 4.1 cover publication and observed validation of the implementation, which are already evidenced at `9d5588a`. Merge is tracked as a separate GitHub integration step, so completed implementation artifacts may be synced and archived in PR #6 before that merge. This supersedes the earlier integration-dependent archive restriction.

Every mutation is disclosed in a bounded operation-specific batch before authorization. Exported evidence remains outside the disposable checkout. After evidence review, request separate authorization to close both PRs and delete the exact laboratory and checkout. Never delete or publish original-repository state as part of this process; publishing final documentation requires separate authorization.

### 7. Complete and archive within the existing PR

Use the update, apply, sync, and archive skills in sequence. Record the published implementation evidence for task 4.1, then sync all ten repository-pr-qa requirements and scenarios into the main specification and verify equivalence before archiving. Preserve the existing dated evidence rather than relabeling old checks as validation of the final documentation commit. A completed implementation checklist and archive do not imply that the PR is merged. Stage, commit, push, and update the same PR only after their specific authorizations; observe fresh results for the new commit before any separately authorized merge. No additional closure PR is required.

The user manually deleted laboratory repository ID `1444157567`; authenticated readback returned HTTP 404. Preserve its exported evidence and `/tmp/php-qa-scope-validation-20261103/checkout`. Closing the former laboratory PRs and expanding CLI deletion permissions are no longer needed; local cleanup remains outside this operation.

## Risks / Trade-offs

- Accepted rerun trade-off (2026-11-05): first-attempt artifact IDs became unavailable remotely after a successful rerun, before their recorded expiration date. All prior ZIPs remain in the laboratory export, and seven fresh artifacts were available for the successful attempt. The accepted policy requires current-attempt evidence and permits loss of earlier-attempt downloads; historical failure diagnosis may therefore require exporting evidence before rerunning. The specific cause is unproven and does not require a workflow change or further remote retention probes for this acceptance.

- Cold-cache builds/downloads and registry outages can increase latency or fail preparation. Optional caches may incur transfer/storage costs or be evicted; preserve independent preparation and diagnostics, and measure actual cold/warm runs before claiming a speedup.
- Tooling images must support locked dependencies and native report formats; smoke-test actual installs and all seven commands rather than inferring readiness from Dockerfile structure.
- Changes to shared helpers could regress hook acceptance; run the existing Python hook tests and focused real-image parity tests.
- Container root paths and permissions can invalidate otherwise correct reports; use matching absolute mounts and runner-owned writable output directories.
- Fork execution may wait for platform approval; record that status rather than claiming skipped checks passed or using privileged event types.
- Missing administration access can prevent operational completion; leave remote tasks unchecked and document the exact limitation.

## Migration Plan

1. Implement shared tooling, CI adapter, workflow, and focused tests; verify default development builds and existing release workflow contracts.
2. Integrate through the existing PR/check policy without a release branch, manifest version change, or tag publication.
3. Observe the seven individual checks on the new revision, then prepare only the required-check-list amendment to the existing main rule for specific authorization.
4. Record authenticated ruleset/check evidence and enforcement results or explicit verification limits. Activation is incomplete while required evidence is missing.
5. If rollback is necessary, restore the prior required-check list before removing the workflow; retain the release check and all other protections. Revert the development stage refactor if needed and rebuild/recreate dev through its existing workflow. Do not remove installed hooks or historical evidence as part of rollback.
