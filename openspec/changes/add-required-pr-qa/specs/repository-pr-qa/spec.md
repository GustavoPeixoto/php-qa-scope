# Spec Delta

## Purpose

Provide full-scope QA for every proposed GitHub integration, with shared local/CI validation behavior and an enforced merge gate on `main`.

## ADDED Requirements

### Requirement: Universal pull request QA

A dedicated GitHub Actions workflow SHALL validate pull requests to any target branch when opened, reopened, synchronized, marked ready for review, or edited to change their target branch. It SHALL include draft, fork, ordinary, release-prefixed, and documentation-only PRs without branch, path, origin, or draft-status exclusions. It SHALL use the `pull_request` event and SHALL NOT execute PR code through `pull_request_target`.

#### Scenario: Ordinary or documentation-only PR
- **WHEN** a PR is opened or updated with only documentation changes
- **THEN** all seven QA validations SHALL be scheduled without changed-file filtering

#### Scenario: Draft, fork, or release PR
- **WHEN** an eligible PR event concerns a draft, fork, or release-prefixed source branch
- **THEN** the same QA workflow SHALL run without requiring repository secrets
- **AND** existing release validation SHALL retain its separate eligibility rules

#### Scenario: Target branch changes
- **WHEN** a PR is retargeted to another branch
- **THEN** QA SHALL validate the integration with the new target branch

### Requirement: Proposed integration validation

Every validation in one QA run SHALL use the same temporary merge commit supplied by GitHub for that PR event. The workflow SHALL NOT substitute the source branch tip when the merge revision is unavailable. Inability to check out or prepare that revision SHALL prevent a successful validation job.

#### Scenario: Source passes but integration fails
- **WHEN** a PR introduces a QA failure only after integration with its target branch
- **THEN** QA SHALL report that failure against the temporary merge revision

#### Scenario: Merge revision cannot be loaded
- **WHEN** a required checkout or runtime preparation fails
- **THEN** the workflow SHALL NOT report successful required QA

### Requirement: Shared full-scope validation contract

CI and pre-push SHALL share one authoritative set of seven validation identities, command definitions, native report options, and report-validation semantics. CI SHALL run QA Scope check, PHPCS, PHP CS Fixer in dry-run mode, PHPMD, PHPStan, PHPUnit, and `openspec validate --all --strict --no-interactive --json` against their complete configured scopes. Existing Composer scripts and configuration rules SHALL remain unchanged. Checks SHALL NOT apply fixes, stage files, or select scope from changed filenames. OpenSpec SHALL validate durable specifications and active deltas, permit unfinished task checklists, and exclude archive lint.

#### Scenario: Local and CI invocation parity
- **WHEN** the seven CI validations are compared with the pre-push contract
- **THEN** validation identities, tool arguments, native report formats, and complete scopes SHALL match apart from runtime and absolute output paths

#### Scenario: Invalid report with successful tool exit
- **WHEN** a native command exits zero but its report is missing, malformed, semantically invalid, or inconsistent with the validated checkout
- **THEN** that validation SHALL fail using the same applicable report checks as pre-push

#### Scenario: Unfinished valid OpenSpec change
- **WHEN** valid active change artifacts contain unchecked implementation tasks
- **THEN** the task checklist alone SHALL NOT fail OpenSpec validation

### Requirement: Shared development and CI tooling

Development and PR QA SHALL obtain PHP and Composer from the existing PHP Dockerfile `tooling` stage and Node and OpenSpec from a new development Dockerfile `tooling` stage. Version declarations SHALL remain in these Dockerfiles rather than being independently maintained in workflow configuration. Existing version values SHALL be preserved. The development Dockerfile SHALL provide `tooling -> development`, with Corepack and the pinned OpenSpec installation inherited by `development`. Both tooling targets SHALL build without development workspace arguments, local environment files, running Compose services, or development bootstrap scripts. Locked PHP development dependencies SHALL be installed without updating the lock or ignoring platform requirements.

#### Scenario: Standalone CI build
- **WHEN** either tooling target is built from the repository root without local development configuration
- **THEN** its required runtime and package manager SHALL be available for the corresponding CI checks
- **AND** the Node tooling target SHALL provide the same OpenSpec version as development

#### Scenario: Development compatibility
- **WHEN** the dev image is built through the existing Compose or Dev Container entrypoint
- **THEN** it SHALL retain its configured user, workspace behavior, Lefthook, assistant tooling, bootstrap scripts, and OpenSpec workflow configuration
- **AND** the final default image SHALL remain the development environment

### Requirement: Optional persistent preparation caches

The workflow SHALL persist Docker tooling layers and PHP Composer package downloads in GitHub Actions caches without adding a preparation job or coupling validations. Docker cache keys SHALL distinguish format version, runner OS/architecture, tooling family, and the corresponding Dockerfile hash. Composer cache keys SHALL distinguish format version, runner OS/architecture, PHP Dockerfile, and Composer manifest/lock hashes, with fallback to earlier downloads for the same runtime. Every PHP check SHALL still install its locked development dependencies and run its native validation. The workflow SHALL NOT cache installed dependency trees, credentials, reports, or outcomes.

#### Scenario: No reusable cache exists
- **WHEN** a cache is missing, expired, or cannot be restored
- **THEN** each check SHALL build its tooling and install applicable dependencies normally
- **AND** cache restore or publication failures alone SHALL NOT fail QA or suppress its native validation

#### Scenario: Cache reuse across checks and commits
- **WHEN** a completed earlier job published a cache visible to a later check or PR execution with compatible inputs
- **THEN** that check SHALL be able to restore the corresponding layers or downloads
- **AND** an ordinary package-source change SHALL NOT change the Docker cache key
- **AND** each check SHALL retain independent build, install, report validation, and upload results

#### Scenario: Composer inputs change
- **WHEN** the Composer manifest or lock changes
- **THEN** the primary Composer cache key SHALL change
- **AND** previously downloaded packages MAY be reused while installation still follows the current lock and platform requirements

#### Scenario: Successful preparation is cached before validation
- **WHEN** a build or locked install succeeds after a cache miss
- **THEN** its prepared cache SHALL be offered for publication before native validation
- **AND** simultaneous publishers SHALL use GitHub's first-publication behavior without failing their QA jobs
- **AND** layer export SHALL replace the old exported directory only after successful construction

#### Scenario: Preparation or validation really fails
- **WHEN** tooling construction, locked installation, native validation, or required report upload fails
- **THEN** the job SHALL fail regardless of cache hits or successful cache publication

### Requirement: Independent validation execution

The seven checks SHALL execute as independent jobs or matrix entries with fail-fast disabled. One check's failure SHALL NOT suppress the remaining validations. A superseding event for the same PR MAY cancel an obsolete run, but cancellation SHALL NOT produce successful required QA. CI SHALL execute the validation contract without invoking the dev-only pre-push coordinator or requiring installation of contributor hooks.

#### Scenario: Early validation failure
- **WHEN** one check fails before the others finish
- **THEN** the other six checks SHALL still be allowed to complete and publish their available results

#### Scenario: Superseded run
- **WHEN** a new PR update cancels an earlier QA run
- **THEN** the earlier run SHALL NOT be reported as successful required QA
- **AND** QA for the new revision SHALL run independently

### Requirement: Retained CI evidence

Each validation SHALL retain its native report when produced, available stdout/stderr diagnostics, and an outcome identifying its check and validated revision. Upload SHALL be attempted after success or failure and after catchable cancellation where the runner remains available. A successful check SHALL require native success and a valid report; missing execution evidence or a failed required artifact upload SHALL prevent that job from succeeding. Available artifacts SHALL remain downloadable for the repository's configured retention period. CI evidence SHALL be separate from local pre-push evidence and SHALL NOT impersonate its container ownership or summary schema.

#### Scenario: Native findings
- **WHEN** a tool completes with findings and a valid nonzero report
- **THEN** its check SHALL fail and retain the report and diagnostics

#### Scenario: Tool never starts
- **WHEN** preparation or native startup fails before a report exists
- **THEN** available diagnostics SHALL be retained without manufacturing a successful native outcome

#### Scenario: Runner becomes unavailable
- **WHEN** runner loss prevents evidence publication
- **THEN** missing evidence SHALL NOT be interpreted as a successful check

### Requirement: Native individual required-check policy

The workflow SHALL emit seven stable `QA (<id>)` checks without an aggregate job. Main protection SHALL require each configured check to be present and completed with conclusion `success`, `skipped`, or `neutral` for the applicable revision. Any other state or conclusion SHALL block merge. Required identities SHALL be registered explicitly; future checks SHALL NOT become required automatically.

#### Scenario: Successful ordinary PR
- **WHEN** all seven individual QA checks succeed and the required release check is skipped for an ordinary PR
- **THEN** the required-check policy SHALL be satisfied subject to all other applicable protections

#### Scenario: Incomplete required checks
- **WHEN** any configured required check is missing, pending, or still running
- **THEN** the policy SHALL block merge

#### Scenario: Unsuccessful required conclusion
- **WHEN** a required check fails, is cancelled, times out, or returns a conclusion outside the explicit allowlist
- **THEN** the policy SHALL block merge

#### Scenario: Native skipped and neutral conclusions
- **WHEN** a configured required check completes with `skipped` or `neutral`
- **THEN** that conclusion SHALL satisfy its required-check condition
- **AND** it SHALL NOT be documented as proof that native validation executed

#### Scenario: New check is introduced
- **WHEN** another check is added or an existing required check is renamed
- **THEN** maintainers SHALL update the explicit protection list to require its emitted identity

### Requirement: Read-only PR execution authority

The QA workflow SHALL use a read-only GitHub token, disable persisted checkout credentials, and operate without repository secrets, App credentials, or write permissions. Neither image builds nor QA containers SHALL receive GitHub API tokens or repository credentials. This workflow SHALL NOT publish releases, push commits, or modify GitHub protections during PR execution.

#### Scenario: Fork code runs QA
- **WHEN** the workflow executes code from a fork PR
- **THEN** checks SHALL run with the same validation scope without privileged repository credentials

### Requirement: Verified required-check activation

After the seven individual QA checks have been emitted under their exact names and integration on the latest PR revision, administrators SHALL add them to the existing `main` ruleset alongside `Validate Release Branch` and all other required checks. Up-to-date enforcement, PR requirements, zero approvals, deletion/force-push protections, empty main bypass and release tag protections SHALL be preserved. Other target branches SHALL receive no new required-check rules. Missing authenticated rule or enforcement evidence SHALL leave activation incomplete.

#### Scenario: Exact required QA identities
- **WHEN** the main required-check list is updated after the emitted identities have been verified
- **THEN** it SHALL include `QA (qa-scope)`, `QA (sniffer)`, `QA (fixer)`, `QA (md)`, `QA (stan)`, `QA (test)`, and `QA (openspec)` with the observed GitHub Actions integration
- **AND** `Validate Release Branch` and every other existing required check SHALL remain required
- **AND** no aggregate context SHALL be introduced

#### Scenario: Failed QA blocks main merge
- **WHEN** any expected QA validation fails for a PR targeting `main`
- **THEN** the configured required QA check SHALL prevent merge

#### Scenario: Remote access is unavailable
- **WHEN** repository rule inspection, modification, or enforcement verification cannot be authenticated
- **THEN** the missing evidence and its consequence SHALL be recorded explicitly
- **AND** remote activation SHALL remain incomplete even if local verification passes
