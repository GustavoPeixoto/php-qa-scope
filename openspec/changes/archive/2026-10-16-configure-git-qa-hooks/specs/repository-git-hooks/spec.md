# repository-git-hooks Specification Delta

## Purpose

Provide a development-environment pre-push gate and direct terminal validation of the current clean checkout, preserving Git reference policies and actionable reports while handling catchable interruption throughout the lifecycle.

## ADDED Requirements

### Requirement: Development environment enforcement
Git and manual pre-push invocations SHALL require execution in the Compose `dev` service. Missing hook runtime or required dependencies SHALL fail clearly rather than skip checks. QA-specific dependencies SHALL be required for manual validation and Git content updates, but not Git empty-update or deletion paths. This capability SHALL NOT impose a commit-environment requirement.

#### Scenario: Content push outside dev
- **WHEN** a content push invokes pre-push outside the `dev` service
- **THEN** the hook SHALL fail before QA
- **AND** it SHALL explain that the push must run in `dev`

#### Scenario: Manual validation outside dev
- **WHEN** `lefthook run pre-push` is invoked directly outside the `dev` service
- **THEN** it SHALL fail with an actionable environment diagnostic before QA
- **AND** it SHALL NOT wait for terminal input

#### Scenario: Deletion or empty update outside dev
- **WHEN** an invoked pre-push receives a deletion or no update records outside `dev`
- **THEN** the environment requirement SHALL still reject the operation

#### Scenario: Missing validation runtime
- **WHEN** QA is required but Compose, the running `php` service, Composer, development dependencies, or compatible OpenSpec 1.14.0 in dev are unavailable
- **THEN** the hook SHALL fail with an actionable runtime diagnostic
- **AND** it SHALL NOT silently skip validation

#### Scenario: Hook executable unavailable
- **WHEN** the installed hook cannot find its dispatcher or Python runtime
- **THEN** it SHALL reject the operation and identify the missing dependency

#### Scenario: OpenSpec prerequisites are exempt for Git early returns
- **WHEN** the dev gate accepts empty Git input or a single deletion
- **THEN** pre-push SHALL retain its early return without checking or running OpenSpec
- **AND** the path SHALL allocate neither a QA report directory nor check containers

### Requirement: Git and manual invocation modes
The installed pre-push launcher SHALL explicitly identify Git invocation for its child. Mode selection SHALL occur before Lefthook forwards stdin to a job. The direct command `lefthook run pre-push` SHALL validate the current checkout without requesting Git update records, waiting for terminal EOF, manufacturing outgoing references, or contacting a remote. Exactly one mode entry SHALL run, sharing the same validation/report pipeline; mode-selection predicates SHALL NOT silently skip both entries. Empty input in Git mode SHALL retain the existing no-update behavior rather than fall back to manual QA. The Git-invocation marker SHALL be scoped to the installed launcher, not the service environment file or user shell.

#### Scenario: Installed Git content invocation
- **WHEN** Git invokes the installed hook with a content update
- **THEN** the selected Git entry SHALL consume and validate Git's complete update records
- **AND** all existing branch/tag/cleanliness policies SHALL remain applicable
- **AND** the manual entry SHALL NOT also run

#### Scenario: Direct invocation in an open terminal
- **WHEN** the user runs `lefthook run pre-push` in a terminal with stdin left open
- **THEN** the manual entry SHALL proceed without reading Git records or requiring Ctrl+D
- **AND** an eligible current checkout SHALL run all seven checks and produce the normal report directory
- **AND** no reference SHALL be pushed or remote operation performed

#### Scenario: Empty Git input
- **WHEN** the installed launcher supplies Git mode and stdin reaches EOF with no records
- **THEN** the hook SHALL take the existing no-update early return after the dev gate
- **AND** it SHALL NOT run manual QA

#### Scenario: Manual detached checkout
- **WHEN** direct invocation validates a clean detached `HEAD`
- **THEN** it SHALL validate that current checkout without inferring a transmitted tag or branch
- **AND** the actual Git tag-push policy SHALL remain unchanged

### Requirement: Temporary validation runtime
Each of the six PHP validations SHALL run in its own temporary container using the existing PHP runtime's image, environment, user, working directory, and shared mounts/network. PHP script/report arguments and scopes SHALL remain unchanged. Hook execution SHALL NOT build/pull images, install dependencies, restart shared services, or create persistent QA services/resources.

The `openspec` validation SHALL run as a supervised local process in dev using its existing Node/OpenSpec installation, without a temporary container or PHP runtime modification.

#### Scenario: Eligible QA execution
- **WHEN** Git content or direct manual validation requires QA after successful pre-flight
- **THEN** each PHP validation SHALL execute directly in a distinct temporary container
- **AND** OpenSpec SHALL execute as a registered local dev process without a check container
- **AND** the current PHP image/runtime context and mounted workspace/dependencies SHALL be reused
- **AND** Lefthook SHALL remain responsible for parallel validation dispatch

#### Scenario: Early return or rejection
- **WHEN** Git input is empty, a single deletion is accepted, or pre-flight rejects either mode
- **THEN** no temporary validation container SHALL be created
- **AND** existing shared services SHALL remain unchanged

### Requirement: Complete temporary-container removal
Every current-run temporary container SHALL be explicitly removed after success, validation/report/scheduler failure, creation/start failure, or catchable interruption with reachable Docker. Containers SHALL be created without automatic removal so native state and logs remain available through collection. Ordinary completion SHALL retain an exited container only until its native completion evidence and log snapshot are collected; failure/cancellation SHALL still remove it within the shared cleanup deadline. Removal SHALL mean verified Docker absence of created, running, stopped/exited and dead containers. Containers SHALL NOT remain as debugging resources. All report/identity evidence SHALL remain retained after removal.

#### Scenario: All checks complete
- **WHEN** all seven checks finish successfully or one or more checks fail
- **THEN** every current-run temporary container SHALL be absent from Docker before completion is declared confirmed
- **AND** stopped or exited containers SHALL NOT remain as retained QA resources
- **AND** reports SHALL remain available independently of container lifetime

#### Scenario: Ordinary collection precedes removal
- **WHEN** a normally completed PHP check still needs terminal-state or log evidence
- **THEN** automatic removal SHALL be disabled and its owned exited container SHALL remain only until collection completes or fails
- **AND** explicit removal and successful absence verification SHALL occur before confirmed execution completion
- **AND** failure or cancellation SHALL NOT turn that temporary evidence window into persistent retention

#### Scenario: Container created but never started
- **WHEN** startup or identity publication fails after a container has been created
- **THEN** the created container SHALL still be removed and its absence confirmed
- **AND** no native command exit code SHALL be invented

#### Scenario: Interrupted creation response
- **WHEN** a create client is interrupted before its daemon result or container ID is recorded
- **THEN** cleanup SHALL reconcile creation and every container owned by that reserved execution/check identity
- **AND** it SHALL NOT declare absence solely because the client exited or an earlier Docker query found nothing
- **AND** late-created owned containers SHALL be removed within the shared cleanup deadline
- **AND** failed Docker reconciliation/removal SHALL follow the explicit unsuccessful-cleanup contract rather than claim absence

#### Scenario: Report processing fails after native completion
- **WHEN** native output is missing/malformed or final consolidation fails
- **THEN** container reconciliation/removal SHALL still execute
- **AND** invalid report evidence SHALL NOT cause container retention

### Requirement: Container ownership and resource isolation
Container startup and cleanup SHALL use verified current-execution ownership. Container identity SHALL be recorded before native startup. Cleanup SHALL affect only that execution's temporary containers and their own temporary resources; shared services, images, mounts, networks, pre-existing volumes, other runs, and report data SHALL remain unchanged. No global prune or prior-run recovery sweep SHALL be performed.

#### Scenario: Overlapping executions
- **WHEN** two executions validate concurrently and one completes or is cancelled
- **THEN** only that execution's owned temporary containers SHALL be removed
- **AND** the other execution's work and reports SHALL remain intact

#### Scenario: Name collision or foreign identity
- **WHEN** a reserved container name or recorded ID resolves to foreign/mismatched ownership
- **THEN** the invocation SHALL reject the operation with a diagnostic
- **AND** it SHALL NOT start, stop, or remove the foreign container

#### Scenario: Resource cleanup boundary
- **WHEN** owned temporary containers are removed
- **THEN** any anonymous volumes allocated specifically for those containers SHALL also be removed
- **AND** existing dev/php containers, shared volumes/networks, images, bind-mounted workspace data, and reports SHALL remain

### Requirement: Shared bounded container cleanup
Cancellation SHALL share one five-second graceful interval and five further seconds for forced removal/verification across local/frontend and container cleanup. Multiple checks SHALL NOT each restart that interval. Repeated received signals SHALL escalate within the same deadline. Unreachable Docker or failed removal/verification SHALL produce an unsuccessful cleanup outcome without asserting absence.

#### Scenario: Six containers need cancellation
- **WHEN** all six PHP checks have active temporary containers at interruption
- **THEN** graceful stop SHALL begin for all owned containers without sequential full grace waits
- **AND** forced cleanup/removal and absence verification SHALL fit the same ten-second invocation deadline

#### Scenario: Native work ignores graceful termination
- **WHEN** owned native work or its descendants do not exit during the graceful interval
- **THEN** cleanup SHALL force termination and complete container removal within the remaining deadline
- **AND** no owned native workload SHALL survive confirmed removal

#### Scenario: Repeated signal requests forced removal
- **WHEN** another signal is received during graceful cleanup
- **THEN** forced termination/removal SHALL be requested without a new grace interval
- **AND** cleanup SHALL remain idempotent

#### Scenario: Docker unavailable during cleanup
- **WHEN** daemon connectivity or container removal/absence verification fails
- **THEN** the invocation SHALL return nonzero within its deadline and record cleanup as unconfirmed
- **AND** an inspect/list/remove error SHALL NOT be treated as successful absence
- **AND** ownership and completed native evidence SHALL remain retained

### Requirement: Full-scope validation matrix
An eligible Git content push or manual invocation SHALL run `composer qa-scope check`, `composer sniffer-check`, `composer fixer-check`, `composer md-check`, `composer stan-check`, and `composer test` in owned temporary PHP containers with their complete configured scopes. It SHALL also run `openspec validate --all --strict --no-interactive --json` from the repository root as a supervised local dev process. All seven checks SHALL run without staged/changed-filename filtering.

#### Scenario: Eligible branch or tag update
- **WHEN** pre-push accepts a single content update for QA
- **THEN** the six PHP validations and OpenSpec SHALL run against their full declared scopes

#### Scenario: Eligible manual validation
- **WHEN** an attached or detached clean checkout is accepted for manual QA
- **THEN** all seven validations SHALL run with the same scopes and backend assignments

### Requirement: Concurrent validation collection
The seven validations SHALL run concurrently and all outcomes SHALL be collected even if a check fails. Validation, report, scheduler, or local-execution/teardown or PHP-container-cleanup failure SHALL make either mode unsuccessful. Final consolidation SHALL run after the scheduler returns or cancellation stops it, including a nonzero return. Checks SHALL NOT automatically fix or stage content. Catchable cancellation SHALL stop owned work rather than require all checks to finish normally.

#### Scenario: Early validation failure
- **WHEN** one validation fails while other validations are running
- **THEN** remaining checks SHALL continue to completion
- **AND** all outcomes SHALL be consolidated
- **AND** the push SHALL be rejected

#### Scenario: All validations pass
- **WHEN** all seven checks finish successfully with valid reports, the scheduler succeeds, and all temporary containers are confirmed removed
- **THEN** the execution SHALL succeed
- **AND** a manual invocation SHALL NOT perform or authorize a push

#### Scenario: Scheduler returns error
- **WHEN** the scheduler returns a nonzero exit code
- **THEN** final consolidation SHALL still inspect every available job result
- **AND** missing or incomplete results SHALL NOT be reported as passed
- **AND** the push SHALL be rejected

#### Scenario: OpenSpec fails while PHP checks continue
- **WHEN** OpenSpec rejects specifications or its local execution/report fails
- **THEN** Lefthook SHALL continue collecting all six PHP outcomes without fail-fast suppression
- **AND** final consolidation SHALL include all seven outcomes and reject the invocation
- **AND** OpenSpec failure SHALL NOT suppress owned PHP-container removal

### Requirement: Independent executions
Concurrent Git and manual executions SHALL NOT be blocked by an execution lock or previous-run state. Each execution SHALL own an exclusive report directory, independent validation results, and any process identity used for cancellation. One execution SHALL NOT cancel another's processes. The hook SHALL NOT create stashes, alter the index, hide changes, or perform restoration.

#### Scenario: Two simultaneous eligible pushes
- **WHEN** two pre-push invocations overlap
- **THEN** neither SHALL be rejected solely because the other is running
- **AND** each SHALL write only its own execution results

#### Scenario: Incomplete previous execution
- **WHEN** an earlier run left incomplete reports
- **THEN** their presence alone SHALL NOT block the next push
- **AND** the next run SHALL NOT overwrite them or attempt recovery

### Requirement: Effective push update classification
In Git mode, pre-push SHALL read and classify all four-field Git update records before QA. More than one effective update SHALL be rejected. Zero records or a single deletion, identified by `(delete)` and a zero local object ID, SHALL skip QA and checkout/cleanliness checks. General environment and semantic authorization rules SHALL remain applicable. Manual invocation SHALL NOT use the absence of Git records to skip QA.

#### Scenario: No updates
- **WHEN** the invoked hook receives no update records
- **THEN** it SHALL succeed after the general environment gate without requiring QA dependencies
- **AND** it SHALL NOT require a clean checkout or matching branch/tag

#### Scenario: Single deletion
- **WHEN** the only record identifies a remote-reference deletion
- **THEN** the hook SHALL skip QA, QA dependencies, and checkout/cleanliness checks
- **AND** it SHALL NOT require the reference being deleted to be checked out

#### Scenario: Multiple updates including deletions
- **WHEN** stdin contains two or more effective records, including any combination of branches, tags, and deletions
- **THEN** the hook SHALL reject the push before QA

#### Scenario: Up-to-date references omitted by Git
- **WHEN** a push command names several references but Git supplies only one effective update record
- **THEN** the hook SHALL apply the single-update policy to that record
- **AND** omitted up-to-date references SHALL NOT trigger QA

#### Scenario: Malformed record
- **WHEN** stdin contains a malformed update record
- **THEN** the hook SHALL reject the push with a classification diagnostic before QA

### Requirement: Checked-out branch push
A branch content update SHALL originate from the currently checked-out local branch and its supplied local object ID SHALL equal `HEAD`. Different source and destination branch names SHALL be allowed. Unsupported content-reference types SHALL be rejected before QA.

#### Scenario: Current branch under another remote name
- **WHEN** `feature/a` is checked out and its `HEAD` is pushed to remote branch `review/a`
- **THEN** the reference policy SHALL allow the update
- **AND** cleanliness and full QA SHALL still be required

#### Scenario: Another branch is pushed
- **WHEN** `feature/a` is checked out but the update originates from `feature/b`
- **THEN** the hook SHALL reject the push before QA even if both branches point at the same commit

#### Scenario: Supplied commit differs from checkout
- **WHEN** the branch update's supplied local object ID differs from `HEAD`
- **THEN** the hook SHALL reject the push before QA

#### Scenario: Unsupported source reference
- **WHEN** a content update cannot be identified as an allowed branch or tag source
- **THEN** the hook SHALL reject it before QA rather than infer an unrelated checkout

### Requirement: Detached tag push
A tag content update SHALL require detached `HEAD` and the transmitted tag's resolved commit to equal `HEAD`. Annotated tags SHALL be compared using their peeled commit rather than their tag object ID. Tags that cannot resolve to commits SHALL be rejected. The hook SHALL NOT change checkout automatically.

#### Scenario: Annotated tag at detached HEAD
- **WHEN** an annotated tag is pushed and its resolved commit equals detached `HEAD`
- **THEN** the tag policy SHALL allow the update despite differing tag-object and commit IDs
- **AND** cleanliness and full QA SHALL still be required

#### Scenario: Lightweight tag at detached HEAD
- **WHEN** a lightweight tag's commit equals detached `HEAD`
- **THEN** the tag policy SHALL allow the update subject to cleanliness and QA

#### Scenario: Attached branch or another commit
- **WHEN** a tag update is attempted from an attached branch or a detached checkout at another commit
- **THEN** the hook SHALL reject the push before QA

#### Scenario: Multiple tag names share one commit
- **WHEN** multiple tags resolve to the detached `HEAD` commit
- **THEN** deterministic acceptance SHALL use commit equality
- **AND** semantic guidance SHALL require explicitly checking out the intended tag

#### Scenario: Non-commit tag
- **WHEN** the transmitted tag cannot resolve to a commit
- **THEN** the hook SHALL reject the update before QA

### Requirement: Clean checkout for QA
A branch or tag content push and manual validation SHALL require an index matching `HEAD`, a tracked worktree matching the index, and no nonignored untracked files. Dirty content SHALL be rejected before QA with a suggestion to stash or resolve local changes. Ignored files SHALL NOT make the checkout dirty; the hook SHALL NOT clean it automatically. Git no-update/deletion paths SHALL retain their existing cleanliness exemption.

#### Scenario: Staged, unstaged, or untracked content
- **WHEN** a content push has staged changes, unstaged tracked changes, or nonignored untracked files
- **THEN** the hook SHALL reject it before QA
- **AND** it SHALL suggest stashing or resolving those changes without doing so automatically

#### Scenario: Only ignored output exists
- **WHEN** tracked state is clean and only ignored logs or caches exist
- **THEN** the cleanliness policy SHALL allow the content push to continue

#### Scenario: Dirty manual checkout
- **WHEN** direct manual invocation finds staged, unstaged tracked, or nonignored untracked changes
- **THEN** it SHALL reject validation before QA without changing Git state
- **AND** it SHALL explain the clean-checkout requirement

### Requirement: Execution report location and retention
Results SHALL use `logs/prepush/YYYYMMDD-HHMMSS-mmm/` with UTC timestamps and millisecond precision, without a SHA directory. Existing run directories SHALL NOT be overwritten. Every generated native report, diagnostic log, job outcome, runtime/container/creation/process record, and cancellation marker SHALL remain retained until manual cleanup after success, failure, or interruption. Container resource cleanup SHALL NOT delete that evidence. Hooks SHALL NOT perform automatic retention cleanup or success-only state deletion. The grouped layout SHALL apply only to newly allocated runs; existing flat-layout runs SHALL NOT be migrated, renamed, rewritten, or pruned.

#### Scenario: New QA execution
- **WHEN** pre-push starts a reportable execution
- **THEN** it SHALL allocate a new directory using the agreed UTC datetime
- **AND** it SHALL NOT include a commit SHA component

#### Scenario: Datetime collision
- **WHEN** a candidate datetime directory already exists
- **THEN** the hook SHALL allocate another unused valid datetime or fail clearly
- **AND** it SHALL NOT overwrite the previous results

#### Scenario: Many old executions
- **WHEN** a new hook runs while previous result directories exist
- **THEN** it SHALL retain all previous results regardless of age or count

### Requirement: Grouped execution artifact layout
Within each execution directory, the hook SHALL store native reports and diagnostics under `results/{validation-id}/`, job outcomes under `jobs/{validation-id}.json`, and PHP-container lifecycle evidence under `containers/{validation-id}/`. Supported validation IDs SHALL remain `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, `test`, and `openspec`. Every reader/writer, including cancellation, late-creation reconciliation, context validation, and exception/finalization paths, SHALL use the revised paths. Record ownership, grouped paths, atomic publication, and retention SHALL remain intact; new job/summary evidence SHALL use the backend-aware schema-4 contract.

QA Scope SHALL use `results/qa-scope/result.log`; Sniffer, Fixer, PHPMD, PHPStan, and OpenSpec SHALL use `results/{validation-id}/result.json`; PHPUnit SHALL use `results/test/result.junit.xml`. Each validation's diagnostic file SHALL be `results/{validation-id}/execution.log`. Staged native stdout, when used, SHALL be `results/{validation-id}/stdout.log`, preserving existing valid-output publication and malformed-output diagnostic handling.

A PHP validation's container directory SHALL retain `metadata.json`, `create.done.json`, `create.stdout.log`, `create.stderr.log`, and `cleanup.log` when produced. Its metadata SHALL additionally retain current-run ownership/immutable identity, separately identified client/native outcomes, selected verified terminal-state evidence, log-collection outcome and available stream byte counts, plus cleanup outcomes/errors. The scheduler log SHALL remain root `runner.log`; root summary/runtime/process/cancellation paths SHALL remain unchanged. No file or evidence of an unreached lifecycle phase SHALL be fabricated.

#### Scenario: Seven validations publish grouped artifacts
- **WHEN** Git or manual invocation completes the seven validations
- **THEN** each native report SHALL use its validation directory and native-format filename
- **AND** each diagnostic log SHALL be separate at that directory's `execution.log`
- **AND** outcome metadata SHALL be stored under `jobs/` and SHALL NOT replace a native report
- **AND** job and summary report/diagnostic references SHALL resolve relative to this run

#### Scenario: Grouped container creation and reconciliation
- **WHEN** a job reserves or creates a temporary container
- **THEN** intent, immutable identity, creation receipt, and creation/cleanup streams SHALL use that validation's `containers/` directory
- **AND** registered receipt paths and coordinator discovery SHALL agree with those paths
- **AND** cleanup SHALL distinguish ownership metadata from the creation receipt
- **AND** the existing startup gate, ownership verification, and late-creation reconciliation SHALL remain effective

#### Scenario: Interrupted directory or artifact publication
- **WHEN** SIGINT or SIGTERM arrives during creation of a grouped directory, receipt/identity publication, native-output processing, or final consolidation
- **THEN** owned work SHALL be terminated and temporary containers removed within the existing shared deadline
- **AND** completed evidence SHALL remain retained with parseable metadata where published or explicitly incomplete evidence where publication could not finish
- **AND** interrupted work SHALL NOT be reported as successful

#### Scenario: Outcome collection uses the jobs namespace
- **WHEN** the coordinator consolidates a run with native JSON reports under `results/`
- **THEN** it SHALL obtain outcome metadata from `jobs/{validation-id}.json`
- **AND** a missing, malformed, foreign, or incomplete job record SHALL fail consolidation
- **AND** a valid native report SHALL NOT be substituted for that missing outcome record

#### Scenario: Successful execution retains operational evidence
- **WHEN** every validation passes and Docker confirms complete removal
- **THEN** generated reports, diagnostic logs, job records, and operational evidence SHALL remain in the run directory until manual cleanup
- **AND** successful summary publication SHALL NOT trigger deletion of containers' evidence, process records, runtime context, or cancellation markers

#### Scenario: Failed or interrupted execution retains operational evidence
- **WHEN** a validation, startup, report, scheduler, cancellation, or cleanup path is unsuccessful
- **THEN** every generated evidence file SHALL remain retained using the revised layout
- **AND** partial or absent artifacts SHALL preserve the existing incomplete/interrupted semantics without fabricated success

#### Scenario: Existing flat-layout runs remain untouched
- **WHEN** a new execution is allocated while earlier flat-layout runs exist
- **THEN** only the new run SHALL use the grouped layout
- **AND** earlier files SHALL remain byte-for-byte unchanged regardless of the new outcome
- **AND** hooks SHALL NOT use old execution records as a recovery or cleanup registry

#### Scenario: Local OpenSpec evidence uses the grouped layout
- **WHEN** the local OpenSpec check produces output
- **THEN** its bulk JSON and diagnostics SHALL use `results/openspec/result.json` and `results/openspec/execution.log`, with `results/openspec/stdout.log` during capture
- **AND** its outcome and process evidence SHALL use `jobs/openspec.json` and `processes/local/openspec.json` when published
- **AND** it SHALL produce no `containers/openspec/` lifecycle evidence or invented Docker identity
- **AND** all generated files SHALL remain retained after success, failure, and interruption

### Requirement: Complete catchable cancellation
SIGINT/SIGTERM SHALL be handled from entry through input, pre-flight, allocation, QA, report processing, publication, and final return. The complete frontend and owned local work SHALL stop within the shared cleanup deadline, without EOF or a traceback. Owned temporary containers and native descendants SHALL be terminated and removed. Unrelated executions SHALL remain unaffected. Unconfirmed cleanup SHALL be unsuccessful. SIGKILL and Docker loss are outside catchable-signal guarantees.

#### Scenario: Cancellation before report allocation
- **WHEN** SIGINT or SIGTERM arrives during input or any pre-flight phase
- **THEN** active owned subprocesses SHALL be stopped and the invocation SHALL terminate with a nonzero status and concise cancellation diagnostic
- **AND** it SHALL NOT create fabricated QA reports or require stdin EOF to finish cancellation
- **AND** no temporary validation container SHALL be created before eligible QA allocation

#### Scenario: Cancellation during allocation or initial publication
- **WHEN** a signal arrives while creating the run directory or initial summary
- **THEN** publication SHALL remain atomic and cancellation SHALL be recorded when the allocated directory is usable
- **AND** any retained partial run SHALL remain unsuccessful or incomplete rather than passed

#### Scenario: Cancellation during QA
- **WHEN** a signal arrives while one or more validation jobs are running
- **THEN** cancellation SHALL stop the execution's scheduler, job processes, Docker clients, and native work in its temporary containers
- **AND** those containers SHALL be completely removed and their absence confirmed while Docker is reachable
- **AND** completed reports SHALL be retained and unfinished jobs SHALL NOT be marked passed
- **AND** another simultaneous execution SHALL remain unaffected

#### Scenario: Cancellation during final consolidation
- **WHEN** a signal arrives while parsing reports or publishing results/summary
- **THEN** the invocation SHALL report interruption and return nonzero
- **AND** published metadata SHALL remain parseable and SHALL NOT claim overall success
- **AND** final cleanup SHALL reconcile every owned temporary container

#### Scenario: A repeated signal during teardown
- **WHEN** a second interrupt arrives during cleanup
- **THEN** teardown SHALL remain idempotent and escalate owned-work termination and removal within the same shared deadline
- **AND** it SHALL NOT re-enter cleanup recursively or produce an uncaught traceback

#### Scenario: Direct frontend cancellation with terminal input open
- **WHEN** Ctrl+C interrupts the actual direct `lefthook run pre-push` command in a PTY
- **THEN** the npm wrapper, native dispatcher, coordinator, and owned local workers SHALL terminate within the deadline
- **AND** native work and temporary containers SHALL NOT remain after confirmed cleanup
- **AND** the terminal SHALL regain control without Ctrl+D or a persistent waiting spinner

#### Scenario: Docker-side cleanup cannot be confirmed
- **WHEN** terminating, removing, or verifying the execution's temporary containers fails
- **THEN** the invocation SHALL stop owned local processes within its deadline and report the cleanup failure
- **AND** it SHALL NOT report success or assert that unverified containers/native processes disappeared

### Requirement: Observed native container completion
Each PHP job SHALL create and register its owned container before starting Composer directly with startup attachment, TTY, stdin and automatic removal disabled. The job SHALL observe daemon container state through cancellation-aware operations and SHALL NOT infer native termination or native exit code from a Docker start/attach/exec/client return. A native code SHALL be known only after verified ownership and coherent actually-started/exited, non-running/non-restarting terminal state with start/finish evidence and an integer native exit code. Unknown/unstarted native completion SHALL retain a null code. Runtime/OOM/start errors SHALL remain explicit failures where applicable. A job SHALL NOT re-execute the tool or use fixed completion sleeps to hide an early client return.

#### Scenario: Start client returns while PHP is running
- **WHEN** the Docker start client returns zero before the owned PHP process finishes
- **THEN** the job SHALL continue observing the actual container
- **AND** it SHALL NOT parse/publish a successful report, infer native zero, or stop/remove the normally running workload merely because that client returned
- **AND** it SHALL remain cancellable without waiting for terminal EOF

#### Scenario: Native command completes with findings
- **WHEN** a verified started container exits with a nonzero native code and a valid native findings report
- **THEN** its actual native code and terminal evidence SHALL be persisted independently of client return codes
- **AND** its valid report SHALL remain retained while its job and overall invocation fail
- **AND** subsequent collection/cleanup failure SHALL NOT erase that known native code

#### Scenario: Startup or terminal observation is unknown
- **WHEN** startup fails, the container never started, daemon state cannot be verified, or state is missing/malformed/inconsistent
- **THEN** the job SHALL fail with an execution diagnostic and null native code unless genuine native completion was already independently confirmed
- **AND** cleanup SHALL reconcile and remove its owned containers without manufacturing a native result

#### Scenario: Completion metadata is spoofed or missing
- **WHEN** a PHP outcome claims success without matching run/check/immutable-ID terminal-state and collection proof
- **THEN** final consolidation SHALL reject it
- **AND** client zero, backend identity, a report file or removal evidence alone SHALL NOT enable success

### Requirement: Complete post-termination log collection
After confirmed native termination and before ordinary removal, each PHP job SHALL retrieve non-follow Docker log snapshots with separate stdout/stderr and disabled TTY. It SHALL preserve native stdout staging and diagnostics under the existing grouped paths, validate report-to-file outputs as well, and persist collection success/failure/interruption separately from native completion. A successful client return alone SHALL NOT certify an unresolved/truncated snapshot. Missing, failed, truncated or unconfirmed required output SHALL make the job unsuccessful even when genuine native exit is zero. All available evidence SHALL remain retained, and log/report failure SHALL NOT suppress explicit container removal. Production execution SHALL NOT introduce an internal PHP/shell supervisor.

#### Scenario: Successful Fixer and PHPStan stdout collection
- **WHEN** Fixer or PHPStan finishes successfully with native JSON on stdout
- **THEN** the container SHALL remain inspectable through complete snapshot collection
- **AND** stdout SHALL be staged separately from stderr and atomically published only after tool-specific validation
- **AND** job success SHALL require genuine native zero, confirmed complete collection, valid native JSON and confirmed container absence

#### Scenario: Snapshot retrieval fails or truncates
- **WHEN** native completion is known but a log client fails, returns incomplete output, or collection completeness cannot be established
- **THEN** native code/terminal evidence and available partial output SHALL remain retained
- **AND** the job SHALL fail with a collection/report diagnostic rather than pass or invent a PHP findings failure
- **AND** its owned container SHALL still be explicitly removed and absence verified

#### Scenario: Native report uses a file and diagnostics are empty
- **WHEN** Sniffer, PHPMD or PHPUnit produces a valid complete fresh native file report and its completed log snapshot has empty diagnostics
- **THEN** empty diagnostics alone SHALL NOT make it fail or imply skipped execution
- **AND** success SHALL still require verified native completion, complete collection, genuine zero and confirmed removal

#### Scenario: QA Scope report is empty or incomplete
- **WHEN** QA Scope's client reports zero but its retained stdout is empty, whitespace-only or missing expected target statuses
- **THEN** native report validity SHALL be false and the job SHALL fail
- **AND** an existing text file or one arbitrary OK line SHALL NOT enable success

#### Scenario: Arbitrary structured output replaces a native report
- **WHEN** a PHP report is parseable JSON/XML but lacks the tool's actual required result structure or coherent configured test results
- **THEN** report validation SHALL fail even with native exit zero
- **AND** malformed/inconsistent output SHALL remain retained with diagnostics

#### Scenario: Cancellation during observation or collection
- **WHEN** SIGINT or SIGTERM occurs during start acknowledgement, polling, snapshot retrieval, parsing or atomic evidence publication
- **THEN** owned work SHALL terminate and containers SHALL be removed within the existing single five-second graceful plus five-second force/verification deadline
- **AND** repeated signals SHALL escalate without resetting that deadline
- **AND** partial output and already confirmed native facts SHALL remain retained without replacing an unknown normal outcome with a cleanup-induced exit
- **AND** the invocation SHALL remain interrupted/unsuccessful and overlapping runs/shared resources SHALL remain unaffected

### Requirement: Native reports and separate diagnostics
QA Scope SHALL produce native target-status text, Sniffer/Fixer/PHPMD/PHPStan their tool-specific native JSON, PHPUnit completed native JUnit XML, and OpenSpec its defined bulk JSON. Each report SHALL be validated for its expected native fields/types and successful semantics, not merely file existence or arbitrary JSON/XML parseability. QA Scope success SHALL account for every configured managed target with the expected OK status and no missing/duplicate/conflicting target; whitespace-only output SHALL fail. Structured reports SHALL contain the tool's actual result structure, including coherent test counts for completed PHPUnit tests. Valid nonzero findings SHALL remain retained reports but SHALL NOT pass. Diagnostics SHALL stay separate from structured reports and MAY be empty after successful complete collection. Each validation SHALL record its outcome under `jobs/{validation-id}.json` and the existing grouped report/diagnostic paths.

#### Scenario: Complete output files
- **WHEN** a pre-push QA execution completes
- **THEN** QA Scope SHALL retain `results/qa-scope/result.log` and tests `results/test/result.junit.xml`
- **AND** Sniffer, Fixer, PHPMD, PHPStan, and OpenSpec SHALL retain `results/{validation-id}/result.json`
- **AND** diagnostics and per-validation outcome records SHALL remain separate from native reports

#### Scenario: Runtime fails before a structured report exists
- **WHEN** a validation cannot produce a valid native report
- **THEN** its diagnostics and report failure SHALL be retained
- **AND** the hook SHALL fail without presenting runtime text as valid JSON or XML

### Requirement: Execution summary and terminal result
Each reportable execution SHALL retain one root `summary.json` owned by the coordinator using schema version 4 and recording execution identity, mode, registered execution backends, overall outcome, all seven validation outcomes, genuine codes when known, durations, relative report/diagnostic paths using the grouped layout, and container-cleanup outcomes/errors. Interruption after allocation SHALL preserve completed evidence and distinguish unfinished/not-started work. Terminal output SHALL identify failed checks, operational/cleanup failures, and report location. Unconfirmed PHP-container removal or local teardown SHALL prevent success; OpenSpec's `not_applicable` container state SHALL never imply local-process cleanup succeeded.

#### Scenario: Multiple failed validations
- **WHEN** PHPStan and tests fail
- **THEN** the terminal SHALL name those failures and the execution's report directory
- **AND** it SHALL NOT stream complete validation output
- **AND** the final summary SHALL include all seven validation outcomes, registered backends, and applicable cleanup outcomes

#### Scenario: Job result is absent or malformed
- **WHEN** the scheduler returns but an expected job result is missing, malformed, or incomplete
- **THEN** the summary SHALL indicate an unsuccessful overall outcome
- **AND** it SHALL NOT report that check as passed
- **AND** the terminal SHALL expose the execution failure
- **AND** missing job evidence SHALL NOT suppress reconciliation/removal of current-run containers

#### Scenario: Scheduler invocation fails
- **WHEN** a report directory exists but the scheduler cannot start
- **THEN** the coordinator SHALL finalize an unsuccessful summary and preserve diagnostics
- **AND** unstarted checks SHALL NOT be reported as passed
- **AND** cleanup SHALL confirm that no temporary containers were left by that execution

#### Scenario: Native success with unconfirmed cleanup
- **WHEN** a native command exits zero with a valid report but its container removal is unconfirmed
- **THEN** its genuine native code and report SHALL remain recorded
- **AND** the invocation SHALL be unsuccessful with an explicit cleanup diagnostic

#### Scenario: Creation or interruption leaves no native exit code
- **WHEN** container creation/start fails or cancellation prevents known native completion
- **THEN** unknown native exit codes SHALL remain null
- **AND** retained cleanup/lifecycle evidence SHALL NOT manufacture successful validation or removal

### Requirement: OpenSpec repository validation
Validation ID `openspec` SHALL execute exactly `openspec validate --all --strict --no-interactive --json` in dev with repository-root cwd using the existing OpenSpec 1.14.0 pin and Node runtime. The command SHALL validate main specs and active change deltas, produce native bulk JSON separately from diagnostics, and use a genuine command exit code. Eligible-run pre-flight SHALL reject missing/incompatible OpenSpec without installation or silent skipping. Validation SHALL NOT modify artifacts, install dependencies, run in PHP, create a check container, filter by changed files, require active tasks to be complete, or include archived-task linting.

Valid OpenSpec bulk evidence SHALL use native report `version: "1.0"`, an `items` array containing change/spec IDs, boolean validity and issue lists, consistent `summary.totals` item/passed/failed counts, and a `root.path` resolving to the requested repository. A passed check SHALL have all item outcomes valid and zero failed items as well as a genuine zero exit code. Nonzero findings MAY still form a valid retained report. Native bulk report version 1.0 SHALL remain distinct from coordinator metadata schema 4.

#### Scenario: Valid main specs and active deltas
- **WHEN** main specs and active change deltas pass strict OpenSpec validation
- **THEN** the local check SHALL retain its valid bulk JSON and genuine zero exit code
- **AND** the check MAY pass subject to successful reporting and owned-local cleanup

#### Scenario: Unfinished active change
- **WHEN** an active change has valid delta specs and unchecked tasks
- **THEN** unchecked tasks alone SHALL NOT fail the OpenSpec check
- **AND** the hook SHALL NOT complete, archive, or rewrite that change

#### Scenario: Invalid specification or delta
- **WHEN** strict OpenSpec validation rejects a main spec or active delta
- **THEN** its genuine nonzero exit code and valid bulk findings SHALL remain retained
- **AND** the overall invocation SHALL fail after all seven outcomes are collected

#### Scenario: Missing or malformed bulk report
- **WHEN** the command produces absent, malformed, inconsistent, or foreign-root bulk JSON, even with exit zero
- **THEN** reporting SHALL fail with retained diagnostics rather than substitute arbitrary JSON as a valid OpenSpec report
- **AND** unknown launch/interruption codes SHALL remain null

#### Scenario: Noninteractive invocation
- **WHEN** either Git or manual QA launches OpenSpec with terminal input open
- **THEN** validation SHALL neither prompt nor wait for EOF
- **AND** its Node process and owned descendants SHALL remain registered for cancellation

### Requirement: Backend-aware job outcomes
The ordered registry SHALL retain `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, `test` as `php-container` and `openspec` as `dev-process`. Job/summary metadata SHALL retain schema 4 and backend identity verified against the registered ID. A future passed PHP outcome SHALL require matching current-run immutable container identity, persisted verified native terminal-state/code and completed-log-collection evidence, genuine zero, a valid native report and `container_cleanup: removed`. Missing/foreign/malformed/contradictory proof SHALL fail consolidation even if job metadata claims success. OpenSpec SHALL retain its genuine zero/valid bulk/local-cleanup requirements, null container ID and `not_applicable`. Only the six PHP IDs SHALL enter Docker lifecycle operations. Overall success SHALL require all seven complete successful outcomes, scheduler success and confirmed cleanup of owned local work and every PHP container.

#### Scenario: Local result has no Docker lifecycle
- **WHEN** OpenSpec passes with its registered local backend and valid evidence
- **THEN** its container identity SHALL remain null and cleanup SHALL be `not_applicable`
- **AND** the hook SHALL NOT fabricate a removed container or create container evidence for it
- **AND** container absence aggregation SHALL consider PHP jobs only

#### Scenario: Backend or container state is spoofed
- **WHEN** a PHP outcome claims `dev-process` or `not_applicable`, or an OpenSpec outcome claims a Docker ID/backend/removal
- **THEN** evidence validation SHALL reject the mismatch
- **AND** the claim SHALL NOT authorize Docker cleanup or a successful invocation

#### Scenario: Missing OpenSpec outcome
- **WHEN** the scheduler returns but OpenSpec's job record is absent, malformed, foreign, or incomplete
- **THEN** final consolidation SHALL fail with all seven expected outcomes represented
- **AND** a valid PHP/native JSON report SHALL NOT replace the missing OpenSpec evidence
- **AND** current-run PHP containers SHALL still be reconciled and removed

#### Scenario: Cancellation spans local and container work
- **WHEN** SIGINT or SIGTERM interrupts OpenSpec probing, Node startup/work, output parsing/publication, or final consolidation alongside PHP jobs
- **THEN** verified owned local groups/descendants and PHP containers SHALL terminate under the single five-second graceful plus five-second forced/verification deadline
- **AND** repeated signals SHALL escalate without extending the deadline
- **AND** completed evidence SHALL remain retained with truthful interrupted/not-started states and unknown codes null
- **AND** overlapping executions and unrelated processes/resources SHALL remain unaffected

#### Scenario: Historical metadata remains untouched
- **WHEN** future-run completion/collection proof is produced while earlier schema-4, schema-3 or flat-layout runs exist
- **THEN** old filenames, metadata, and report bytes SHALL remain unchanged
- **AND** hooks SHALL NOT migrate old runs or use them for recovery

### Requirement: Contributor hook convention ownership
`conventions/git-hooks.md` SHALL be the canonical source for Lefthook installation, pre-push policy/runtime, validation dispatch, hook automation verification, and agent response to hook failures and bypass authorization. Hook-specific sections SHALL move from `conventions/environment.md` and `conventions/git.md` into that convention without losing their existing behavior or instructions. General environment/bootstrap/local package commands SHALL remain in the environment convention; general Git operations and push authorization SHALL remain in the Git convention. Report formats, paths, ownership, and retention SHALL remain in `conventions/artifacts.md`. The convention index, documentation boundaries, and OpenSpec context map SHALL reference the new source.

#### Scenario: Hook documentation is centralized
- **WHEN** contributor hook documentation is reorganized
- **THEN** the hook dispatcher, runtime/installation, validation/result ownership, pre-push policy, and agent failure response sections SHALL reside in `conventions/git-hooks.md`
- **AND** the environment and Git conventions SHALL link to that source without duplicating the migrated rules
- **AND** general environment/Git responsibilities and canonical report documentation SHALL remain in their existing conventions

#### Scenario: Agents discover the hook convention
- **WHEN** an agent consults `AGENTS.md`, repository documentation boundaries, or OpenSpec context for work involving hooks
- **THEN** those sources SHALL direct the agent to `conventions/git-hooks.md`
- **AND** the new convention SHALL declare when it must be read for hook installation, execution, verification, troubleshooting, or bypass decisions

### Requirement: Agent response to hook failure
After any hook failure, agents SHALL inspect available diagnostics, explain actual causes and relevant file/line details, suggest corrective actions, and await a new explicit instruction. They SHALL NOT immediately fix, restage, bypass hooks, or retry.

#### Scenario: Sniffer identifies indentation error
- **WHEN** pre-push fails because Sniffer reports an indentation issue at `Foo.php:45`
- **THEN** the agent SHALL explain that cause and suggest an appropriate correction command
- **AND** it SHALL NOT execute the correction or retry the push without a new instruction

#### Scenario: Execution failure prevents reports
- **WHEN** pre-push reports a missing runtime or incomplete execution results
- **THEN** the agent SHALL explain the available diagnostic and recommend next steps
- **AND** it SHALL await a new instruction before carrying them out

### Requirement: Explicit human authorization for hook bypass
Agents MUST NOT bypass repository hooks without explicit human authorization for the specific operation.

Authorization to commit, push, fix a failure, or retry MUST NOT be interpreted as authorization to bypass hooks.

This restriction applies to `--no-verify`, `LEFTHOOK=0`, disabling hooks, and equivalent mechanisms. It SHALL apply before and after any hook failure and SHALL be documented in the `Agent Response To Hook Failure` section of `conventions/git-hooks.md`. This is an agent conduct rule; it SHALL NOT require new runtime enforcement or remove existing hook bypass mechanisms.

#### Scenario: Push authorization without bypass authorization
- **WHEN** the human authorizes a push but has not explicitly authorized bypass for that operation
- **THEN** the agent MUST NOT bypass repository hooks
- **AND** this restriction SHALL apply even if no hook has failed yet

#### Scenario: Failure correction or retry without bypass authorization
- **WHEN** a hook fails and the human instructs the agent to fix the cause or retry without explicitly authorizing bypass
- **THEN** the agent MUST NOT treat that instruction as authorization to bypass hooks
- **AND** it SHALL preserve the requirement to inspect and explain the failure before corrective actions

#### Scenario: Human explicitly authorizes a specific bypass
- **WHEN** the human explicitly authorizes bypassing hooks for a specific operation
- **THEN** the agent MAY use the authorized bypass for that operation
- **AND** it MUST NOT treat that authorization as permission to bypass hooks for another operation

### Requirement: Semantic push guidance
Contributor conventions SHALL require explicit push authorization, prefer matching local/remote branch names, require explicit tag checkout before pushing it, and describe local hook enforcement limits. Deterministic acceptance SHALL NOT constitute push authorization.

#### Scenario: Different remote branch name
- **WHEN** an authorized push uses different local and remote branch names
- **THEN** deterministic gates SHALL allow the name difference
- **AND** semantic guidance SHALL recommend matching names for ordinary pushes

#### Scenario: Technical checks pass without authorization
- **WHEN** deterministic checks pass but an agent has no authorization to push
- **THEN** the agent SHALL NOT treat hook success as permission to push

### Requirement: Contributor-only push integration
Only pre-push SHALL be installed. Setup SHALL integrate with the existing dev post-create bootstrap and support explicit reinstallation. Hook tooling SHALL remain excluded from Composer dist archives and SHALL NOT change consumer interfaces. No start/attach checks SHALL be added.

#### Scenario: Development container creation
- **WHEN** the dev container completes its post-create bootstrap
- **THEN** setup SHALL install pre-push while preserving existing bootstrap steps
- **AND** it SHALL NOT install a pre-commit hook

#### Scenario: Commit outside dev
- **WHEN** a contributor commits outside dev
- **THEN** this capability SHALL impose no commit runtime gate or QA invocation

#### Scenario: Composer dist archive
- **WHEN** a source archive is generated with repository export attributes
- **THEN** it SHALL exclude the root hook configuration and internal tooling

#### Scenario: Container restart or attachment
- **WHEN** the container restarts or an editor attaches
- **THEN** this change SHALL NOT add lifecycle checks

### Requirement: Bounded automation verification
Standard-library tests SHALL verify Git/manual policies, native/OpenSpec reporting, seven-job concurrency, registered backends, unchanged Git state, local supervision, and PHP-container lifecycle/removal. PTY tests SHALL exercise the actual npm/Node/Lefthook/Python frontend with open stdin and both signals across phases. Native Docker acceptance SHALL verify complete owned-container absence, descendant termination, overlap isolation, and truthful cleanup failure. Automation tests SHALL run explicitly outside the pre-push QA matrix.

#### Scenario: Automation implementation is verified
- **WHEN** automation is implemented or changed
- **THEN** verification SHALL cover Git policies, direct manual invocation, parallel checks, report isolation, failure consolidation, and all-phase cancellation
- **AND** it SHALL exercise interruption during creation, identity publication, startup, native execution, and removal
- **AND** it SHALL verify both running and stopped temporary containers are absent after cleanup
- **AND** it SHALL NOT affect the contributor's actual index, stash, remotes, or Docker resources

#### Scenario: Native temporary-container acceptance
- **WHEN** permitted and intentionally rejected Git/manual executions run in isolated native fixtures
- **THEN** all six PHP outcomes/reports and the real pinned OpenSpec bulk result SHALL be verified with unchanged PHP script/report arguments
- **AND** every check container SHALL be confirmed removed after completion
- **AND** interrupted native work/descendants SHALL terminate and be removed within the shared deadline
- **AND** overlapping runs, unrelated containers, existing services, shared mounts/networks, and retained reports SHALL remain unaffected

#### Scenario: Grouped artifact layout is verified
- **WHEN** the artifact-layout revision is applied
- **THEN** standard-library, actual Lefthook/PTY process fixtures, and real Docker/native acceptance SHALL verify all seven report paths/formats and job/summary references in both Git and manual modes
- **AND** success, intentional rejection, interruption, repeated signals, late creation, and overlap SHALL preserve full evidence retention and existing container-removal deadlines
- **AND** previous flat-layout runs SHALL remain unchanged
- **AND** fresh layout evidence SHALL be recorded separately from historical flat-layout acceptance

#### Scenario: Ordinary push
- **WHEN** pre-push executes its QA matrix
- **THEN** it SHALL NOT additionally run the Python automation suite

#### Scenario: Mixed-backend seven-job acceptance
- **WHEN** the OpenSpec revision is applied
- **THEN** standard-library and actual npm/Node/Lefthook/Python PTY fixtures SHALL verify local CLI availability, codes, report parsing, seven-result collection, and backend-aware schema 4
- **AND** actual OpenSpec 1.14.0 and Docker/native fixtures SHALL exercise valid and intentionally invalid specs/deltas in Git/manual modes without contributor mutations
- **AND** unfinished active tasks SHALL remain permitted, and all seven results SHALL remain retained
- **AND** both signals, repeated interruption, Node descendants, concurrent PHP work, and overlap SHALL share the bounded teardown deadline with complete owned-local/PHP-container absence
- **AND** schema-3 directories and historical evidence SHALL remain unchanged until manual cleanup
