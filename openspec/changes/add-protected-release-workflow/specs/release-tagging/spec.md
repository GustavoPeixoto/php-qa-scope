## Purpose

Provide PR-based release preparation with synchronized Composer metadata, enforce valid stable-version succession, and create protected Git tags only after eligible release PRs merge into main.

## ADDED Requirements

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

Both `Validate Release Branch` and `Validate Merged Release` SHALL replace `shivammathur/setup-php` with a direct build of the `tooling` target from their exact checked-out commits and SHALL execute strict Composer validation in the resulting image against that checkout. The proposed head SHA SHALL be used before merge and the integrated SHA after merge. Workflow and test configuration SHALL NOT introduce independent PHP/Composer version pins. CI SHALL NOT require local `.env` files, a running Compose service or development workspace setup. Python and GitHub CLI validation SHALL remain on the runner, and App credentials and GitHub API tokens SHALL NOT be supplied to image builds or Composer containers. The publisher's existing credential-isolation and no-checkout/no-repository-code-execution requirements SHALL remain unchanged.

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

### Requirement: Release credentials remain isolated

PR validation SHALL use read-only permissions without App credentials. The publisher SHALL use a short-lived `release-bot` token generated from `RELEASE_APP_CLIENT_ID` and `RELEASE_APP_PRIVATE_KEY` after successful checks. It SHALL NOT check out repository files, execute package code or checkout-supplied scripts, install dependencies, or expose credentials in outputs or logs.

#### Scenario: PR validation executes
- **WHEN** any PR is validated
- **THEN** the job SHALL have no App key or installation token and no repository write permission

#### Scenario: Publisher obtains credentials
- **WHEN** the publisher reaches tag creation after fresh validation
- **THEN** only the tag-creation step SHALL receive the App token with `Contents: write`
- **AND** the ordinary `GITHUB_TOKEN` SHALL retain read-only contents permission

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
