# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
