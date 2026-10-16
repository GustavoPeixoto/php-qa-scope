---
id: git-hooks
title: Git Hooks Convention
when: Whenever installing, configuring, executing, verifying, troubleshooting, documenting, or deciding whether to bypass repository Git hooks.
---

# Git Hooks Convention

This convention owns contributor Git hook setup, pre-push policies and validation,
hook automation verification, and agent failure/bypass behavior. General Git
operations belong in [conventions/git.md](git.md), environment/bootstrap/local
package commands in [conventions/environment.md](environment.md), and canonical
report formats and retention in [conventions/artifacts.md](artifacts.md).

## Pre-push Policy

Run authorized pushes from the Compose `dev` service. Commits have no hook-specific
environment or QA requirement. Lefthook installs only `pre-push`; its custom
`qa-checks` group runs six full-scope PHP checks and OpenSpec concurrently.

The hook reads effective updates supplied by Git, rather than counting command
refspecs or commits. Every invoked path requires dev, including these early exits:

| Effective updates | Policy |
| --- | --- |
| None | Skip QA and checkout checks. |
| One deletion | Skip QA and checkout checks, regardless of current checkout. |
| More than one, including deletions | Reject before QA; push one reference at a time. |
| One branch | Source must be the checked-out branch, supplied OID must equal HEAD, and checkout must be clean. |
| One tag | Explicitly check out the intended tag with detached HEAD; its peeled commit must equal HEAD and checkout must be clean. |
| Malformed or unsupported reference | Reject before QA. |

Prefer matching local/remote branch names for ordinary pushes. A different remote
branch name is technically allowed. Another source branch at the same commit is
rejected. Symbolic HEAD can identify the current branch; raw object sources cannot.
Annotated tags are compared by their peeled commit. Git cannot prove which tag name
was checked out when several names resolve to one commit, so explicit intended-tag
checkout remains a contributor obligation.

Content pushes require an index matching HEAD, a tracked worktree matching the
index, and no nonignored untracked files. Ignored logs/caches are allowed. Suggest
manual stashing or explicit resolution when dirty; hooks never stash, clean, change
checkout, stage, or restore content. Avoid editing the checkout while QA runs.
Overlapping pushes may compete for resources; each receives its own reports.

For manual validation from dev, run exactly:

```sh
lefthook run pre-push
```

This mode validates an existing clean checkout, attached or detached, with the
same seven checks and dependency requirements. It does not read Git update records,
wait for terminal EOF, manufacture references, or contact a remote. Dirty or
unborn checkouts reject before report allocation. Git's empty/deletion early
returns apply only to Git mode.

Local launchers and the dev marker are contributor guardrails. Passing technical
checks does not authorize a push or bypass the explicit authorization rule in
[conventions/git.md](git.md).

## Agent Response To Hook Failure

Agents MUST NOT bypass repository hooks without explicit human authorization for the specific operation.

Authorization to commit, push, fix a failure, or retry MUST NOT be interpreted as authorization to bypass hooks.

This restriction applies to `--no-verify`, `LEFTHOOK=0`, disabling hooks, and equivalent mechanisms.

The bypass prohibition applies before and after any hook failure. Explicit human
authorization is limited to the specific operation; it does not authorize bypass
for another operation or follow from a general instruction to complete the work.

After an actual repository hook failure, inspect the available summary, native
reports, and diagnostics. Explain the actual cause and relevant file/line details,
recommend remedies, and await a new explicit instruction before fixing, restaging,
bypassing hooks, or retrying the push. Do not execute suggested corrections
immediately. Controlled intentional failures in isolated automation tests are test
fixtures, not instructions to repair contributor content.

For example, if Sniffer reports indentation at `Foo.php:45`, explain that location
and suggest reviewing it or running `composer sniffer-fix`; await authorization
before executing the command or retrying. If the php service is missing, explain
the runtime diagnostic and recommend starting it; await instruction before doing so.

## Git Hook Dispatcher

The dev image installs the official `lefthook@2.1.16` npm package through its
existing Yarn after `corepack enable`. Installation-scoped `CI=1` suppresses
the package's automatic hook installation; `setup-git-hooks` owns activation.
This scoped installation flag controls package postinstall behavior; it does not
authorize bypassing repository hooks during a Git operation.
The npm command requires the existing Node runtime and its package files, with
version-matched optional dependencies selecting the platform binary. Yarn/package
metadata handles integrity in place of hardcoded GitHub asset checksums. The build
and setup both verify the exact version. Rebuild/recreate the dev container after
changing this pin or introducing hook setup. Verify with
`lefthook version` inside dev. Ordinary local Composer commands and commits
remain available outside dev; pushes use the dev runtime described below.

Hook automation uses Python's standard library. Run its tests explicitly after
automation changes, outside the pre-push PHP QA matrix:

```sh
PYTHONPATH=tools python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py'
```

The integration tests require the pinned command on PATH or
`QA_HOOKS_TEST_LEFTHOOK=/absolute/path/to/lefthook`. Missing commands skip those
integration cases, so supply one for complete verification. Fixtures link to the
installed command instead of copying its Node wrapper, preserving the package
layout. Node must remain available, including when testing missing Python.
Tests use temporary Git repositories and standard-library fixtures, with synchronization barriers to
verify actual Lefthook concurrency. PTY tests exercise the actual npm/Node/native
frontend with stdin left open, both signals across lifecycle phases, atomic
publication, repeated interruption, and overlapping runs. Instrumentation exists
only in disposable committed fixtures. They never use contributor index/stash/remotes.

For full native acceptance from an active dev environment with dev/php services
and Docker available, run the same command with `QA_HOOKS_NATIVE_ACCEPTANCE=1`.
To verify a rebuilt dev image before recreating the active environment, supply
`QA_HOOKS_NATIVE_DEV_IMAGE=<image>` with the npm package and Docker/Compose feature
installed. Acceptance verifies the npm wrapper and its platform package inside
that image; it never mounts a replacement standalone dispatcher.
It creates separate disposable Compose services and a local bare remote, verifies
a successful push, attached/detached manual validation, intentional QA Scope
rejection, and real native PHP cancellation with descendant/overlap/unrelated
process checks. It compares remote references after manual runs and tears down
its own services. It mounts the existing dev dependency tree read-only and retains native
evidence in `tmp/git-hooks-verification/native-reports/`. This opt-in test is also
outside the pre-push matrix.

## Pre-push Runtime And Installation

Push from dev with `QA_HOOKS_SERVICE=dev` and a container runtime indicator.
The required marker is declared in `docker/dev/.env.example` and supplied through
the local `docker/dev/.env`, which Compose loads with the dev service's `env_file`.
For content updates, pre-flight requires Docker Compose access, the
running php service, Composer, installed development dependencies, OpenSpec 1.14.0 in dev, and all native
QA configurations. Hooks never start services or install dependencies. Empty
updates and one deletion skip QA-specific prerequisites after the dev gate.
The running php container supplies the active immutable image, environment, user,
working directory, existing networks, and workspace/dependency mounts. Docker
create/start/inspect/logs/stop/remove/query support and Docker-managed init are
required. Temporary check containers are created without automatic removal. Checks reuse that runtime without builds or pulls; the shared php service
continues running and is used for dependency probes.
Ordinary package commands can still run locally as described in
[conventions/environment.md](environment.md); commits have no dev gate. See
[Pre-push Policy](#pre-push-policy) for checkout policies and
[conventions/git.md](git.md) for general push authorization.

For a fresh environment, `make env-dev` creates the missing local file from the
example, including the marker. Existing `.env` files are left untouched: add or
update only this assignment in `docker/dev/.env`, preserving other local values:

```dotenv
QA_HOOKS_SERVICE=dev
```

Recreate dev through the Dev Container workflow to apply changed env-file values;
restarting an existing container does not reload them. A missing or incorrect
marker rejects invoked pushes, including empty updates and deletions. Hooks and
bootstrap do not automatically rewrite existing env files or recreate containers.

Rebuild/recreate dev after introducing the dispatcher or changing its pin. The
existing post-create chain runs `setup-git-hooks` after Codex context/Headroom setup.
Explicit installation/reinstallation from the repository root in dev is:

```sh
setup-git-hooks
```

Setup is idempotent, installs only pre-push, honors existing `core.hooksPath`,
preserves unrelated hooks, and rejects unmanaged pre-push conflicts. The generated
Lefthook launcher bears `# php-qa-scope managed pre-push launcher`. It forwards
remote name/location through `QA_HOOKS_REMOTE_NAME` and `QA_HOOKS_REMOTE_LOCATION`
without shell interpolation, and scopes `QA_HOOKS_GIT_PUSH=1` to the child
invocation. Lefthook selects exactly one entry before stdin forwarding: the Git
entry uses `use_stdin`, and the manual entry uses interactive terminal I/O without
Git-record reads. Invalid launcher context rejects clearly.
Existing launchers MUST be explicitly reinstalled with `setup-git-hooks` after
this routing revision; updating repository files alone does not add the marker.
Agents do not automatically install/reinstall contributor hooks during verification.
Missing dispatcher/Python fails the hook. No start/attach lifecycle checks are
introduced, and existing Headroom startup remains unchanged.

For an authorized rollback, resolve the active hook path with
`git rev-parse --git-path hooks/pre-push`, verify that ownership marker, and remove
only the owned pre-push launcher. Retain logs and unrelated hooks/hook-path settings.
Reverting versioned configuration alone does not remove an installed launcher.

## Pre-push Validation And Result Ownership

The coordinator runs one `lefthook run qa-checks`; Lefthook owns parallelism and
waits for all seven jobs even on failure. The custom group is not an installed hook
and never invokes pre-push recursively. Each PHP job synchronously invokes
`composer --no-interaction --no-ansi` directly in an owned temporary container with script
forwarding through `--`, preserving complete configured scope:

| Composer invocation | Forwarded report options |
| --- | --- |
| `qa-scope -- check` | Native stdout text |
| `sniffer-check` | `--report=json --report-file=<path> --no-colors -q` |
| `fixer-check` | `--format=json --no-ansi --show-progress=none` |
| `md-check` | `--reportfile-json <path>` |
| `stan-check` | `--error-format=json --no-progress --no-ansi` |
| `test` | `--log-junit <path> --colors=never` |

Composer scripts are unchanged: Fixer keeps dry-run/diff, PHPMD keeps its text
renderer and `src,tests,bin`, and native configurations retain scope/rule policy.
No job filters filenames or runs correction/staging commands.

Jobs require the allocated absolute `QA_HOOKS_RUN_DIR` under this checkout's
`logs/prepush/` and matching `QA_HOOKS_EXECUTION_ID`. Direct custom-group execution
without valid context fails. Only each job writes its own result; only the
coordinator writes the summary after the scheduler returns, including nonzero or
launch-failure outcomes. See [conventions/artifacts.md](artifacts.md) for filenames,
evidence validation, UTC layout, interruption limits, and manual retention.

For newly allocated runs, native reports and execution logs are grouped by
validation under `results/`, container evidence under `containers/`, and atomic
job outcomes under `jobs/`. Allocation/context checks and consolidation use the
job namespace; native reports never replace outcome metadata. The artifact
convention defines the complete path mapping. Preserve every generated evidence
file after success, failure, and interruption; existing flat-layout runs remain
untouched. Container removal is independent of evidence retention.

## Cancellation

SIGINT and SIGTERM are handled from entry/input and every pre-flight through
allocation, native-report processing, atomic publication, and final return.
One shared deadline allows five seconds for graceful termination and five more
for forced termination and verification. Repeated received signals request forced
cleanup without restarting that deadline. Previous handlers are restored on exit.

The managed boundary verifies native frontend/command-parent identities by PID
and Linux start time. A detached guardian survives Lefthook's command-group
cancellation, monitors parent/frontend lifetime, and keeps the coordinator alive
for cleanup. It stops only its verified frontend when needed to release a blocked
stdin copier. It never signals a contributor shell or unrelated process group.

Each local child is registered before its command starts. Each Composer command
keeps its existing script/report argv and runs directly in its own temporary
container, with Docker-managed init and TTY/stdin disabled. Create without `--rm`
and with `--pull never`, reuse mounts through the existing php container, and
reuse its environment, user, working directory, immutable image, and networks.
Override the service's startup command with Composer; no PHP/shell supervisor
executes inside the check container.

Before creation, publish a unique reserved name and project/execution/check
ownership labels. Register and verify the immutable Docker ID before native
startup. A local creation-request owner can survive a killed Lefthook job long
enough to retain the daemon acknowledgement. A killed create client is insufficient
proof that nothing was created: reconcile pending receipts and current-run labels.
Never use a container name alone as authorization to stop/remove it.

Cleanup is mandatory after success, native/report/scheduler/startup failure,
and catchable interruption. Stop all owned running containers before waiting,
then force removal of remaining objects within the same shared deadline.
Repeated received signals force cleanup sooner. Remove created-but-never-started,
running, stopped, exited, and dead containers through explicit reconciliation
and successful Docker absence queries. Normal cleanup follows confirmed native
completion and the log-collection attempt; an early start-client return must not
stop an otherwise normally running validation.
Another run, shared dev/php services, image layers, mounts, existing volumes/
networks, and retained reports remain intact. No global prune or prior-run
recovery sweep is used. Own temporary anonymous volumes are removed with the
containers when applicable. The current PHP image has no declared volumes and
its workspace/dependency mounts are reused.

Stopping a Docker client or leaving a stopped container is insufficient.
Unreachable Docker, unresolved creation, or unconfirmed removal fails explicitly;
native exit zero and valid reports cannot override cleanup failure. Native exit
status comes from verified daemon terminal state, independently of Docker-client
codes. Unknown/unstarted completion stays null; cleanup-induced termination must
not substitute a previously unknown normal tool outcome. Reserve time within the deadline
for client reaping, atomic final evidence, and frontend return.

Before allocation, cancellation exits nonzero with a concise phase diagnostic
and creates no QA reports. After allocation, retain completed evidence and publish
an interrupted summary where possible. SIGKILL/container loss may leave explicitly
incomplete evidence; neither enables automatic recovery, locking, report pruning,
service shutdown, or restoration of contributor changes.

## OpenSpec Validation In Dev

The seventh validation, `openspec`, uses `execution_backend: dev-process` and the
existing OpenSpec 1.14.0/Node installation in dev. Eligible manual/content runs
probe that exact version through the cancellation-aware process supervisor before
allocating reports. Missing or incompatible tooling rejects with rebuild guidance.
Git empty-update/deletion paths return before these QA dependencies and allocation.
No package installation, PHP-image tooling, Composer script, or service is added.

Run `openspec validate --all --strict --no-interactive --json` with argv-only
execution at the repository root. It validates all durable specs and active deltas;
unchecked active tasks are allowed. It excludes archive lint and never fixes,
rewrites, archives, or filters artifacts by changed filenames. Nonzero findings,
missing/malformed/foreign-root reports, and scheduler failures fail the gate while
all seven jobs still run and their outcomes are collected.

OpenSpec ownership is published before Node starts. Its local process group and
descendants join the same five-second graceful plus five-second forced/verification
deadline as the frontend, coordinator, probes, Docker clients and six PHP containers.
Repeated signals escalate without extending that deadline. Docker lifecycle loops
operate only on the six registered `php-container` checks. OpenSpec has no container
identity or creation receipts; see the backend-specific artifact contract.

## Native Completion And Snapshot Collection

PHP jobs start their verified owned containers without attachment and poll daemon
state through cancellation-aware requests. A start/attach/exec client returning
zero never establishes native completion. Confirm actual startup and coherent
exited/non-running/non-restarting state, start/finish timestamps and genuine native
exit code; preserve OOM/runtime diagnostics. Do not retry Composer, add completion
sleeps or introduce a container-side supervisor. Normal tool execution has no
five/ten-second timeout; that shared budget applies to cancellation and cleanup.

After native termination, retrieve separate stdout/stderr using non-follow
`docker logs` snapshots before explicit removal. Preserve complete and partial
streams under the existing grouped paths. Publish QA Scope/Fixer/PHPStan stdout
as reports only after validation; retain console streams as diagnostics for
report-to-file checks. Correctly empty diagnostics are allowed after complete
collection. Missing/truncated/unconfirmed output fails even with native zero;
known native codes survive collection failure and all owned containers still
require removal. Terminal output must distinguish native findings from execution,
collection, report and cleanup failures.

QA Scope must report each configured managed target (currently phpstan.neon,
phpcs.xml and php-cs-fixer.dist.php) exactly once with a consistent status. Empty
text cannot pass. Validate each structured tool's native fields/types and result
semantics, including actual JUnit test cases/counts; arbitrary JSON/XML cannot
replace a native report. Complete nonzero findings remain retained valid reports.

A passed PHP job requires matching current-run immutable identity, confirmed
terminal-state/native-code proof, complete snapshot collection, valid report and
confirmed removal. Consolidation verifies the retained container metadata;
summary schema 4, seven checks and OpenSpec's local backend remain unchanged.
Cancellation covers polling, collection, parsing and publication under the same
shared deadline, preserving confirmed facts/partial output without postponing
removal. Repeat-signal escalation and overlap/resource isolation still apply.

Automation verification must reproduce early client return and prove complete
small/large separate stdout/stderr snapshots, genuine zero/nonzero, invalid reports,
failed/truncated snapshots, spoofed metadata and cancellation. Native acceptance
must independently prove its own remote fixture command completion through
persisted fixture receipts or equivalent daemon evidence before interpreting its
results or stopping fixture services. Fixture-only control helpers never enter
production hook execution. Preserve old schema/layout files unchanged.
