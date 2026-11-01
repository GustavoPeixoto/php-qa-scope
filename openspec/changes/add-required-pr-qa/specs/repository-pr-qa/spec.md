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

Every validation in one QA run SHALL use the same temporary merge commit supplied by GitHub for that PR event. The workflow SHALL NOT substitute the source branch tip when the merge revision is unavailable. Inability to check out or prepare that revision SHALL prevent a successful aggregate check.

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

Each validation SHALL retain its native report when produced, available stdout/stderr diagnostics, and an outcome identifying its check and validated revision. Upload SHALL be attempted after success or failure and after catchable cancellation where the runner remains available. A successful check SHALL require native success and a valid report; missing execution evidence or a failed required artifact upload SHALL prevent aggregate success. Available artifacts SHALL remain downloadable for the repository's configured retention period. CI evidence SHALL be separate from local pre-push evidence and SHALL NOT impersonate its container ownership or summary schema.

#### Scenario: Native findings
- **WHEN** a tool completes with findings and a valid nonzero report
- **THEN** its check SHALL fail and retain the report and diagnostics

#### Scenario: Tool never starts
- **WHEN** preparation or native startup fails before a report exists
- **THEN** available diagnostics SHALL be retained without manufacturing a successful native outcome

#### Scenario: Runner becomes unavailable
- **WHEN** runner loss prevents evidence publication
- **THEN** missing evidence SHALL NOT be interpreted as a successful check

### Requirement: Stable required QA result

The workflow SHALL emit a stable aggregate job/check named `QA Required`. It SHALL succeed only if all seven expected checks completed successfully and their current-revision evidence is present and valid. Failed, cancelled, skipped, missing, duplicate, unknown, or foreign-revision check outcomes SHALL NOT satisfy the gate. Aggregation SHALL be attempted after upstream failure when GitHub still permits the job to execute.

#### Scenario: All checks pass
- **WHEN** exactly the seven expected checks succeed with valid evidence for the same merge revision
- **THEN** `QA Required` SHALL succeed

#### Scenario: Incomplete or unsuccessful validation set
- **WHEN** any expected check fails, is cancelled or skipped, or has no valid current-revision outcome
- **THEN** `QA Required` SHALL NOT succeed

#### Scenario: Evidence set is inconsistent
- **WHEN** uploaded outcomes include duplicate or unexpected identities, or evidence for another revision
- **THEN** the aggregate gate SHALL fail

### Requirement: Read-only PR execution authority

The QA workflow SHALL use a read-only GitHub token, disable persisted checkout credentials, and operate without repository secrets, App credentials, or write permissions. Neither image builds nor QA containers SHALL receive GitHub API tokens or repository credentials. This workflow SHALL NOT publish releases, push commits, or modify GitHub protections during PR execution.

#### Scenario: Fork code runs QA
- **WHEN** the workflow executes code from a fork PR
- **THEN** checks SHALL run with the same validation scope without privileged repository credentials

### Requirement: Verified required-check activation

After `QA Required` has been emitted by GitHub Actions under its exact name and integration, repository administrators SHALL add it to the existing `main` ruleset alongside `Validate Release Branch` and any other required checks. Existing up-to-date-branch enforcement, PR requirements, zero required approvals, deletion/force-push protections, empty main bypass list, and release tag protections SHALL be preserved. Other target branches SHALL receive QA execution without new required-check rules from this change. Activation SHALL remain incomplete until dated authenticated remote evidence establishes the updated rule and blocking behavior; local tests SHALL NOT substitute for that evidence.

#### Scenario: Successful ordinary PR
- **WHEN** an ordinary PR has successful `QA Required`, a skipped emitted `Validate Release Branch`, and satisfies other applicable rules
- **THEN** the QA and release-check requirements SHALL permit merge without a required human approval

#### Scenario: Failed QA blocks main merge
- **WHEN** any expected QA validation fails for a PR targeting `main`
- **THEN** the configured required QA check SHALL prevent merge

#### Scenario: Remote access is unavailable
- **WHEN** repository rule inspection, modification, or enforcement verification cannot be authenticated
- **THEN** the missing evidence and its consequence SHALL be recorded explicitly
- **AND** remote activation SHALL remain incomplete even if local verification passes
