# release-tagging Specification

## Purpose

Provide PR-based release preparation with synchronized Composer metadata, enforce valid stable-version succession, and create protected Git tags only after eligible release PRs merge into main.

## Requirements

### Requirement: Release branch and manifest agreement

A release PR SHALL originate in the same repository, target `main`, and use `release/vX.Y.Z` with canonical non-negative integer components and no prerelease/build suffixes. Its `composer.json` SHALL contain a string `version` exactly equal to `X.Y.Z`. The branch SHALL be the authority for the intended version; no separate `VERSION` file SHALL be required.

#### Scenario: Matching release declaration
- **WHEN** a same-repository PR to `main` uses `release/v0.1.0` and its manifest declares `"version": "0.1.0"`
- **THEN** branch and manifest agreement validation SHALL pass

#### Scenario: Missing or mismatched metadata
- **WHEN** a release PR's manifest has no `version`, a non-string value, a `v` prefix, or a value different from the branch's version
- **THEN** release validation SHALL fail with the mismatch identified

#### Scenario: Noncanonical release name
- **WHEN** a branch starting with `release/` uses `release/1.0.0`, `release/v1.2`, `release/v01.2.3`, `release/v1.2.3-beta.1`, or `release/v1.2.3+build.5`
- **THEN** release validation SHALL fail explicitly

#### Scenario: Fork cannot publish a release
- **WHEN** a release-named PR comes from a fork
- **THEN** it SHALL NOT be eligible for release publication
- **AND** its release validation SHALL report the unsupported release origin

### Requirement: Published version baseline

Version progression SHALL use the numerically greatest stable version among all remote repository tags matching `vX.Y.Z` or `X.Y.Z` in canonical form. Tag enumeration SHALL include every result page and SHALL distinguish an empty tag set from a lookup failure. Nonmatching tags SHALL NOT supply a baseline.

#### Scenario: Numeric maximum across pages
- **WHEN** remote tag pages include `v1.9.0`, `v1.10.0`, `1.8.0`, and `v2.0.0-rc.1`
- **THEN** the baseline SHALL be `1.10.0` regardless of creation date or response order

#### Scenario: Tag lookup fails
- **WHEN** remote tags cannot be fully retrieved because of an API, authentication, or network error
- **THEN** release validation SHALL fail rather than assume an initial release

### Requirement: Exact stable version progression

With no stable baseline, the first release SHALL be `0.1.0`. Given baseline `M.m.p`, the only valid next versions SHALL be `(M+1).0.0`, `M.(m+1).0`, and `M.m.(p+1)`. Version syntax alone SHALL NOT establish valid progression.

#### Scenario: Initial release
- **WHEN** no stable tag exists
- **THEN** `0.1.0` SHALL pass progression validation and every other proposed initial version SHALL fail

#### Scenario: Allowed successors
- **WHEN** the baseline is `1.0.0`
- **THEN** `1.0.1`, `1.1.0`, and `2.0.0` SHALL pass progression validation

#### Scenario: Repetition regression or skipped numbers
- **WHEN** the baseline is `1.0.0` and the candidate is `1.0.0`, `0.9.9`, `1.0.2`, `1.2.0`, `3.0.0`, `1.1.1`, or `2.1.0`
- **THEN** progression validation SHALL fail and identify the baseline and permitted successors

#### Scenario: Nonzero components and pre-1.0 versions
- **WHEN** the baseline is `0.2.7`
- **THEN** only `0.2.8`, `0.3.0`, and `1.0.0` SHALL pass progression validation

### Requirement: Shared PHP and Composer environment for development and CI

`docker/php/Dockerfile` SHALL be the shared source of PHP and Composer version declarations for development and release validation. It SHALL provide `base -> tooling -> development`, with the existing PHP reference in `base`, a single shared Composer provision in `tooling`, and `development` inheriting that stage. This refactor SHALL preserve the current version values. The `tooling` target SHALL build independently of development-only workspace arguments and SHALL exclude Xdebug and its PIE/build setup. The `development` target SHALL retain its existing Xdebug, user/workspace configuration and development behavior, and SHALL remain the target used by Compose and Dev Containers.

Both `Validate Release Branch` and `Validate Merged Release` SHALL replace `shivammathur/setup-php` with a direct build of the `tooling` target from their exact checked-out commits and SHALL execute strict Composer validation in the resulting image against that checkout. The proposed head SHA SHALL be used before merge and the integrated SHA after merge. Workflow and test configuration SHALL NOT introduce independent PHP/Composer version pins. CI SHALL NOT require local `.env` files, a running Compose service or development workspace setup. Python and GitHub CLI validation SHALL remain on the runner, and App credentials and GitHub API tokens SHALL NOT be supplied to image builds or Composer containers. The publisher SHALL preserve credential isolation and SHALL execute only release automation loaded from the executing workflow revision, as defined by the modular-authority and credential-isolation requirements below; it SHALL NOT build or run package Dockerfiles/images.

#### Scenario: Shared runtime parity
- **WHEN** the tooling and development targets are built from the same checkout
- **THEN** their actual PHP and Composer versions SHALL match the shared Dockerfile declarations and each other
- **AND** workflow/test configuration SHALL obtain its version expectations from the shared source or runtime comparison rather than independently maintained version literals

#### Scenario: CI excludes development tooling
- **WHEN** CI builds only the `tooling` target without development workspace arguments
- **THEN** the build SHALL succeed without executing the development-only PIE/Xdebug installation
- **AND** the resulting image SHALL provide PHP and Composer without loading Xdebug
- **AND** the development target SHALL retain its existing Xdebug and user/workspace behavior

#### Scenario: Proposed and integrated content use the same environment definition
- **WHEN** either read-only release-validation job runs for an eligible PR event
- **THEN** its exact proposed or integrated checkout SHALL supply both the Dockerfile build inputs and Composer validation input
- **AND** strict manifest/lock validation SHALL execute in the resulting tooling image before the release-contract helper proceeds
- **AND** the publisher SHALL continue to depend on successful integrated-content validation

#### Scenario: Image build or container validation fails
- **WHEN** the tooling image cannot be built or containerized Composer validation fails
- **THEN** the validation job SHALL fail without falling back to setup-php or a separately provisioned Composer
- **AND** dependent publication SHALL NOT proceed

### Requirement: Strict Composer manifest validation

Release validation SHALL validate the proposed and integrated Composer manifests strictly, including publishability and lock consistency where a lock file exists. It SHALL suppress only Composer's advisory about the presence of `version`. It SHALL NOT install dependencies, run package scripts, or enable Composer plugins to perform validation.

#### Scenario: Explicit version is allowed
- **WHEN** an otherwise valid manifest declares the release version
- **THEN** that declaration alone SHALL NOT cause strict Composer validation to fail

#### Scenario: Other Composer problems remain failures
- **WHEN** the manifest is invalid, has another strict validation warning, is unpublishable, or has inconsistent lock metadata
- **THEN** release validation SHALL fail

### Requirement: Required release check skips ordinary PR jobs

The PR workflow SHALL retain its `pull_request` events targeting `main` on opening, reopening, updates, and becoming ready for review, without path filtering. It SHALL retain a single validation job named `Validate Release Branch`, with one job-level condition checking only whether the source branch begins with `release/`. Ordinary PRs, including forks, SHALL skip the entire job before runner allocation. The job SHALL NOT contain an ordinary-PR echo step or repeated release-prefix conditions on its validation steps. A skipped ordinary-PR job SHALL satisfy this required check without replacing it with an absent check.

The job condition SHALL NOT filter by repository origin or canonical version syntax. All release-prefixed PRs SHALL enter validation, so release-named forks and malformed release names fail explicitly. The origin check SHALL remain the first step, before checkout, and subsequent validation steps SHALL retain normal success/failure sequencing.

#### Scenario: Ordinary PR
- **WHEN** `feature/example` opens or updates a PR to `main`
- **THEN** the entire `Validate Release Branch` job SHALL be skipped before allocating a runner or executing any step
- **AND** no tooling image SHALL be built or run for that ordinary PR event
- **AND** its skipped conclusion SHALL NOT block merge when the other branch rules are satisfied
- **AND** no release naming or version bump SHALL be required
- **AND** no release tag SHALL be created

#### Scenario: Ordinary fork PR
- **WHEN** an ordinary branch from a fork opens a PR to `main`
- **THEN** the entire release-validation job SHALL be skipped by the same job-level condition
- **AND** the unsupported-release-origin error SHALL NOT apply to that ordinary PR

#### Scenario: Invalid release still enters validation
- **WHEN** a PR to `main` has a release-prefixed branch with malformed version syntax or comes from a fork
- **THEN** the job-level condition SHALL allow the validation job to execute
- **AND** validation SHALL fail explicitly for the invalid name or unsupported origin
- **AND** a fork-origin release SHALL fail before checkout or any tooling image build

#### Scenario: Release PR update
- **WHEN** a release PR changes its manifest after an earlier successful check
- **THEN** validation SHALL run again on the updated content
- **AND** it SHALL retain the exact proposed-commit checkout and existing release validation sequence

### Requirement: Publication follows eligible merge

A release tag SHALL be created only after a same-repository release PR has merged into `main` and post-merge validation succeeds. The tag SHALL be named `vX.Y.Z` and point to the PR's integrated commit identified by `merge_commit_sha`, rather than the source branch tip or the current moving `main` tip.

#### Scenario: Eligible release is merged
- **WHEN** an eligible release PR merges and post-merge validation passes
- **THEN** the App SHALL create a lightweight tag matching the declared version at that PR's integrated commit
- **AND** squash and rebase merges SHALL use their corresponding integrated commit

#### Scenario: No eligible merge
- **WHEN** a PR is still open, is closed without merging, targets another branch, comes from a fork, or is an ordinary PR
- **THEN** the release publisher SHALL NOT create a tag for that event

### Requirement: Fresh publication checks and serialization

Release publication attempts SHALL be serialized for the repository, including fresh version checks and tag creation. Immediately before obtaining write credentials, publication SHALL revalidate release eligibility, the integrated manifest's version, and progression against current remote tags. Failed or incomplete validation SHALL prevent tag creation.

#### Scenario: Another release changes the baseline
- **WHEN** a release PR passed against `1.0.0` but another release publishes `1.1.0` before its publication attempt
- **THEN** its candidate SHALL be evaluated against `1.1.0`
- **AND** publication SHALL fail if the candidate is no longer a permitted successor

#### Scenario: Concurrent events
- **WHEN** multiple eligible merge events request publication concurrently
- **THEN** their critical publication sections SHALL NOT overlap
- **AND** a running publisher SHALL NOT be canceled by a newer request

### Requirement: Immutable release tags

The publisher SHALL create tags without updating or deleting existing references. An existing target tag SHALL cause an explicit publication failure, including on workflow retries, regardless of whether it already points to the requested commit. API failures SHALL NOT be treated as permission to overwrite a tag.

#### Scenario: Target already exists
- **WHEN** `v1.0.1` already exists and publication requests it again
- **THEN** publication SHALL fail and the existing reference SHALL remain unchanged

#### Scenario: Tag creation fails
- **WHEN** the Git API rejects or fails tag creation
- **THEN** the workflow SHALL report failure without moving any tag or automatically selecting another version

### Requirement: Modular release validation and publication authority

The inline `authority` Python implementation SHALL be extracted to `tools/release/authority.py`. The checkout-validation entry point `validate.py` and the publication-authority entry point SHALL use a single shared implementation of canonical version parsing, branch/manifest agreement, repository/base eligibility, duplicate-target rejection, stable-baseline selection, and exact version succession. Read-only GitHub API calls and complete tag enumeration SHALL also have a shared implementation. These modules SHALL use the Python standard library and the existing GitHub CLI without installing dependencies or importing package code. Shared contract evaluation SHALL accept explicit inputs without reading files, environment variables, or remote state and without producing GitHub outputs.

`validate.py` SHALL retain its existing CLI options, environment defaults, JSON success/error output and exit-status behavior, local manifest/tag-fixture support, and ordinary-branch skip behavior. Publication authority SHALL explicitly require an eligible release and SHALL NOT treat an ordinary-branch skip as successful authorization. API transports, both post-merge job conditions, the validation dependency, and existing version/publication policies SHALL remain unchanged by this refactor.

#### Scenario: Shared rules with fresh publication inputs
- **WHEN** checkout validation and publication authority evaluate release metadata
- **THEN** both entry points SHALL invoke the same shared contract implementation
- **AND** authority SHALL independently collect current remote tags within the serialized publisher instead of reusing a prior validation result or tag snapshot
- **AND** stale versions and existing target tags SHALL fail before App-token issuance

#### Scenario: Validation entry point remains compatible
- **WHEN** a caller uses the existing validation CLI or its local manifest/tag-fixture inputs
- **THEN** success/error JSON, exit statuses, and ordinary-branch handling SHALL preserve the existing behavior
- **AND** publication authority SHALL reject a non-release event rather than emit publication outputs

#### Scenario: Publication-specific checks remain mandatory
- **WHEN** authority evaluates a closed-PR event
- **THEN** it SHALL re-read and validate the PR identity, merged state, base, origin, canonical branch, and integrated SHA against the event
- **AND** it SHALL validate and decode the manifest response for that exact integrated SHA before applying the common contract to current tags
- **AND** malformed API data, incomplete tag pagination, PR/SHA mismatches, or invalid metadata SHALL prevent successful publication authority

#### Scenario: Canonical authority outputs
- **WHEN** all publication checks succeed
- **THEN** the existing step ID `authority` SHALL expose `tag=vX.Y.Z` and `sha=<verified integrated SHA>` through `GITHUB_OUTPUT`
- **AND** its script SHALL NOT create tags or request an App token
- **AND** failed authority checks SHALL emit no successful publication outputs and SHALL prevent the token and create-ref steps from running

### Requirement: Consistent release checkout names

Every checkout step in `validate-release.yml` and `create-release-tag.yml` SHALL be named exactly `Checkout repository`. This SHALL include the proposed-commit validation, integrated-commit validation, protected-tag publication automation, and GitHub Release automation checkouts. Naming and destination changes SHALL NOT change existing job names or required-check identity, action pins, conditions, dependencies, permissions, selected commits, or checkout scope. The content-validation jobs SHALL retain their full proposed/integrated checkouts; both publication jobs SHALL use standard full checkouts from `github.workflow_sha`.

#### Scenario: All three checkout labels match

- **WHEN** the two release workflows are inspected after the checkout-presentation update
- **THEN** all three original checkout steps SHALL have the exact name `Checkout repository`
- **AND** their existing PR-head, integrated-commit, and executing-workflow revision selectors SHALL remain associated with their respective jobs
- **AND** the required `Validate Release Branch` job/check name SHALL remain unchanged

#### Scenario: GitHub Release checkout matches existing labels

- **WHEN** the two release workflows are inspected after dedicated Release automation is introduced
- **THEN** all four checkout steps SHALL have the exact name `Checkout repository`
- **AND** their existing PR-head, integrated-commit, and protected-publisher executing-workflow revision selectors SHALL remain associated with their respective jobs
- **AND** the GitHub Release job SHALL also select the executing workflow revision
- **AND** the required `Validate Release Branch` job/check name SHALL remain unchanged

#### Scenario: Standard checkout configuration across jobs

- **WHEN** the four release checkout steps are configured
- **THEN** none SHALL set `sparse-checkout` or `sparse-checkout-cone-mode`
- **AND** both publication jobs SHALL retain their executing-workflow revision, default workspace and disabled credential persistence
- **AND** package files present in those full checkouts SHALL NOT be executed by publication authority or the Release coordinator

### Requirement: Publication automation has an explicit revision

The publisher SHALL load `authority.py` and its shared release-automation modules from the same repository at the exact commit identified by `github.workflow_sha`, in the default job workspace without setting the checkout action's `path` input, using a standard full checkout with persisted checkout credentials disabled. All imported release-automation modules SHALL come from that selected revision. The automation revision SHALL be selected independently of the event/API integrated SHA used to read package metadata and create the tag. Loading and execution SHALL remain inside the existing publisher concurrency group and SHALL precede App-token issuance. The authority step SHALL invoke `python3 -I -B tools/release/authority.py` from the workspace root.

#### Scenario: Automation and package revisions differ
- **WHEN** the executing workflow revision differs from the PR's integrated SHA
- **THEN** the publisher SHALL load executable automation from `github.workflow_sha`
- **AND** it SHALL read the package manifest and create the tag using the verified integrated SHA
- **AND** it SHALL NOT execute package code or API-returned content to perform publication checks

#### Scenario: Required automation is unavailable
- **WHEN** the selected automation revision or a required script/module cannot be loaded
- **THEN** the publisher SHALL fail before App-token issuance or tag creation
- **AND** it SHALL NOT fall back to a moving branch, PR head, candidate commit, previous-job artifact, another revision, or the removed inline implementation

#### Scenario: Authority executes from the default checkout destination
- **WHEN** publication automation has been loaded successfully
- **THEN** `authority.py` and its sibling modules SHALL be available under `tools/release/` in the default job workspace without a custom checkout `path`
- **AND** authority SHALL execute with `python3 -I -B tools/release/authority.py` before App-token issuance
- **AND** missing selected scripts or modules SHALL fail without falling back to a candidate checkout, another revision, or the previous `.release-automation` path

### Requirement: Release credentials remain isolated

PR validation SHALL use read-only permissions without App credentials. The publisher SHALL use a short-lived `release-bot` token generated from `RELEASE_APP_CLIENT_ID` and `RELEASE_APP_PRIVATE_KEY` after successful checks. It MAY load and execute only the release-automation scripts from the explicit workflow revision described above, with read-only normal-token permissions and persisted checkout credentials disabled. It SHALL NOT execute package code, scripts selected from the package-validation checkout, or API-returned content, install dependencies, or expose credentials in outputs or logs. Script loading and authority execution SHALL receive no App private key or installation token; the existing App-token generation step SHALL remain after successful authority checks.

Only the new `github-release` job SHALL grant its `GITHUB_TOKEN` `contents: write` for Release publication. Existing workflow-level and job-level permissions SHALL remain unchanged. The Release job SHALL use the runner's GitHub CLI and load its coordinator through the fixed workflow-revision checkout with persisted credentials disabled, without App credentials, a PAT, or new secrets. The App installation token SHALL remain exclusive to protected-tag creation.

#### Scenario: PR validation executes

- **WHEN** any PR is validated
- **THEN** the job SHALL have no App key or installation token and no repository write permission

#### Scenario: Publisher obtains credentials

- **WHEN** the publisher reaches tag creation after fresh validation
- **THEN** only the tag-creation step SHALL receive the App token with `Contents: write`
- **AND** the ordinary `GITHUB_TOKEN` SHALL retain read-only contents permission

#### Scenario: Loading and executing authority precede write credentials

- **WHEN** the publisher loads its workflow-revision scripts and executes authority
- **THEN** those steps SHALL have only the existing read-only normal-token permissions and no App credentials
- **AND** a script-loading or authority failure SHALL prevent token generation and reference creation

#### Scenario: Release job receives its own normal token

- **WHEN** the dependent Release job runs after protected-tag creation
- **THEN** only that new job SHALL use its `GITHUB_TOKEN` with `contents: write` for Release publication
- **AND** its checkout SHALL disable credential persistence and it SHALL have no App private key, App installation token, PAT, or newly introduced secret
- **AND** all existing validation and publisher permission declarations SHALL remain unchanged

### Requirement: Main and tag protections gate operational readiness

Before infrastructure activation is declared complete, `main` SHALL require PRs, zero required human approvals, and `Validate Release Branch` plus existing required CI. Workflow and ownership changes SHALL follow the same PR/check policy. Independent reviewers, mandatory CODEOWNER review, stale-approval dismissal and approval of the latest push SHALL NOT be prerequisites in this initial single-maintainer phase. Main protection SHALL retain deletion/force-push blocks and an empty bypass list. Tag protections SHALL block ordinary users/tokens from creating, updating, or deleting protected tags and allow the verified App to create release tags; existing `~ALL` tag coverage SHALL be preserved. Merge queue integration SHALL remain outside this capability's initial supported topology.

The required release check SHALL be added only after it has been emitted under its expected name and integration; an ordinary PR's skipped validation job SHALL be an acceptable emitted check. The existing required-check identity SHALL be preserved during the job-level condition revision. Verification SHALL distinguish a skipped job from an absent check caused by workflow filtering, and SHALL establish that ordinary skipped jobs do not block eligible merges while failed release jobs do. Local simulations and authenticated remote evidence SHALL be recorded separately; historical per-step validation evidence SHALL NOT be presented as verification of the revised behavior. An initial ruleset requiring PRs without required status checks SHALL be treated as partial bootstrap, not completed activation. Real publication acceptance SHALL remain separate from infrastructure activation. Completion of infrastructure setup SHALL NOT require executing a real release.

#### Scenario: Main requires PRs and successful checks
- **WHEN** a contributor attempts a direct push to `main` or a PR merge with failed required checks
- **THEN** repository protection SHALL block the update or merge

#### Scenario: Skipped ordinary check permits merge
- **WHEN** an ordinary PR has a skipped `Validate Release Branch` job and meets all other applicable branch rules
- **THEN** repository protection SHALL NOT block merge because the release-validation job was skipped
- **AND** `Validate Release Branch` SHALL remain configured as a required check

#### Scenario: Failed release check blocks merge
- **WHEN** a release-prefixed PR has a failed `Validate Release Branch` job
- **THEN** repository protection SHALL block merge through that required check

#### Scenario: Single maintainer can merge without another person's approval
- **WHEN** a maintainer's PR to `main` meets the required automatic checks and other applicable branch rules
- **THEN** protection SHALL NOT block its merge solely because another person has not approved it
- **AND** required human approvals SHALL remain zero without mandatory CODEOWNER or latest-push approval

#### Scenario: PR-only bootstrap is incomplete
- **WHEN** `Protect main` requires PRs with zero approvals but no required status checks have been configured
- **THEN** infrastructure activation SHALL remain incomplete
- **AND** the release check SHALL be required after it has been emitted under the expected name and integration, including as a skipped job for an ordinary PR

#### Scenario: Tag rules are enforced
- **WHEN** an ordinary developer or personal token attempts a protected tag mutation
- **THEN** repository protection SHALL reject it
- **AND** the authorized App SHALL be able to create a valid release tag

#### Scenario: Controls are unverified or topology is unsupported
- **WHEN** required-check/tag enforcement or the actual App installation and permissions have not been verified, or merge queue is enabled
- **THEN** infrastructure activation SHALL remain incomplete and the limitation SHALL be reported
- **AND** the absence of an independent reviewer SHALL NOT itself block the initial zero-approval policy

### Requirement: Release operation and recovery are documented

Durable contributor guidance SHALL describe preparing a release by editing `composer.json`, the initial version and successor rules, required controls, publication failures, and recovery without retagging. It SHALL distinguish Git tags from GitHub Releases and explain Packagist's VCS version discovery. Live acceptance SHALL NOT publish disposable test versions in the production release sequence. Infrastructure preparation and activation SHALL NOT imply authorization to publish a real release. Live publication acceptance SHALL belong to a separately authorized future release operation, outside infrastructure setup's completion scope. Guidance SHALL disclose actual App token issuance and live publication as unexercised until they have been verified, without claiming that infrastructure evidence proves either.

Guidance SHALL explain automatic normal GitHub Releases with tag titles and generated notes, including the first version, and their independence from the existing Packagist integration. It SHALL distinguish failed protected-tag publication from failed Release presentation, explain rerunning only the Release job after successful tag publication, and document published-Release no-op behavior, draft/prerelease conflicts, and fatal lookup errors. Release failure SHALL NOT justify changing or deleting a tag.

#### Scenario: Infrastructure advances without a release

- **WHEN** infrastructure is prepared and activated through ordinary PRs before the maintainer authorizes a real release
- **THEN** that work SHALL NOT require a production release branch or a manifest version declaration and SHALL NOT publish a tag or GitHub Release
- **AND** guidance SHALL disclose actual App token issuance and live publication as unexercised
- **AND** the absence of a real release SHALL NOT block completion of the implemented, activated, validated and documented infrastructure

#### Scenario: Release when product changes are already merged

- **WHEN** all product changes are already on `main` and a maintainer prepares the next release
- **THEN** changing `composer.json`'s version on the release branch SHALL supply the preparation diff for its PR

#### Scenario: Failed or canceled publication

- **WHEN** a merged release lacks a successfully created tag
- **THEN** guidance SHALL explain checking the integrated commit, current remote tags, and failure cause before retrying
- **AND** recovery SHALL NOT authorize moving existing tags, bypassing protections, or using a stale version

#### Scenario: Tag exists but Release publication failed

- **WHEN** the protected publisher succeeded but the Release job failed
- **THEN** guidance SHALL explain resolving the cause and rerunning only `github-release` with the original successful publisher outputs
- **AND** it SHALL explain that rerunning tag publication still rejects existing tags and is not the Release recovery procedure
- **AND** any corrective Git/GitHub operation SHALL remain subject to its separate concrete authorization

#### Scenario: Distribution remains tag based

- **WHEN** maintainers inspect release guidance after this change
- **THEN** guidance SHALL identify GitHub Releases as additional version presentation and Packagist's existing VCS integration as independent
- **AND** it SHALL describe generated notes, normal publication, and automatic source archives without prescribing additional uploaded assets

### Requirement: GitHub Release publication consumes successful tag authority

The existing post-merge workflow SHALL expose `publish` job outputs `tag` and `sha` from the unchanged `authority` step outputs. A dependent job `github-release`, named `Publish GitHub Release`, SHALL run only after successful `publish` and consume those outputs as the intended tag and integrated SHA. Existing events, eligibility, required-check names, tag-publication dependencies, and serialization SHALL remain unchanged.

#### Scenario: Protected tag publication succeeds

- **WHEN** authority validates `v0.1.0` at integrated SHA A and the publisher successfully creates that tag
- **THEN** the publisher SHALL expose `tag=v0.1.0` and `sha=A` to the dependent Release job
- **AND** the Release job SHALL use those values even when the source branch tip or current `main` points to another SHA

#### Scenario: Tag publication fails or is skipped

- **WHEN** `publish` fails, is canceled, or is skipped because validation or eligibility does not succeed
- **THEN** `github-release` SHALL NOT publish or query a Release for that attempt

#### Scenario: Existing publication guarantees remain in force

- **WHEN** the workflow gains the dependent Release job
- **THEN** `Validate Release Branch`, `Validate Merged Release`, and `Publish protected release tag` SHALL retain their identities and eligibility behavior
- **AND** the protected publisher SHALL retain its repository-wide serialization with `cancel-in-progress: false` and reject every existing target tag, including a tag already at the requested SHA
- **AND** no new publication trigger SHALL be introduced

### Requirement: GitHub Release publication verifies the remote tag

Before publishing or accepting an existing Release, the Release job SHALL confirm remotely that its exact tag exists as a lightweight reference pointing to the expected integrated SHA. Missing or invalid inputs, missing tags, unexpected reference types, mismatched SHAs, malformed responses, and lookup failures SHALL fail the job without creating or altering a Release or tag.

#### Scenario: Remote tag matches integrated commit

- **WHEN** the successful publisher outputs tag T and integrated SHA A and the remote reference for T points directly to A
- **THEN** the Release job SHALL proceed using T and A without consulting a moving branch for the version or target

#### Scenario: Remote tag is absent or different

- **WHEN** the remote tag is missing, is not the expected lightweight reference, or points to a SHA different from the publisher output
- **THEN** the Release job SHALL fail with the failed verification identified
- **AND** it SHALL NOT create a Release, repair the reference, or accept an existing Release as completion

#### Scenario: Verification inputs or API response are invalid

- **WHEN** the publisher outputs are missing or malformed, or remote reference verification encounters an authentication, network, API, or malformed-response error
- **THEN** the Release job SHALL fail before attempting Release publication

### Requirement: GitHub Releases use stable generated presentation

For a verified tag T, publication SHALL use `gh release create` with explicit `--repo`, `--verify-tag`, `--title T`, and `--generate-notes`. The Release SHALL be published normally with draft and prerelease disabled, including for `v0.1.0`. No additional assets SHALL be attached; GitHub's automatic source archives SHALL suffice. Publication SHALL NOT create a missing tag.

#### Scenario: First release presentation

- **WHEN** the verified tag is `v0.1.0` and no matching Release exists
- **THEN** publication SHALL create a normal published Release titled `v0.1.0` with GitHub-generated notes
- **AND** it SHALL use the explicit repository and existing-tag verification flags without uploading assets

#### Scenario: Subsequent release presentation

- **WHEN** another verified stable tag has no matching Release
- **THEN** publication SHALL use the same title, generated-notes, non-draft, and non-prerelease behavior
- **AND** it SHALL NOT substitute custom notes or require an earlier Release for note generation

### Requirement: GitHub Release discovery fails closed

Release discovery SHALL distinguish a successful absence result from failed queries and SHALL include matching drafts and prereleases across all result pages. Only complete, successful enumeration with no matching tag SHALL establish absence. Authentication, network, API, pagination, and malformed-response failures SHALL fail publication rather than authorize Release creation.

#### Scenario: No matching Release exists

- **WHEN** all Release pages are retrieved successfully and none contains the verified tag
- **THEN** the job SHALL treat the Release as absent and may proceed to its creation

#### Scenario: Matching Release appears on a later page

- **WHEN** a published Release, draft, or prerelease for the verified tag appears after the first page
- **THEN** discovery SHALL find it and apply the matching existing-Release behavior

#### Scenario: Release lookup fails

- **WHEN** any Release page fails with an authentication, network, API, pagination, or malformed-response error, including an HTTP 404 from the listing endpoint
- **THEN** the job SHALL fail with a diagnostic identifying discovery failure
- **AND** it SHALL NOT interpret that failure as an absent Release or attempt creation

### Requirement: GitHub Release recovery is independent and idempotent

Release failure SHALL leave all tags intact. Rerunning only `github-release` SHALL reuse successful publisher outputs and repeat remote tag verification without tag creation or progression checks. A matching normal published Release SHALL complete the job without edits. A matching draft or prerelease SHALL fail with a conflict diagnostic and remain unchanged.

#### Scenario: Existing published Release completes a retry

- **WHEN** the tag is verified and a matching non-draft, non-prerelease published Release already exists
- **THEN** the job SHALL succeed without creating another Release or editing its title, notes, or assets

#### Scenario: Conflicting draft or prerelease exists

- **WHEN** discovery finds a draft or prerelease associated with the verified tag
- **THEN** the job SHALL fail with the conflict identified
- **AND** the conflicting Release, its assets, and the tag SHALL remain unchanged

#### Scenario: Release creation fails and recovers independently

- **WHEN** tag publication succeeds but Release creation fails and only `github-release` is rerun after the cause is resolved
- **THEN** the job SHALL verify the original tag and SHA and complete Release publication if still absent
- **AND** it SHALL NOT rerun authority, version progression, App-token generation, or tag creation
- **AND** all existing tag references SHALL remain unchanged

#### Scenario: Creation succeeded remotely before the client failed

- **WHEN** a creation attempt reports failure after a matching normal Release was published remotely
- **THEN** a rerun SHALL verify the tag and accept that published Release without edits

### Requirement: GitHub Release automation has an explicit revision

The Release job SHALL load its dedicated automation from a full checkout of the same repository at `github.workflow_sha` in the default workspace with persisted credentials disabled. It SHALL execute only that coordinator with isolated Python, without package execution or dependency installation. The automation revision SHALL remain independent of the validated integrated tag target. Missing selected automation SHALL fail without fallback or Release mutation.

#### Scenario: Workflow and tag target revisions differ

- **WHEN** the executing workflow revision differs from the publisher's validated integrated SHA
- **THEN** the Release coordinator SHALL come from `github.workflow_sha`
- **AND** the verified tag, SHA, and repository environment inputs SHALL retain their existing publication meaning
- **AND** the workflow SHALL invoke `python3 -I -B tools/release/github_release.py` without embedding the coordinator in YAML

#### Scenario: Selected Release automation is unavailable

- **WHEN** checkout fails or the selected coordinator is unavailable
- **THEN** the job SHALL fail before querying or creating a Release
- **AND** it SHALL NOT fall back to another revision, candidate directory, previous path, or inline implementation
