---
id: artifacts
title: Artifacts Convention
when: Whenever you need to understand, create, use, move, version, reference, or distill artifacts, inputs, handoffs, drafts, `tmp/`, or sources of truth.
---

# Artifacts Convention

## Definition

Artifacts are inputs, documents, specs, conventions, decisions, handoffs, drafts, and deliverables used to carry project work.

This convention separates durable, versionable artifacts from transient artifacts. That separation prevents important decisions from depending on conversational memory, temporary files, or context outside the repository.

## Durable Artifacts

Durable artifacts are versioned sources of truth. They must contain the context needed for another person or agent to continue the work without depending on temporary files.

Examples:

- `README.md`;
- `AGENTS.md`;
- `conventions/`;
- `openspec/`;
- final documentation;
- consolidated decisions;
- OpenSpec specs, proposals, designs, and tasks.

## Transient Artifacts

Transient artifacts are supporting materials. They may guide exploration, review, and implementation, but they must not be treated as durable sources of truth.

Use `tmp/` for temporary inputs, such as:

- handoffs;
- drafts;
- exploration notes;
- dumps;
- support files;
- materials not yet distilled.

Content in `tmp/` must remain ignored by Git, except structural markers such as `tmp/.gitkeep`.

## Distilling Inputs

When a transient artifact is needed to understand scope, a decision, a requirement, a risk, or a task, distill the relevant content into a durable artifact.

References to transient files may remain as provenance, but the main understanding must live in the corresponding durable artifact.

## Use In OpenSpec Changes

Change artifacts must be self-sufficient. `proposal.md`, `design.md`, specs, and `tasks.md` must not depend on handoffs, drafts, or temporary files to be understood.

Before considering a change ready, review whether relevant transient inputs were incorporated into the applicable OpenSpec artifacts.

## Pre-push Execution Evidence

Each reportable execution exclusively allocates
`logs/prepush/YYYYMMDD-HHMMSS-mmm/`, using UTC and three millisecond digits.
Collisions retry with a new datetime or fail; existing directories are never
overwritten and names contain no SHA or suffix. Existing log ignore rules cover
these artifacts. Early pre-flight rejections, empty updates, and single deletions
do not allocate a report directory.

| Artifact | Content/owner |
| --- | --- |
| `results/qa-scope/result.log` | QA Scope native text |
| `results/sniffer/result.json` | PHPCS native JSON |
| `results/fixer/result.json` | PHP-CS-Fixer native JSON |
| `results/md/result.json` | PHPMD native JSON side report |
| `results/stan/result.json` | PHPStan native JSON |
| `results/test/result.junit.xml` | PHPUnit native JUnit XML |
| `results/openspec/result.json` | OpenSpec native bulk JSON, report version 1.0 |
| `results/{validation-id}/execution.log` | Separate Composer/runtime/native diagnostics |
| `results/{validation-id}/stdout.log` | Staged native stdout; published as the report when valid, or retained and copied into diagnostics when malformed |
| `runner.log` | Nested Lefthook output and scheduler diagnostics |
| `jobs/{validation-id}.json` | One job's atomic running/final outcome, identity, code, duration, paths, validity, and error |
| `summary.json` | Coordinator-only initial incomplete and final all-seven-result summary |
| `processes/coordinator.json` | Run-owned coordinator PID/start-time identity |
| `processes/local/{validation-id}.json` | Job identity and registered local child/session identities |
| `runtime.json` | Active template/image/project identities and unique run ownership token, without environment values |
| `containers/{validation-id}/metadata.json` | Reserved name/labels, immutable Docker ID, native lifecycle/code, and removal outcome/errors |
| `containers/{validation-id}/create.stdout.log`, `create.stderr.log` | Docker creation acknowledgement/diagnostics, separate from native report streams |
| `containers/{validation-id}/create.done.json` | Atomic settled creation-request receipt, retained even if its Lefthook job dies |
| `containers/{validation-id}/cleanup.log` | Docker stop diagnostics |
| `cancel.json`, `{validation-id}.cancel.json` | Coordinator-wide or single-job cancellation request, shared deadline, forced-cleanup flag |

Validation IDs are `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, `test`, and `openspec`.
Each validation has a separate `results/` directory; only PHP checks have `containers/`. `jobs/`
contains operational outcome metadata used for consolidation. A native JSON
report never substitutes for a job record. Job and summary report/diagnostic
references remain relative to the execution root.

This grouped layout applies to newly allocated runs. Older flat-layout runs stay
unchanged: hooks never migrate, rename, rewrite, or prune their files. Runtime,
process, and cancellation paths remain unchanged. Staged stdout
keeps its existing atomic report-publication and malformed-output handling;
interrupted partial stdout remains where capture stopped.
Metadata paths are relative to the execution directory. Structured primary reports
must parse; invalid stdout is retained in diagnostics rather than published as JSON.
A valid report can accompany a failed command. Missing, malformed, foreign, or
incomplete job evidence and scheduler failures always make the summary unsuccessful.
The summary records schema version 4, execution ID, hook, invocation mode
(`git` or `manual`), UTC start/end, overall
status/code, Lefthook code, operational errors, all seven ordered outcomes, and
container cleanup outcome. Job records include container ID and cleanup state.
Only `removed` cleanup can accompany a passed PHP validation; `not_created` describes
unstarted work, and `pending`/`unconfirmed` never enable success.

Job states are `running`, `passed`, `failed`, `interrupted`, and `not_run`.
Final summaries distinguish unfinished started jobs from jobs never started and
retain completed valid outcomes. Unknown command/scheduler exit codes stay null;
they are never fabricated from the interruption signal. Interruption cannot
publish a successful overall outcome. Metadata and results are replaced atomically
in the same directory; signals defer through small atomic writes, then enter cleanup.

Retain every generated report, diagnostic log, job outcome, container metadata,
creation receipt/stream, runtime/process identity, and cancellation marker until
manual cleanup, including successful runs. Evidence files remain after Docker
removal; there is no success-only state deletion, debug-only retention, or automatic
retirement of operational metadata. Setup and hooks never prune reports or
inspect old runs for recovery. An interrupted run may remain incomplete; it cannot
be treated as passed and does not block a later independent execution. Catchable
signals trigger lifecycle-wide local/frontend and temporary-container teardown and final
reporting, with one five-second graceful plus five-second forced/verification
deadline. Repeated received signals escalate without extending it. Cleanup uses
local PID/session/start-time identities and verified Docker container ownership.
It reconciles creation/start races and confirms no current-run created/running/
stopped/dead objects remain, which also ends their native descendants.
Stopping a Docker client alone or leaving a stopped container is not confirmation.
Unconfirmed removal is recorded as a cleanup failure. Before allocation,
cancellation produces only a concise nonzero diagnostic. SIGKILL or container loss
can prevent finalization. Process metadata stays ignored and run-local and is
never used to repair old executions or signal another run. Temporary containers
are removed after every success/failure/interruption path independently of report
retention. Identity/receipt/result files remain as evidence after Docker objects
are removed; hooks never retain stopped containers for debugging or prune shared
services, images, networks, mounts, existing volumes, or old reports.

Schema 4 requires the registry's `execution_backend` in every job and summary
outcome: `php-container` for the six PHP checks and `dev-process` for OpenSpec.
OpenSpec always has null `container_id` and `container_cleanup: not_applicable`;
it has no `containers/openspec/`, fake Docker state, receipt, or removal evidence.
Container cleanup aggregation covers only PHP checks. Overall success still
requires all seven valid successful outcomes, successful local cleanup, and a
successful scheduler. Backend/cleanup/identity spoofing cannot enable success.

OpenSpec captures `results/openspec/stdout.log`, atomically publishes validated
bulk JSON as `results/openspec/result.json`, and retains diagnostics in
`results/openspec/execution.log`. Invalid/interrupted stdout remains available.
Its job is `jobs/openspec.json`, process ownership is
`processes/local/openspec.json`, and `openspec.cancel.json` is retained when produced.
The native report version `1.0` is distinct from metadata schema 4: it requires
change/spec items, boolean validity, issue lists, consistent item/passed/failed
totals, and the requested repository root. Valid findings remain a retained report
even when the CLI exits nonzero. Unknown launch/interruption codes stay null.
All generated files remain on every outcome until manual cleanup. Schema-3 and
older flat runs remain untouched, without migration or recovery sweeps.

Future PHP-container metadata also retains `native_completion`, selected
`terminal_state` (status/running/restarting/start/finish/native code/OOM/error),
separate `start_client_exit_code`, `log_collection` and available stdout/stderr
byte counts. Persist terminal proof before collecting logs or removing the object.
Native completion is `pending`, `confirmed` or `unknown`; collection is `pending`,
`complete`, `failed` or `interrupted`. Consolidation cross-checks current-run,
validation and immutable container identity and the job's genuine native code.
Missing, foreign, malformed or contradictory proof cannot enable a passed PHP job.
Keep summary schema 4 and all existing filenames; old schema-4 runs are untouched.

Collect non-follow stdout/stderr snapshots after verified native termination and
before normal explicit removal. Stage stdout separately for every PHP check;
report-to-file checks retain that stream and copy console output into diagnostics.
Correctly empty diagnostics are allowed after confirmed complete collection.
Missing/truncated reports, arbitrary JSON/XML, empty/incomplete QA Scope target
statuses and inconsistent native results fail. JUnit must contain actual completed
test cases and coherent counts. Valid nonzero findings remain report evidence.
Unknown completion keeps a null native code; a known code remains retained through
later collection/report/removal failure. Cancellation preserves partial streams
and confirmed facts without using cleanup-induced exit as an unknown tool result.
All generated files survive success, failure and interruption until manual cleanup;
containers are removed explicitly after collection or on failure/cancellation.
