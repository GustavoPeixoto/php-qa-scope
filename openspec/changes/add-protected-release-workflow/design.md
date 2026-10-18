## Context

See `proposal.md` for motivation, boundaries, and provisioned infrastructure. The manifest has no `version` and remote tags remain empty. Initial authenticated inspection on 2026-10-17 found no registered workflows; the two workflows have since been integrated through ordinary PR #1. Active tag ruleset `Protect releases` (ID `25208186`) still covers `~ALL` with a sole Integration bypass actor (ID `5338805`).

The maintainer created active `Protect main` (ID `25322253`) for `refs/heads/main`, with no bypass actors, a PR requirement, zero required approvals, no CODEOWNER/latest-push approval requirement, and deletion/force-push blocks. After the actual PR check passed, activation added required `Validate Release Branch` from GitHub Actions integration `15368`, with an up-to-date branch. The only collaborator is `GustavoPeixoto`; the maintainer explicitly chose an initial policy without another person's approval. Re-read live state before a real release.

The initial incompatible local draft used `VERSION` and only a post-merge job. It has been replaced locally with the two-workflow design below; keep exactly one publisher. No CODEOWNERS file is required in this initial phase.

The project uses Python standard-library automation/tests under `tools/`, root Composer metadata, and conventions indexed by `AGENTS.md`. Composer 2.10.3 in the running PHP service supports `--no-check-version`; local fixture and workflow checks have passed. GitHub CLI authentication proves repository admin access and variable/secret presence, but the App-specific installation endpoints require different credentials. The maintainer inspected authenticated settings and confirmed App `gustavopeixoto-releasebot`, ID `5338805`, installed for all account repositories with code read/write permission. Its ID matches the tag bypass. Isolated authenticated enforcement probes passed; exact receipts and their scope are recorded in `verification.md`. Actual App token issuance and real publication remain untested.

This change covers infrastructure implementation, activation, validation and its operational documentation. Completion does not require a real release. Do not create a production release branch or manifest version, and do not publish a tag or GitHub Release in this change. Actual App token issuance and end-to-end live publication remain unexercised limitations; a future real release requires separate explicit maintainer authorization and live verification outside this change.

The original 23 tasks and rollout evidence describe the completed baseline, where ordinary PRs start a runner and execute an echo step while release steps have individual conditions, and both validation workflows use `shivammathur/setup-php`. At that baseline the local Dockerfile declared PHP `8.5.10-alpine` and Composer `2.10.3`, while workflows independently requested PHP `8.5` and Composer `2.10.3`. The revised contract skips ordinary PR jobs and shares the Dockerfile's runtime between development and CI. Groups 6 and 7 in `tasks.md` track these follow-ups; current implementation and verification status is recorded there and in `verification.md`, separately from the historical checks.

## Goals / Non-Goals

**Goals:** Make the version contract testable; support a single maintainer through PRs and automatic checks; avoid allocating a validation runner for ordinary PRs; centralize PHP/Composer version declarations for development and CI without building Xdebug for release validation; keep unprivileged content validation separate from App credentials; use current publication state at tag creation; and make rollout and failures reviewable.

**Non-Goals:** Execute a production release or its live acceptance, change the package CLI or local hook runner, infer release severity from source changes, require independent human or CODEOWNER approval in this initial phase, support maintenance branches or merge queue, or automate GitHub Releases, deployment, and Packagist account setup.

## Decisions

### 1. Branch authority with a mandatory manifest copy

`release/vX.Y.Z` supplies the requested version. A release PR must set the root manifest's string `version` to exactly `X.Y.Z`, without whitespace trimming, a `v` prefix, or numeric coercion. Tags are named `vX.Y.Z`. Canonical components match `0|[1-9][0-9]*`; only ASCII digits are accepted. Reject incomplete names, leading zeros, prereleases, and build metadata.

The first release PR adds `"version": "0.1.0"`. Installing this infrastructure must not prepopulate that field on `main`: the release PR needs to supply the manifest diff. Later release PRs update the existing value. Ordinary feature PRs need no artificial version bump. Release guidance reserves version edits for release preparation; this change does not introduce an additional ordinary-PR version-change policy.

Alternative: omit `version` and infer it entirely from tags. That is Composer's usual recommendation, but it would omit the requested package metadata and the preparation diff. A separate `VERSION` file duplicates the manifest and is excluded.

### 2. Remote tags define a single release line

List every page of the GitHub repository tags API and parse canonical `vX.Y.Z` and `X.Y.Z` names into integer tuples. Choose the numeric maximum, not API order, tag date, GitHub Release status, or lexical order. Ignore names outside those forms, including prerelease/build tags. Treat incomplete pagination or API errors as failures, never as an empty history.

With no stable baseline accept only `(0, 1, 0)`. Otherwise construct the set `{(M + 1, 0, 0), (M, m + 1, 0), (M, m, p + 1)}` and require exact membership. Report the proposed version, baseline, and allowed successors on rejection. Check whether the exact target ref exists separately so duplicate-publication errors are explicit.

This deliberately excludes older maintenance-line releases once a larger stable version exists. SemVer syntax and precedence alone would permit skipped numbers; exact succession is an additional repository policy. Selecting major/minor/patch still requires human review of compatibility.

### 3. Strict Composer validation accepts the intentional version field

Use Composer from the shared `tooling` target of `docker/php/Dockerfile` in both workflow validation jobs, as described in decision 8, and run inside that container:

```sh
composer --no-plugins --no-scripts validate --strict --no-check-version
```

`--no-check-version` suppresses only the advisory recommending omission of `version`. Keep all other strict warnings, schema/publishability checks, and lock consistency checks enabled. Do not use `--no-check-publish`, `--no-check-lock`, broad warning filters, or `|| true`. Do not install dependencies. If metadata updates make the lock stale, refresh lock metadata in the release PR without dependency upgrades.

The release-specific equality check remains separate from Composer validation. A valid Composer manifest does not prove a valid release version. Composer's version-matching advisory must not be used to replace that check.

### 4. Two workflows separate PR checks from privileged publication

Create `.github/workflows/validate-release.yml` and `.github/workflows/create-release-tag.yml`; replace the conflicting local `release.yml` draft rather than leave multiple publishers enabled. Preserve unrelated user changes when applying.

The PR workflow listens on `pull_request` to `main` for `opened`, `reopened`, `synchronize`, and `ready_for_review`, without path filters. Keep the single job named `Validate Release Branch` and add `if: startsWith(github.event.pull_request.head.ref, 'release/')` at `jobs.validate`. For ordinary branches, including forks, GitHub skips the entire job before allocating a runner. The skipped job is an acceptable conclusion for the required check; it is distinct from a workflow that never emits the required check because event/path filters excluded it.

The job condition must test only the release prefix, not repository origin or the full canonical release name. Any `release/` branch enters validation, including malformed names and forks. Keep `Check release origin` as the first step so release-named forks fail before checkout; malformed release names must reach validation and fail explicitly. Remove the `Ordinary PR` echo step and all repeated release-prefix conditions from the remaining steps. Within an eligible job, steps retain normal success/failure sequencing, so an origin or Composer failure prevents subsequent validation steps from running.

Alternative: retain per-step conditions and an ordinary-PR echo. That starts a runner for a PR that needs no release validation. A second aggregation job or a composite action adds structure without serving a requirement of this revision. Use one conditional job while preserving its required-check name and integration.

Release PR validation checks out the exact PR head with persisted credentials disabled, builds the checked-out Dockerfile's `tooling` target, validates the mounted manifest and lock in that image with scripts/plugins disabled, and runs a Python standard-library helper under `tools/release/` on the runner for name/agreement/succession checks. Read remote tags with the runner's `gh` and a read-only `GITHUB_TOKEN`; the job never references App credentials. Pass event values through environment variables or structured action inputs, not directly into shell source.

The post-merge workflow listens on `pull_request` closed events targeting `main`. Both jobs gate on a merged, same-repository, release-prefixed PR. A `Validate Merged Release` job uses read-only permissions, checks out the exact `merge_commit_sha` without persisted credentials, builds that checkout's `tooling` target, and repeats content validation, including the full Composer command in the resulting image. It has no App credentials. An ordinary PR or a PR closed without merging never reaches publication.

The dependent publisher has no checkout and runs only after merged-content validation succeeds. Use workflow-owned inline validation with Python's standard library and the GitHub-hosted runner's `gh` client. Read the PR's merged state/origin/base/branch/SHA again from the API, read and parse `composer.json` at that immutable SHA through the contents API, and enumerate current tags. Repeat syntax, equality, duplicate-ref, and succession checks independently of helper outputs. The merged-content job supplies the strict Composer validation; the publisher's independent read guards against stale publication state.

Only after these read-only checks pass, generate an installation token with `actions/create-github-app-token@v3`, using the existing variable/secret, restricting it to this repository and explicitly requesting `permission-contents: write`. Give that token only to the `gh api POST .../git/refs` step. Create `refs/tags/vX.Y.Z` at the verified merged SHA. The normal workflow token remains `contents: read`. Inline publisher logic must not execute data obtained from the repository API. Use vetted immutable action SHAs, recording the corresponding action versions in comments.

The minimal publisher repeats the critical pure checks instead of importing repository scripts into a credential-bearing job. Test the helper and the actual inline publisher logic against the same fixtures so their contracts cannot drift unnoticed.

### 5. Serialization and immutable references contain races

Put the complete publisher job, including fresh reads and token creation, in one repository-wide concurrency group, with `cancel-in-progress: false`. Do not key it by version: different versions can invalidate each other's baseline. GitHub's queue behavior can replace a pending attempt; do not claim this configuration is a durable release queue. Surface canceled/pending attempts in operational guidance, and finish one release before merging another as the normal release procedure.

If another release changes the baseline between the PR check and publication, reevaluate against the new baseline and reject when no longer valid. The tag ruleset must prohibit competing ordinary writers. The create-ref API still enforces uniqueness; any duplicate or creation error is a failure. Do not PATCH refs, delete tags, choose another version automatically, or treat a matching existing tag as an implicit successful retry.

If publication fails after merge, the code remains on `main` and the tag may be absent. Inspect the requested commit, current remote state, and original failure first. Retry the existing merged-PR workflow only after a fix and only if the requested version is still valid and its tag does not exist. If the candidate became stale, prepare a new valid release PR. If a published package needs correction, publish a successor rather than move its tag. Do not add a new manual publication trigger in this change.

### 6. Protection configuration is part of activation

Verify, rather than recreate, the existing release App, Actions variable/secret, and active tag ruleset. Authenticated inspection of `Protect releases` confirms `~ALL` coverage, creation/update/deletion/non-fast-forward restrictions and a sole Integration bypass. Preserve this coverage. The logical name `release-bot` alone does not prove the provisioned App's identity; verify the actual installation and its correspondence to the configured client ID and bypass actor without exposing credentials. The App must have target repository access and contents-write permission. Tag rules must block ordinary mutations and grant the intended App the tag-rule bypass. Do not add a main-branch bypass.

For the initial single-maintainer policy, require PRs with zero required human approvals. Do not require an independent reviewer, CODEOWNER review, stale-approval dismissal or approval of the latest push. Workflow and ownership changes follow the same PR/check controls. Preserve the active main deletion/force-push restrictions and empty bypass list. The maintainer can merge their own PR once the applicable checks pass; adding an approval gate later requires an explicit policy revision.

Bootstrap the automatic check separately from creating the ruleset. `Protect main` already enforces PRs, so integrate the infrastructure through an ordinary PR, without release naming or a manifest version. Observe `Validate Release Branch` under its exact name and GitHub Actions integration before requiring it; an ordinary PR may emit it as a skipped job without allocating a runner. A missing check caused by workflow filtering is not an acceptable substitute. Preserve the already configured required check, any existing required CI and the up-to-date-branch requirement. A ruleset without required checks is only partial activation; do not claim that PR creation alone enforces the full release contract.

For this revision, verify separately that a skipped release job does not block an otherwise eligible ordinary PR and that a failed release job blocks merge. Use isolated fixtures or a disposable repository for enforcement probes without changing production protections or publishing production tags. Record local simulation and authenticated remote evidence separately; original rollout evidence covers the previous per-step design and must not be relabeled as verification of job-level skipping.

Ordinary merges are the supported initial topology. Verify merge queue is disabled before activating the required check. If it is enabled, stop activation and request a separate scope decision; do not silently add a permanently pending required check or claim `merge_group` support.

Verify remote controls and coordinated isolated enforcement probes independently of live publication. No production release or test tag is needed to prepare the infrastructure. Keep actual end-to-end publication acceptance explicitly pending until the maintainer authorizes a real release; do not treat infrastructure activation as proof that a tag has been successfully published.

### 7. Internal guidance and distribution stay in their existing boundaries

Add `conventions/releases.md`, with appropriate `when` front matter, and index it from `AGENTS.md`. Describe preparing a release from current `main`, the manifest diff, accepted successors, checks, review, App/tag controls, bootstrap, recovery, and expected Packagist discovery. The public package README remains focused on package usage. Do not add another contributor documentation hierarchy.

Add `/.github export-ignore` to `.gitattributes`; `tools/` and `conventions/` are already excluded. The package manifest remains distributed. No package runtime dependency or public CLI interface changes are needed.

### 8. Development and CI inherit one PHP/Composer tooling stage

Refactor the existing `docker/php/Dockerfile` into `base -> tooling -> development`. Keep the PHP image reference in `base` and move the existing Composer copy into `tooling`, making it the single shared Composer declaration. Preserve the current version values; this is a source-of-truth change rather than a PHP/Composer upgrade. `development` inherits `tooling` and retains its PHP development ini files, Xdebug/PIE installation, shell utilities, user identity, workspace arguments, workdir and long-running command. The shared target must build without development-only workspace arguments or Xdebug/PIE build dependencies.

Build the `tooling` target directly in `Validate Release Branch` and `Validate Merged Release`, replacing `shivammathur/setup-php` in both. Use each job's exact checkout as build context and validation input: the proposed head SHA before merge and the integrated SHA after merge. Preserve the origin check before checkout/build in PR validation. Mount the checkout at an explicit container workdir, preferably read-only for production validation, and run the unchanged strict Composer command in a disposable container. Build or container-validation failure must fail the job and prevent dependent publication, without falling back to a separately installed Composer.

The CI image does not need a separate Dockerfile or an empty `ci` stage: `tooling` is the build target. Keep Compose and Dev Containers on `development`. CI must not need local `.env` files, a running Compose service or development-only workspace setup. Python and `gh` stay on the hosted runner. The publisher continues to have no checkout, no execution of repository-supplied Dockerfiles/images, and no change to App token handling. Do not supply App credentials or GitHub API tokens to Composer containers or image builds.

Update workflow tests to check the Docker build target, exact-checkout ordering and containerized Composer command instead of `setup-php` options. Update Composer integration fixtures to run against the tooling image while retaining convenient local invocation; fixture paths must resolve inside the container. Compare actual PHP and Composer versions from tooling and development images, and verify Xdebug is absent from tooling and retained in development. Replace the independent hard-coded Composer-version assertion with checks tied to the shared source and actual runtime parity. Keep malformed-manifest, strict-warning, lock-consistency, no-package-script and no-dependency-installation fixtures.

Building the lighter target avoids Xdebug compilation in CI. Docker layer caching can reuse the shared parent layers; cached execution must still correspond to the selected checkout and Dockerfile inputs. The shared file removes independent version declarations, but upstream tags and Alpine packages remain mutable, so this change does not establish byte-for-byte image reproducibility. Retain that limitation in evidence and guidance.

Alternative: continue using `setup-php` and synchronize versions manually or parse the Dockerfile to configure it. That retains a second environment-construction path. Building the full development target avoids duplicated versions but unnecessarily installs Xdebug and requires local workspace setup. The shared tooling stage provides the needed version parity with less CI setup.

## Risks / Trade-offs

- **Explicit version can drift:** enforce exact agreement twice, using the integrated manifest for publication; do not relax unrelated Composer warnings.
- **Stale checks or concurrent events:** serialize publishers, re-read remote state under the concurrency group, use create-only refs, and document cancellation/retry behavior. A merged release can still fail to publish; there is no atomic merge-and-tag transaction.
- **Broad App contents capability:** scope the installation/token, require PRs and checks for workflow changes, generate the token late, and expose it only to create-ref. The App's tag-rule bypass is not proof that main PR/check protections are enforced.
- **No independent human approval:** this initial policy supports a single maintainer but does not guarantee another person's review of credential-bearing workflow changes. Retain PR traceability, automatic checks, isolated publication credentials and no main bypass. Requiring independent or CODEOWNER approval later is an explicit policy change.
- **Validation drift between helper and inline publisher:** use one shared fixture matrix and execute both implementations in tests with mocked API responses.
- **Strict lock validation:** retain it and fix lock metadata when necessary rather than installing/upgrading dependencies as a side effect of release validation.
- **Shared image builds and runtime parity:** Docker builds add registry/network and cache dependencies. Build only the tooling target in CI, verify actual tooling/development versions and strict Composer behavior, and fail on build/run errors. A shared Dockerfile centralizes declared versions but mutable upstream tags/packages still prevent a claim of byte-for-byte reproducibility. Treat repository Dockerfiles as executable validation inputs only in read-only jobs without publication credentials.
- **Skipped job versus missing check:** retain the workflow's events, job name and required-check integration, and avoid path filters. A job-level skip permits ordinary PRs to satisfy this check; omitting the workflow can leave it pending. Test the job's actual condition, ensure malformed and fork-origin release PRs still enter validation, and verify merge behavior separately from local simulations.
- **Live credentials/publication are unexercised:** authenticated API reads and isolated probes verified check enforcement and the relevant protections; maintainer-observed settings verified App identity/installation/permissions. These are distinct from actual App token issuance and a live publication, which remain untested. Preserve that limitation without treating a real release as unfinished infrastructure work; re-read remote state before any future authorized release.
- **Production test tags would consume versions:** use isolated fixtures or a disposable test repository for failure/concurrency probes. A future live publication is outside this change and requires separate authorization; it must use the real next release, initially `0.1.0` if no remote stable baseline exists.

## Migration Plan

1. Implement helpers, fixtures, and both workflows; remove the incompatible publisher draft. Leave `composer.json`'s version absent until the first release PR. Run local workflow and helper checks before rollout.
2. Preserve the existing `Protect main` bootstrap rules: PRs, zero approvals, no mandatory CODEOWNER/latest-push approval, deletion/force-push blocks and no bypass. Integrate the infrastructure through an ordinary PR; no release branch or manifest version is needed.
3. Observe `Validate Release Branch` under its exact name and integration on an ordinary PR, where the revised job is skipped, then require that exact check and any existing required CI with an up-to-date branch. Preserve the already activated requirement during this revision. Confirm ordinary merges and a disabled merge queue. An independent reviewer is not required for this initial policy.
4. Verify the actual App identity, installation, repository access, contents-write permission and existing tag bypass. Coordinate isolated enforcement probes proving blocked direct main pushes, failed-check merges and ordinary protected-tag mutations, together with the permitted zero-approval PR path. Preserve existing controls and publish no production test tags.
5. The original rollout and task 4.7 completed the infrastructure-only documentary alignment. Retain that historical evidence, fixture cleanup and explicit limits: actual App token issuance and live publication have not been exercised.
6. Apply group 6: move release classification to the PR job, remove the ordinary-PR echo and repeated step conditions, and update workflow tests and `conventions/releases.md`. Verify skipped ordinary jobs and failing release jobs against the retained required check, then update `verification.md` with fresh evidence and explicit limits. Run strict OpenSpec and whitespace validation and review the scoped diff. Complete the change only after the follow-up tasks are done, without publishing a version.
7. Apply group 7: extract the shared tooling stage, retain the development target and Compose contract, and replace setup-php in both read-only validation jobs. Reconcile group 6's pending workflow/tests/documentation with containerized Composer execution, build and smoke-check both targets, run strict fixtures using the tooling image, and update environment/release guidance and evidence. Keep the original 23 tasks as historical baseline work and complete both follow-up groups before archiving.

Outside this change, a later explicitly authorized real release must re-read tags and use `0.1.0` if no stable baseline exists, otherwise a permitted successor. Its live verification must check the manifest preparation diff, successful checks, App actor, exact tag/integrated SHA and unchanged prior refs. Infrastructure completion does not claim this future live acceptance occurred.

Rollback: stop future publisher runs and revert the workflow changes through reviewed commits while preserving existing controls and published tags. Do not delete or move a tag to undo a release; publish a corrective successor when needed.

## Open Questions

No relevant design questions remain. App settings evidence, original required-check activation and coordinated protection probes are recorded in `verification.md`; the original fixture has been deleted. The initial zero-approval policy, infrastructure-only completion scope, single conditional PR job and shared PHP/Composer tooling stage are settled. Groups 6 and 7 track implementation and verification, with completed work and remaining checks identified by their checkboxes and fresh evidence. Original evidence does not claim these follow-ups have passed. Future live credentials/publication verification remains outside this change.
