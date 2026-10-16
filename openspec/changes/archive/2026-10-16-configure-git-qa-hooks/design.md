# Design

## Context

See `proposal.md` for motivation and scope, and `specs/repository-git-hooks/spec.md` for acceptance behavior. Existing package capabilities describe scope management, not contributor push gates.

The repository separates `dev` automation from the `php` tooling service, with both mounting the same workspace. The dev image already includes Python 3, Git, and Docker integration. All six Composer scripts exist. PHPMD's script selects `src,tests,bin` with text output; its installed CLI also supports `--reportfile-json`, allowing a JSON side report without changing that script. Logs and caches are ignored, and export attributes already cover contributor infrastructure except the proposed root Lefthook configuration.

Existing dev post-create steps initialize Codex context and Headroom; post-start starts the Headroom proxy. This change appends hook setup to post-create only. Hook activation belongs to post-create or explicit `setup-git-hooks` execution.

Sections 1–9 record completed implementation: Git/manual routing, entry-wide cancellation, the managed frontend guardian, atomic evidence, and an internal PHP supervisor were verified by 34 tests including PTY/native acceptance. The earlier open-stdin/KeyboardInterrupt defect motivated section 9 and is resolved by the retained routing and frontend supervision.

Section 10 replaces shared-service native execution and its PHP supervisor with disposable containers, verified by fresh 45-test native/PTY acceptance in `verification.md`. Previous acceptance remains historical evidence, not proof of container creation/removal guarantees. The active PHP service currently uses a workspace bind mount, no declared image volumes, the existing project network, and restart policy `no`; it remains available as a runtime template without being restarted or removed.

Section 11 groups container evidence and native reports by validation, renames job metadata to `jobs/`, and retains all generated evidence. Fresh 48-test unit/integration/PTY/native acceptance verifies this grouped layout. The earlier 49 tasks and flat-layout acceptance remain historical implementation evidence; `verification.md` records the current layout independently.

Sections 12 and 13 are implemented and verified, completing all 70 tasks. Preserve the original 60 checked descriptions and all earlier evidence as history. The real manual-run defect (empty Fixer/PHPStan capture and falsely accepted empty QA Scope) motivated decision 12. Its verified state/snapshot/removal boundary now distinguishes native completion from client return, and the fixture independently proves remote completion with retained receipts. The complete 60-case suite with real Docker/PTY enabled plus the added historical-schema-4 case exercised 61 distinct tests, including 16 real-native runs. Current evidence is in `verification.md`; historic schema-3/schema-4/flat runs remain untouched.

## Goals / Non-Goals

**Goals:**

- Delegate validation scheduling and concurrency to Lefthook.
- Keep Python focused on pre-flight, one validation's report capture, run context, and final consolidation.
- Support the exact direct terminal command and installed Git invocation with shared QA behavior and distinct input/reference policies.
- Handle SIGINT/SIGTERM in every phase, with bounded frontend/local/container teardown and truthful interrupted evidence.
- Run each PHP check in a temporary container and confirm complete removal after every reachable-Docker outcome, including creation/start failure and interruption. Execute OpenSpec locally in dev under the same lifecycle supervision.
- Retain detailed native reports while keeping terminal output concise.
- Verify push policies and integration without adding a separate Python tooling stack.

**Non-Goals:**

- Pre-commit enforcement or a commit-specific dev requirement.
- Stash creation/application, index backups/fingerprints, recovery markers, or lock ownership.
- A Python thread/process pool, public hook framework, automatic fixes, report pruning, or workspace snapshot isolation.
- Persistent QA services, new dedicated networks/named volumes, global Docker pruning, shared-service shutdown, or another internal PHP/shell process supervisor.

## Decisions

### 1. Install one Git hook and use one custom parallel group

Keep Lefthook `2.1.16`, the stable release inspected for this change, pinned in the dev Dockerfile. Use the existing Node/Yarn toolchain to install the official npm package after `corepack enable`:

```dockerfile
RUN CI=1 yarn global add lefthook@2.1.16 \
    && test "$(lefthook version)" = 2.1.16
```

The installation-scoped `CI=1` suppresses the package's automatic `lefthook install` postinstall behavior without setting CI globally. Hook activation stays in `setup-git-hooks`. Retain setup's exact version check, the matching configuration minimum version, and `assert_lefthook_installed: true`.

Remove the Lefthook-specific architecture mapping, release download, hardcoded checksum check, and the now-unused `TARGETARCH` argument. Keep shared tools required elsewhere. The official package selects a version-matched platform binary through optional dependencies; Yarn/package metadata supplies package integrity instead of independent hardcoded GitHub asset checksums. The installed command is a Node wrapper that needs its package files. Node and Yarn are already part of dev, so this simplifies image maintenance without adding another toolchain.

The previous standalone binary avoided a Node dependency but required custom platform/download/checksum logic. Prefer the npm package because dev already maintains Node/Yarn; verify the installed wrapper and adapt isolated fixtures rather than copying only the wrapper executable.

The pre-push frontend has two mutually exclusive mode entries selected before stdin forwarding. The installed managed launcher exports `QA_HOOKS_GIT_PUSH=1` only to its child; it is not a service env-file setting. That entry invokes the Git coordinator mode with `use_stdin: true`. Direct `lefthook run pre-push` selects manual mode with no Git-stdin forwarding. Use complementary Lefthook conditions so exactly one entry runs, and validate the routing against the pinned release. Git-mode EOF with zero records remains an early return; it never triggers manual QA.

Both modes enter the same coordinator pipeline after their mode-specific pre-flight. Git mode consumes and classifies actual records and keeps all branch/tag policies. Manual mode requires dev, an existing clean `HEAD`, and QA dependencies, then checks that checkout whether attached or detached; it neither invents a reference update nor contacts a remote. The custom `qa-checks` group still declares the seven parallel jobs and invokes `tools/git-hooks check <validation-id>`; it is not another installed Git hook.

A managed command boundary supplies verified identity of the outer frontend and preserves a cancellation-capable supervisor even when Lefthook cancels its command shell. Keep terminal signal delivery and frontend-lifetime observation explicit; do not rely on the default PTY behavior or a cleanup handler in a process the frontend may immediately hard-kill. On cancellation, the supervisor can terminate this invocation's identified frontend as well as its descendants, so an outer stdin copier cannot keep a waiting spinner alive after the coordinator exits. PTY tests of the actual npm wrapper/native dispatcher must validate this arrangement before it is accepted.

Detecting a TTY only in Python is insufficient: Lefthook's cached reader has already turned terminal input into a pipe. Supplying artificial Git records or mapping empty stdin to manual mode would also blur the existing Git no-update policy. Select the mode at the frontend and retain one shared QA implementation instead.

Verify the pinned release's stdin/argument forwarding and named custom group execution in isolated installation tests. Forward the remote name/location when available; update policy depends on stdin, not inferred command arguments.

```text
Git --> installed launcher --> Git-mode entry ----+
                                                  |
Terminal --> lefthook run pre-push --> manual -----+
                                                  |
                                                  v
                         lifecycle cancellation supervisor
                                                  |
                               mode-specific pre-flight
                                                  |
                            checkout/runtime checks
                                                  |
                               allocate run context
                                                  |
                            lefthook run qa-checks
                                  |             |
                                  v             v
                          six PHP containers   OpenSpec in dev
                                  |             |
                                  +------+------+
                                         |
                                         v
                              collect all seven outcomes
```

Do not put final reporting after the checks in a stop-on-failure pipeline. Lefthook's `piped: true` stops subsequent jobs on error and cannot be enabled with `parallel: true` at the same level. The coordinator waits for the custom group's return, including a nonzero result, then consolidates evidence. Configure neither fail-fast sequencing nor file filters on the seven check jobs.

Alternatives considered: a Python scheduler makes context/result sharing convenient but duplicates functionality already supplied by Lefthook. Pure configuration sequencing complicates unconditional final reporting. A small coordinator plus a native parallel group gives one owner for each responsibility.

### 2. Keep domain responsibilities and shared lifecycle supervision

Planned layout:

```text
tools/
    git-hooks
    git_hooks/
        __init__.py
        execution.py
        test_execution.py
        runner.py
        test_runner.py
        preflight.py
        test_preflight.py
        qa.py
        test_qa.py
        reports.py
        test_reports.py
        test_hooks_integration.py
        test_hooks_terminal.py
```

| Module | Responsibility |
| --- | --- |
| `runner.py` | Coordinate pre-push, pass run context, invoke/wait for one Lefthook process, handle final result and catchable interruption |
| `execution.py` | Own entry-wide cancellation state, verified process/frontend identities, cancellation-aware subprocess operations, and bounded idempotent teardown |
| `preflight.py` | Environment/dependency checks, Git queries, update parsing, checkout and cleanliness policies |
| `qa.py` | Execute one registered PHP-container or dev-local validation, capture reports/diagnostics, and record backend-specific outcome/cleanup |
| `reports.py` | Allocate UTC directories, write independent result records, consolidate the sole summary, render terminal output |

Git queries belong to pre-flight; a separate `git.py` with state mutation/recovery helpers is unnecessary. The entrypoint supports explicit Git/manual coordinator modes and `check <id>` plus any internal managed-boundary mode needed for supervision. Contributors still use `lefthook run pre-push` directly. Disable bytecode before local imports so the automation does not introduce untracked `__pycache__`. Tests use `python3 -B`, standard-library `unittest`, temporary directories, and real PTYs. Container lifecycle stays in contributor-side Python helpers. Remove `php-process.php` and the obsolete PHP-side cancellation adapter rather than adding an executable or supervision script inside the temporary containers. Keep local process/frontend supervision; it solves a different lifecycle boundary.

There is no generic registry, plugin API, additional Python dependency manager, or mirrored test for every helper.

### 3. Preserve push pre-flight and remove commit enforcement

Declare `QA_HOOKS_SERVICE=dev` in `docker/dev/.env.example` and the ignored local `docker/dev/.env`. The existing dev `env_file` in Compose supplies it to the container. Remove the inline `environment` declaration for this variable so service variables are centralized in the env file, without duplicate definitions whose Compose precedence would override local values. Preserve unrelated local environment entries and keep `docker/dev/.env` ignored.

The required runtime value remains `dev`; moving its declaration does not change acceptance policy. Check that identifier together with a container runtime indicator rather than deriving service identity from username/hostname. A missing or incorrect marker fails clearly, including for empty updates and deletions. It is a contributor guardrail, not authentication. No commit hook or commit-specific runtime gate is installed.

`tools/env` copies the service example only when the local file is absent and leaves existing files untouched. Fresh environments receive the marker from the updated example; existing environments need a targeted addition/update of `QA_HOOKS_SERVICE=dev` followed by dev recreation. Document that migration without adding an automatic env-file rewrite, container recreation, or start/attach check. Inline Compose assignment was initially chosen for a fixed service identity; the confirmed decision now prioritizes centralizing service variables in the env file while retaining the same gate.

In Git mode, read all four-field records as `<local-ref> <local-oid> <remote-ref> <remote-oid>`, validate shape and object IDs using Git's object format, and classify before QA. Manual mode does not consume these records; it validates the current clean checkout through the shared runtime/check pipeline:

| Effective records | Action |
| --- | --- |
| Zero | After dev gate, succeed without QA dependencies or checkout checks |
| More than one | Reject, including multiple deletions or branch plus tag |
| One deletion: `(delete)` and zero local OID | After dev gate, succeed without checkout/cleanliness checks or QA dependencies |
| One branch update | Require current source branch, input local OID equal to HEAD, clean checkout, and all seven checks |
| One tag update | Require detached HEAD, transmitted tag's peeled commit equal to HEAD, clean checkout, and all seven checks |

Count records supplied by Git, not command refspecs or commit count. Up-to-date references omitted by Git do not trigger validation. A new tag is an effective update even if its commit already exists remotely. Git might not invoke pre-push for a no-op; these policies apply when it does.

Resolve source names through symbolic full-name resolution where needed. Symbolic `HEAD` on the checked-out branch can resolve to that branch; raw-object sources and unsupported namespaces are rejected. Branch and tag updates require destinations in their respective namespaces. A different remote branch name is allowed, while identical commits on another source branch do not satisfy source identity.

For tags, peel the transmitted local OID to a commit and check source consistency. An annotated tag's object ID differs from its commit ID; non-commit tags fail. Deterministic acceptance uses detached HEAD and commit equality. Semantic guidance requires explicit checkout of the intended tag because Git cannot distinguish synonymous tag names at one commit.

A content update requires index equality to HEAD, tracked worktree equality to index, and no nonignored untracked files, using NUL-safe Git queries. Suggest stash or explicit resolution if dirty; do not perform either. Ignored output does not count as dirtiness. Verify Docker Compose access, the running php service, Composer, development tools, and required configuration before launching the scheduler. Do not start services or install missing dependencies automatically.

### 4. Accept overlapping pushes and isolate reports

Do not acquire an interprocess lock or inspect previous-run state. There is no stash transaction to serialize. Two pushes can repeat QA and compete for resources; this is accepted for the first version.

Each invocation exclusively creates its own `logs/prepush/YYYYMMDD-HHMMSS-mmm/` directory. Use timezone-aware UTC, truncate microseconds to three millisecond digits, and retry collisions with a new datetime within a bounded interval. Fail rather than overwrite or append a suffix that changes the agreed format. No SHA path component is used.

Pass the allocated absolute directory to the nested Lefthook process through `QA_HOOKS_RUN_DIR`, plus `QA_HOOKS_EXECUTION_ID` matching its basename. Child jobs inherit this context. They validate that the directory is the allocated pre-push run location and their ID is one of the seven expected IDs. Direct custom-group execution without valid context fails clearly. Do not use global current-run pointers, shared temp filenames, or a shared writable summary.

Only ignored reports and existing native caches are written. No stash/index/worktree preparation or recovery is performed. Incomplete prior reports neither block a new execution nor trigger repair.

### 5. Each job captures one registered validation

Each PHP job creates one temporary container and directly executes the existing Composer command with noninteractive/no-ANSI options and its script separator. Use argv-only creation, startup without attachment, cancellation-aware state observation, and non-follow log collection with TTY/stdin disabled. Reuse the PHP runtime context in decision 9 and preserve the commands/scopes below. OpenSpec stays dev-local (decision 11). Each job waits for actual workload completion and evidence collection; Lefthook schedules all seven.

| ID | Command/script | Primary report | Adapter/runtime |
| --- | --- | --- | --- |
| `qa-scope` | `qa-scope check` | `results/qa-scope/result.log` | Text stdout; stderr is diagnostics |
| `sniffer` | `sniffer-check` | `results/sniffer/result.json` | `--report=json --report-file=<path> --no-colors -q` |
| `fixer` | `fixer-check` | `results/fixer/result.json` | `--format=json --no-ansi --show-progress=none`; native stdout |
| `md` | `md-check` | `results/md/result.json` | `--reportfile-json <path>`; existing text output is diagnostics |
| `stan` | `stan-check` | `results/stan/result.json` | `--error-format=json --no-progress --no-ansi`; native stdout |
| `test` | `test` | `results/test/result.junit.xml` | `--log-junit <path> --colors=never` |
| `openspec` | `openspec validate --all --strict --no-interactive --json` | `results/openspec/result.json` | Supervised dev process; JSON stdout, separate stderr |

Use full native scopes without filename arguments or filtering. Preserve Fixer's existing dry-run/diff policy and PHPMD's text-renderer positional argument. Confirm adapters against installed CLI capabilities during implementation; PHPMD's JSON side-report support was already inspected.

For PHP jobs, collect native stdout/stderr from the verified exited container using non-follow Docker log snapshots before explicit removal. Stage stdout for QA Scope/Fixer/PHPStan, keep stderr separate, and route report-to-file tools' console streams to diagnostics. OpenSpec retains supervised local process capture. Atomically publish only complete valid native reports; retain invalid/interrupted output. Validate native fields/types and successful semantics rather than arbitrary JSON/XML or text-file existence. Require QA Scope statuses for the configured managed targets. A valid nonzero native report remains retained; zero without valid complete evidence fails.

Each job atomically writes its own `jobs/{id}.json`; only PHP jobs write `containers/{id}/metadata.json`. Preserve existing schema-4 job fields: run/check/backend identity, status, genuine native code or null, duration, relative paths, report validity, container identity/cleanup state, and errors. Extend PHP metadata with verified terminal-state and collection proof (decision 12). Record start-client codes separately from native codes. Unstarted or unobserved completion keeps the native code null. Consolidation verifies matching container proof before accepting a passed PHP record. OpenSpec keeps null ID and `not_applicable`. Any command, collection/report, cancellation or cleanup failure returns a nonzero job result; only the coordinator writes the shared summary.

Per-job records are operational metadata, not replacements for native tool JSON. They are retained with the run. Only the coordinator writes `summary.json`.

### 6. Always consolidate after scheduler return

After allocation, write an initial `summary.json` with the seven expected validations and an incomplete overall status. Capture the nested Lefthook stdout/stderr into `runner.log` so its execution chatter does not stream to the main terminal. Preserve the Python terminal summary through the outer hook launcher.

Invoke one `lefthook run qa-checks` subprocess with the run context and await its completion. Never invoke pre-push recursively. In finalization, read every expected result record and validate its execution identity, validation ID, completeness, and reported artifact paths. Missing/malformed/running records are execution failures, not successful or silently skipped checks.

The final summary records schema version 4, execution ID, hook `pre-push`, invocation mode, UTC start/end times, overall status/exit code, Lefthook exit code when available, operational/cleanup errors, and all seven validation outcomes with codes, durations, and report/diagnostic paths. Preserve the existing six-ID order and append `openspec`; each outcome includes the registered backend. Container cleanup summarizes only the six PHP jobs, while local cleanup errors also prevent overall success. Atomically replace the summary from the same directory. Extend result validation consistently for interrupted/not-started outcomes and mode/container metadata and cleanup outcomes without fabricating command exit codes.

Success requires seven complete successful records, valid reports, successful scheduler/local teardown and confirmed PHP-container removal. Passed PHP records must match current-run/container terminal-state and completed-collection proof; a zero start/log client or empty text file is insufficient. Preserve genuine native codes even if collection or cleanup fails, without enabling success. Scheduler launch failure finalizes unstarted checks truthfully. Early returns before allocation keep concise diagnostics without invented files. `not_applicable` remains exclusive to local OpenSpec.

Terminal output names failed checks, identifies execution/report failures, and points to the directory without streaming native output. Example:

```text
The following validations failed: PHPStan, tests. Check reports in logs/prepush/20261007-010000-123/.
```

Install lifecycle signal handling before mode/input/environment/argument processing, and retain it through subprocess teardown and final reporting. A shared execution helper owns cancellation state, subprocess/group registration, frontend identity, and bounded waits for Git/runtime probes, the scheduler, jobs, and Docker clients. Local cancellation has a five-second graceful interval and a further five-second forced-teardown/verification budget shared by the whole execution rather than restarted for each child. A repeated signal escalates within that same deadline; it does not recursively re-enter finalization.

Do not rely solely on terminal propagation or `subprocess.run` cleanup. Register children before waiting, use cancellation-aware input/probe operations, and supervise frontend lifetime. The managed boundary keeps the cancellation owner alive long enough to stop its workers and publish evidence, then terminates only its verified frontend if it is still waiting. Restore previous signal handlers on ordinary exit. These helpers supervise lifecycle; they do not implement a Python validation scheduler or pool.

Container cleanup is unconditional after normal native completion and log collection, execution/report/scheduler failure, and catchable interruption. An early normal start-client return triggers state observation, not cleanup of a still-running tool. Per-job cleanup owns its container; the coordinator reconciles current-run identities when jobs/clients die. During cancellation/failure, stop all owned running containers together, then force removal and verify absence under one shared five-second graceful plus five-second force/verification budget. Polling, log capture, clients and repeated signals must not reset that budget. Preserve available terminal/partial-log evidence without delaying removal beyond it. Shared services and other runs remain untouched.

Cancellation before allocation emits a short diagnostic and nonzero result without fabricated QA files. During allocation/initial publication, retain an interrupted summary if the run directory is usable; otherwise any partial directory remains incomplete. After allocation, preserve completed job outcomes and native files, distinguish interrupted/not-started work, and publish overall `interrupted` rather than success. Defer cancellation across short atomic-publication critical sections, then re-check it before terminal success or final return. Metadata remains parseable even when interrupted during report parsing or final consolidation.

SIGKILL or Docker/container loss may prevent teardown/finalization; retained records then remain incomplete or record unconfirmed cleanup and never imply success. Ordinary SIGINT/SIGTERM with reachable Docker must satisfy the full local-process and owned-container-removal contract, including the original outer frontend, without requiring EOF or additional interrupts. Missing or unreachable Docker is not equivalent to a confirmed absent container.

Keep every report, diagnostic, result record, and summary until manual cleanup. Setup and hooks perform no pruning.

### 7. Install only pre-push and document contributor boundaries

Create idempotent `docker/dev/bin/setup-git-hooks`, prepare its executable in the dev Dockerfile, and append it to the existing post-create chain. Preserve existing Codex setup and Headroom startup; add no start/attach checks.

Configure actual installed hooks to contain only pre-push; the custom `qa-checks` group is invoked explicitly. Preserve unrelated user hooks/hook-path configuration and report unmanaged conflicts instead of overwriting them. No previous pre-commit from this change has been installed; future rollback removes only the owned pre-push launcher after authorization.

Add `/lefthook.yml export-ignore`. Existing exclusions cover tools, Docker, conventions, logs, and OpenSpec. Existing log ignore patterns remain sufficient. Composer scripts, native tool scope policies, and consumer interfaces are unchanged.

Create `conventions/git-hooks.md` with standard convention front matter: `id: git-hooks`, title `Git Hooks Convention`, and a `when` covering hook installation, configuration, execution, verification, troubleshooting, documentation, and bypass decisions. Use a hook-specific name because this change documents local Git hooks; the scoped `CI=1` installation flag does not introduce a remote CI pipeline.

Move these existing sections into the new convention, preserving the installed pin, commands, prerequisites, policies, examples, and failure handling:

- From `conventions/environment.md`: `Git Hook Dispatcher`, `Pre-push Runtime And Installation`, and `Pre-push Validation And Result Ownership`.
- From `conventions/git.md`: `Pre-push Policy` and `Agent Response To Hook Failure`.

The final documentation ownership is:

| Source | Responsibility |
| --- | --- |
| `conventions/git-hooks.md` | Lefthook installation/rebuild/setup, required dev marker and migration, pre-push reference/checkout policies, custom group/context and adapters, hook automation verification, and agent failure/bypass rules |
| `conventions/environment.md` | Environment topology, general service/bootstrap guidance, AI tools, and ordinary local package QA commands; link to the hook convention for hook-specific instructions |
| `conventions/git.md` | General working-state, branch, commit, push authorization, and review guidance; link to the hook convention for pre-push policies |
| `conventions/artifacts.md` | Canonical report formats, UTC paths, diagnostics/results/summary ownership, and manual retention; reference it from the hook convention rather than copy its report specification |

Add the new source to `AGENTS.md`, the documentation boundaries in `conventions/repository.md`, and the context map in `openspec/config.yaml`. Replace migrated blocks with concise links so later changes have one canonical owner. Existing source configuration files, tool behavior, export boundaries, and runtime tests remain unchanged by this documentation revision.

After any hook failure, agents inspect available evidence, explain the actual cause and file/line details when available, suggest commands, and await a new explicit instruction before corrective actions, restaging, or retries. They do not immediately execute a suggested fix. Technical acceptance is not permission to push.

In the migrated `Agent Response To Hook Failure` section, preserve that response rule and add the following independently applicable rule exactly:

> Agents MUST NOT bypass repository hooks without explicit human authorization for the specific operation.
>
> Authorization to commit, push, fix a failure, or retry MUST NOT be interpreted as authorization to bypass hooks.
>
> This restriction applies to `--no-verify`, `LEFTHOOK=0`, disabling hooks, and equivalent mechanisms.

State explicitly that the bypass prohibition applies before and after a failure. Explicit authorization is limited to the named operation and cannot be inferred from a general instruction to complete the work. Lead with `Agents MUST NOT bypass` so the rule remains a prohibition even if its first clause is excerpted. This governs agent conduct; it adds no runtime enforcement and does not remove existing bypass mechanisms. The build's installation-scoped `CI=1` controls package postinstall activation rather than granting authorization to bypass a Git operation.

### 8. Verify integration boundaries without a Python scheduler suite

Use standard-library tests adjacent to the four modules. Use real temporary Git repositories for reference/checkout policies and evidence that no tracked content, index, or stash is changed. Stub native commands only where needed to return controlled reports/exits and exercise capture.

Test the pinned Lefthook in isolated repositories for pre-flight ordering, stdin forwarding, the exact seven-job custom group, concurrent execution, continuation after one failure, and final consolidation after nonzero exit. Use process synchronization rather than fragile timing thresholds. Test independent run contexts with overlapping invocations and forced timestamp collisions.

Adapt fixtures that previously copied a standalone executable: the npm wrapper's relative imports require its package layout and Node runtime. Exercise the installed npm command with those dependencies available; where isolation deliberately requires the package's native binary, resolve it explicitly and retain separate wrapper verification. Missing-Python launcher tests must still reach the Python failure with Node available, and unavailable dispatcher/runtime paths must continue to reject clearly. Native acceptance must exercise the rebuilt npm installation rather than silently mounting the old downloaded binary. Verify the installed version, platform package resolution, and absence of npm-time Git hook installation during the image build.

Test malformed/missing result records, mismatched execution IDs, report parsing, scheduler launch failure, catchable interruption, UTC directories, retained incomplete runs, and concise output. Verify no pre-commit is installed and commits receive no dev gate. Recovery, index-fingerprint, stash-selector, locking, and Python-worker-pool tests are outside this version's scope.

Add isolated PTY tests of the installed npm/Node/native-Lefthook frontend, not only direct Python calls. Keep terminal stdin open and prove the exact manual command begins its seven checks. Use synchronization barriers to inject SIGINT/SIGTERM during input, Git/environment/runtime probes, allocation/initial publication, job execution, native-report parsing, and final consolidation, plus repeated interruption during teardown. Assert nonzero interruption outcome, no traceback or persistent waiting spinner, bounded exit and no owned local or temporary-container survivors, parseable interrupted/incomplete metadata, completed-report retention, and independence of overlapping runs. Kill only fixture-owned processes in these tests.

Repeat native acceptance for real installed Git pushes and direct manual validation on clean attached/detached disposable checkouts, including success and intentional PHP/OpenSpec rejection. Compare fixture remote refs after manual runs. Verify daemon-observed native completion, complete non-follow snapshots including large stdout/stderr, and removal of every owned created/running/exited container. Keep policy/setup tests. Historical attached/automatic-removal acceptance does not prove the revised boundary. The fixture's own remote control must independently prove real command completion, for example through a uniquely scoped atomic fixture receipt and persisted stdout/stderr; a Docker exec client's return cannot close the fixture or end its services. Such fixture control must not enter production tooling.

For the env-file revision, verify Compose resolves `QA_HOOKS_SERVICE=dev` from the service file with no inline override. Update the isolated native acceptance fixture to exercise `env_file` delivery rather than setting the marker directly in its service `environment`. Verify fresh bootstrap includes the example marker and existing local values are preserved. The prior direct-environment native run does not establish acceptance of the revised configuration source.

Explicit command:

```sh
PYTHONPATH=tools python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py'
```

Run it during implementation and relevant automation changes, not from pre-push. Add no Python testing framework or separate formatter/linter stack.

Verify unique convention ownership, links/index/context references, and explicit human bypass authorization before/after failures. During completion/capture apply, update `conventions/git-hooks.md` and `conventions/artifacts.md` for observed completion, snapshot collection, proof metadata and explicit removal. Preserve historical verification: the 45-test flat-layout, 48-test schema-3 grouped-layout and later 41 standard/13 distinct terminal cases do not prove the revised native lifecycle. Keep all 60 checked descriptions unchanged. Sections 12.6/12.7 and every section 13 task require fresh full-suite/native evidence before archive readiness. Implementation, canonical conventions and current `verification.md` evidence now match the revised contract; all 70 tasks are complete.

### 9. Own and completely remove temporary check containers

Use one disposable container per PHP validation, up to six per invocation. Resolve the running PHP service through the current Compose project, then reuse its immutable image ID, configured environment, user, working directory, workspace/dependency mounts with their access modes, and existing project network. This preserves the actual running runtime when an image tag or local env file changes. The shared service remains a template and dependency probe target; native QA no longer uses its exec processes. Keep the full seven-job registry separate from its six PHP-container IDs; local OpenSpec gets no container creation, reserved name/labels, receipt, or Docker lifecycle record.

Do not build/pull images, install dependencies, recreate/start services, allocate dedicated networks/named volumes, or publish service ports during hooks. Add Docker-managed init to the temporary containers and use no restart policy. No internal PHP/shell process supervisor is needed. Existing bind data, shared volumes/networks, image layers, and retained report directories are not temporary resources to remove.

Use separate creation, identity registration, startup without attachment, native-state observation, snapshot collection and explicit removal. Composer must not start before immutable identity publication and verification.

```text
reserve run/check name and labels --> create without --rm
                                         |
                                         v
                          register and verify immutable ID
                                         |
                                         v
                           start directly, without --attach
                                         |
                                         v
                      inspect until native termination is known
                                         |
                                         v
                     retain exit/state --> collect non-follow logs
                                         |
                                         v
                    validate reports --> retain native evidence
                                         |
                                         v
                      unconditional remove --> confirm absence
```

Publish unique intent/ownership before the create request. Register and verify the immutable ID/name/labels before startup and every state/log/removal operation; a name alone is not authority. Keep creation receipts and late-create reconciliation. Each job owns only its container; coordinator cleanup reconciles the current run's six PHP IDs. Preserve metadata after removal and never read old runs for recovery.

Disable automatic removal. Hold an exited container only for immediate evidence collection, not debugging retention. After collection or on failure/cancellation, explicitly remove every owned created/running/exited/dead object and its own anonymous volumes when applicable, then verify absence. Preserve shared/named volumes, bind sources, images, networks and services.

A start-client return never proves Composer completion. Use cancellation-aware daemon polling without rerunning Composer, fixed completion sleeps, terminal EOF or container-side supervisors. Ordinary validation has no artificial five/ten-second execution timeout; the deadline governs cancellation/cleanup. Verify that the container actually started and reached coherent terminal state before recording a native exit. Unknown/unstarted completion keeps that code null.

Reconcile outstanding creation/start requests before declaring absence; killing a client can leave work or a late-created object. During interruption, stop all owned running containers together, then force removal under the shared deadline. Missing/unreachable Docker produces unsuccessful unconfirmed cleanup. Report/collection failure cannot retain a container or authorize removing unrelated work.

Alternatives considered: attached completion plus `--rm` loses state/log evidence when the client returns early; reattachment/fixed sleeps cannot prove native completion; shared-service exec or PHP/shell supervisors restore the removed supervision problem; global/service shutdown affects unrelated work. Separate daemon state, snapshot collection and explicit removal preserve direct Composer execution and complete ownership.

### 10. Group retained evidence by validation and purpose

Use the same UTC execution root, `logs/prepush/YYYYMMDD-HHMMSS-mmm/`, for newly allocated executions. Validation IDs are `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, `test`, and `openspec`; container-specific paths apply only to the first six.

| Artifact | Previous path | Revised path |
| --- | --- | --- |
| Job running/final outcome | `results/{id}.json` | `jobs/{id}.json` |
| Container intent/identity/lifecycle | `containers/{id}.json` | `containers/{id}/metadata.json` |
| Settled creation request | `containers/{id}.create.done.json` | `containers/{id}/create.done.json` |
| Creation stdout | `containers/{id}.create.stdout.log` | `containers/{id}/create.stdout.log` |
| Creation stderr | `containers/{id}.create.stderr.log` | `containers/{id}/create.stderr.log` |
| Stop diagnostics | `containers/{id}.cleanup.log` | `containers/{id}/cleanup.log` |
| QA Scope report | `qa-scope.log` | `results/qa-scope/result.log` |
| Sniffer/Fixer/PHPMD/PHPStan report | `{id}.json` | `results/{id}/result.json` |
| PHPUnit report | `test.junit.xml` | `results/test/result.junit.xml` |
| Native/Composer diagnostics | `{id}.diagnostics.log` | `results/{id}/execution.log` |
| Staged stdout while capturing a report | `{id}.stdout.log` | `results/{id}/stdout.log` |
| Nested scheduler diagnostics | `runner.diagnostics.log` | `runner.log` |

Keep root `summary.json` and `runtime.json`, `processes/coordinator.json`, `processes/local/{id}.json`, root `cancel.json` and `{id}.cancel.json` at their existing paths. Section 11 preserved owners/data semantics/schema 3; section 12 introduced backend-aware schema 4. Section 13 keeps those paths and job/summary schema while extending current-run container metadata and native validation. All report references remain relative to the execution root.

Define one consistent path mapping within the existing responsibility-based modules and update every reader/writer. Allocation, context validation, runner exception/finalization paths, and consolidation must use `jobs/` for outcome records rather than treating native `results/` as the job-context marker. Prepare report directories for all jobs and container directories only for PHP jobs before opening writers or supplying paths to native tools, preserving run-boundary, ownership, and symlink protections. Directory creation and path publication remain cancellation-aware.

Update container intent/identity/receipt helpers, detached creation-request writers, process registrations containing receipt paths, and cleanup discovery together. Replace flat JSON discovery with the known PHP-validation metadata/receipt paths under this run; otherwise grouped records would be missed or `create.done.json` could be mistaken for ownership metadata. Directory names alone never authorize Docker operations. Preserve receipt settlement, immutable identity verification, late-create reconciliation, overlap isolation, and the shared cleanup deadline.

Preserve native report formats, original Composer/script arguments, full scopes, genuine codes and diagnostic separation. Atomically publish valid staged stdout and retain invalid/interrupted snapshots as well as their diagnostic copies. Decision 12 adds post-exit snapshot capture, native-format/target completeness checks and container completion/collection proof without renaming files or pruning generated evidence.

Retain every generated report, diagnostic, job outcome, container record/receipt, process identity, and cancellation marker until manual cleanup, including successful executions. Container removal never deletes their evidence files. Do not introduce `.state/` retirement, success-only deletion, combined evidence files, or debug-only retention. Existing flat-layout run directories remain byte-for-byte untouched; hooks neither migrate historical runs nor search them for recovery.

Alternatives considered: `stats/` would obscure job outcomes' status/error/identity role; `jobs/` matches the existing Lefthook boundary. Shared infrastructure logs or success-only state deletion could reduce file count but are outside this organization-only scope. Preserve distinct creation streams and receipts for their existing consumers.

During apply, update `conventions/artifacts.md` and hook references for all seven IDs, retained evidence, old-run immutability, atomic publication, malformed/absent outcomes, interruption and real Docker absence in Git/manual modes. Historical 45-test and 48-test records validate their respective old layouts. Pending 12.6/12.7 and section 13 require fresh mixed-backend/native-completion/snapshot acceptance before archive readiness.

### 11. Run OpenSpec locally with backend-aware seven-job outcomes

Register `openspec` after the existing ordered PHP IDs and have Lefthook run all seven jobs concurrently without filters or fail-fast sequencing. The registry must identify `execution_backend: php-container` for `qa-scope`, `sniffer`, `fixer`, `md`, `stan`, and `test`, and `execution_backend: dev-process` for `openspec`. Derive Docker ownership, creation, discovery, reconciliation, and cleanup only from the six registered PHP IDs; do not iterate the full registry as if every job owned a container.

Run exactly `openspec validate --all --strict --no-interactive --json` with repository-root cwd and argv-only launch in dev. Reuse the installed `@fission-ai/openspec@1.14.0` and Node runtime; add no OpenSpec/Node tooling to PHP, new image, temporary dev container, or package dependency. Eligible-run pre-flight checks availability and the existing pin through supervised probes. Missing/incompatible OpenSpec rejects required Git/manual QA without installation or silent skipping. Git no-update/deletion paths retain their dependency exemption after the dev gate.

The command validates main specs and active change deltas, including unfinished changes. It does not require active tasks to be checked, validate archived tasks, prove semantic correctness, or verify implementation/spec correspondence. Run the full declared scope on each eligible execution, without filename filtering, auto-fixes, artifact rewrites, or archiving.

Use the existing local process/session gate and publish ownership before launching Node. Capture JSON stdout via `results/openspec/stdout.log`, atomically publish valid bulk JSON to `results/openspec/result.json`, and keep stderr/launch/runtime diagnostics in `results/openspec/execution.log`. Require the pinned bulk format: `version: "1.0"`, an `items` array with change/spec IDs, boolean `valid` and issue lists, consistent `summary.totals` item/passed/failed counts, and a `root.path` resolving to the requested repository. Exit-zero success requires all item outcomes valid and no failed items; valid nonzero findings remain report evidence. Do not confuse native bulk version 1.0 with coordinator metadata schema 4 or accept arbitrary parseable JSON. Nonzero validation with a valid report retains that report and fails the job; missing/malformed or inconsistent output fails even with exit zero. Keep genuine codes when known and null codes when launch/interruption prevents known completion. Preserve existing malformed-stdout diagnostic handling and interrupted partial-output retention.

Write `jobs/openspec.json` and use the existing `processes/local/openspec.json`, coordinator/global cancellation, and `openspec.cancel.json` paths when produced. Do not produce `containers/openspec/`, a Docker ID, creation receipt, or a false removed outcome. The local record always carries `container_id: null` and `container_cleanup: not_applicable`; failures of local launch, reporting, or teardown remain explicit failures.

Keep summary schema version 4 and mandatory per-outcome `execution_backend` verified against the registered ID. PHP success requires genuine zero, a valid native report, matching terminal-state/completed-collection proof from decision 12 and `container_cleanup: removed`. OpenSpec requires genuine zero, valid bulk output, successful owned-local execution/cleanup, `dev-process`, null container ID and `not_applicable`. Reject backend/proof/cleanup spoofing. Aggregate Docker cleanup over six PHP outcomes, but require all seven records, scheduler success and successful local/container teardown overall. Missing OpenSpec evidence neither substitutes another JSON report nor suppresses PHP reconciliation.

Handle both signals during OpenSpec probes, directory allocation, Node launch/validation, report parsing/publication, and final consolidation. Register any owned descendants and terminate only verified run-local groups; coordinate local cancellation with PHP stop/removal under the same five-second graceful plus five-second forced/verification deadline. Repeated signals escalate without extending it. Preserve completed evidence and overlap/unrelated-process isolation; do not require terminal EOF or leave a frontend spinner.

Keep every new/old evidence file until manual cleanup. Schema-3 directories and all prior layouts remain untouched and are not read for recovery or migrated to schema 4. The prior 48-test record remains six-job evidence; the standalone four-item OpenSpec validation in approximately 0.75 seconds only establishes local CLI behavior.

During apply, update hook/artifact conventions and exercise the real pinned CLI in isolated seven-job native fixtures with valid specs/deltas and deliberately invalid deltas. Add fake CLI and PTY cases for missing/incompatible tools, genuine zero/nonzero, malformed output, unfinished active tasks, backend spoofing, continued PHP execution after OpenSpec failure, local Node descendants, signals/repetition/overlap, full retention, seven-result publication, and confirmed removal of exactly the PHP resources. No tests or fixture mutations use contributor hooks/index/stash/remotes.

### 12. Observe native completion before collecting logs and removing containers

A prematurely returned Docker client can leave stdout empty and cause cleanup to stop unfinished work; the text validator can also falsely accept empty QA Scope output. Direct Composer checks succeeded with valid reports persisted inside PHP. Changing PHP rules or accepting empty JSON would not repair this boundary.

Use `docker start <verified-id>` without attachment and inspect the owned container until its native process terminates. Inspect `.State.Status`, `Running`, `Restarting`, `StartedAt`, `FinishedAt`, `ExitCode`, `OOMKilled` and `Error`. Confirmed native completion requires an actually started, exited, non-running/non-restarting container, coherent nonzero start/finish timestamps and a genuine integer native code. Retain OOM/runtime errors as failure diagnostics. Created/unknown/dead or startup-error state cannot fabricate completed success. Observe an acknowledged workload rather than launching it again after an early client return.

Extend existing `containers/{id}/metadata.json` with selected run-owned proof, without environment secrets: separate start-client code when known; native completion state (`pending`, `confirmed`, `unknown`); selected terminal-state snapshot/native code; collection state (`pending`, `complete`, `failed`, `interrupted`); available stdout/stderr byte counts; and existing ownership/cleanup/errors. Persist terminal evidence before collection/removal. Job/summary schema 4 and existing fields remain unchanged. Consolidation must cross-check current-run/ID/backend/native code against the proof before passing PHP. Missing, malformed, foreign or contradictory proof fails. A genuine nonzero native code remains recorded even when subsequent collection fails.

After verified native termination, retrieve separate stdout and stderr using `docker logs` without follow or TTY. Stage stdout for QA Scope/Fixer/PHPStan and atomically publish it only after native validation. For Sniffer/PHPMD/PHPUnit, validate their freshly generated report-to-file artifact and retain console output as diagnostics. Empty stderr may be correct after complete collection; an empty native report cannot prove success. Preserve partial/staged bytes and distinguish native findings, unknown completion, log-collection failure, and report-format failure.

Before relying on that path, prove non-follow snapshot completeness in the affected environment using delayed native work, separate stdout/stderr, large output, genuine zero/nonzero and deliberately failed/truncated retrieval. Normal cleanup starts after terminal observation and collection attempt, never merely because the start client returned. A client code alone cannot mark an unresolved snapshot complete. If reliable complete collection cannot be established, leave the job unsuccessful, remove its container and report the remaining blocker; do not add completion sleeps, accept empty output, silently narrow tests or introduce an internal supervisor.

Require tool-specific native fields/types and successful semantics, not arbitrary parseable JSON/XML or file existence. Sniffer needs native totals/files; Fixer a native changed-file list; PHPStan its totals/files/errors; PHPMD its native file/violation structure; PHPUnit completed JUnit suites with actual configured test results and coherent counts. Confirm exact installed native formats in fixtures during apply. QA Scope must account for every expected managed target (currently `phpstan.neon`, `phpcs.xml`, `php-cs-fixer.dist.php`) with no missing/duplicate/conflicting status; maintain the expectation from this repository's configured target contract rather than accept one arbitrary OK line. Complete nonzero findings remain retained valid reports but fail the job. Missing/truncated/malformed/inconsistent evidence fails even when a client reports zero.

Cancellation stays active through startup acknowledgement, state polling, log retrieval, parsing, atomic state/job publication and final return. Preserve facts confirmed before interruption; do not substitute a cleanup-induced termination code for a previously unknown normal outcome. Retain partial logs while enforcing the same five-second graceful plus five-second force/verification deadline for frontend, coordinator, local OpenSpec/probes/descendants, Docker clients and six PHP containers. Evidence retrieval cannot postpone removal beyond that deadline, and repeated signals cannot reset it. Test client/frontend death, pending creation, snapshot failure, unavailable Docker and overlapping runs. OpenSpec remains a direct local dev process with no container evidence.

Apply only to future runs. Preserve grouped paths, schema-4 backend identities, seven-job concurrency, command scopes, retained files and human bypass authorization. Do not repair historic summaries that accepted empty QA Scope or migrate schema-3/schema-4/flat runs. Update canonical conventions and fresh `verification.md` evidence during apply, without rewriting earlier acceptance claims.

## Risks / Trade-offs

- [Overlapping pushes compete for resources/caches] -> Accept concurrent execution; isolate result paths and record any runtime failure without adding a lock.
- [Missing/incomplete job evidence] -> Require all seven complete records and scheduler success; never infer success from absent files.
- [Catchable interruption before scheduler startup or during report publication] -> Use entry-wide cancellation state and supervised operations, defer interruption only across atomic critical sections, and re-check it before any success publication/return.
- [Frontend cancellation can hard-kill a command while workers survive] -> Preserve the supervisor at the managed boundary, verify frontend identity/lifetime, and test actual CLI/PTY cancellation rather than coordinator-only signal handling.
- [Native work or created containers survive Docker-client exit] -> Track current-run owned container intents/IDs, close creation/start races, stop/remove only matching identities, and verify Docker reports complete absence.
- [Client zero precedes native completion/output] -> Retain the container until coherent terminal-state observation and complete non-follow snapshots; separate client/native codes, prevent parsing or normal cleanup of active QA, and test premature-return fixtures.
- [Six containers consume the teardown deadline sequentially] -> Start stop requests together and share one grace/force/verification deadline; measure the entire frontend/native lifecycle in PTY tests.
- [Docker becomes unreachable during removal] -> Record unconfirmed cleanup and fail within the deadline; do not equate an inspect error with absence or erase ownership evidence.
- [Runtime context drifts or temporary resources accumulate] -> Reuse the active PHP image/configuration and existing mounts/network without builds/pulls, service recreation, or dedicated persistent resources; test context parity and anonymous-volume cleanup.
- [Checkout changes during QA] -> Require cleanliness before checks and document that contributors should avoid editing the checked-out content during validation; no workspace-freezing mechanism is introduced.
- [Report flags vary by tool version] -> Verify installed options and native parsing without changing existing Composer scripts.
- [Local hooks/environment markers can be bypassed externally] -> Treat them as contributor guardrails and retain semantic authorization requirements.
- [Existing local env files lack the new marker] -> Document a targeted env-file update and dev recreation; preserve bootstrap's existing-file behavior and fail clearly until the required value is present.
- [Two layers of execution] -> Keep a single coordinator invocation and fixed custom group; verify recursion avoidance, context propagation, and final reporting at the integration boundary.
- [npm wrapper depends on Node/package layout] -> Preserve those dependencies in isolated fixtures, verify the installed wrapper, and repeat native acceptance against the npm installation. Prior standalone-binary evidence does not validate this revision.
- [Documentation migration leaves duplicate or stale rules] -> Move the five named sections together, retain general Git/environment/report ownership, and update the convention index, documentation boundaries, and OpenSpec context map.
- [General task authorization is mistaken for hook bypass authorization] -> Start with `Agents MUST NOT bypass`, require explicit human authorization for the specific operation, and document that commit/push/fix/retry instructions do not imply it, before or after a failure.

## Migration Plan

1. Implement the focused Python entrypoint/modules and result protocol, testing them in temporary repositories without installing a hook into the contributor's working repository.
2. Install the pinned official Lefthook npm package through Yarn with scoped `CI=1` and an exact version check, add pre-push/custom-group configuration, dev marker in the service env example/local file, and post-create setup; remove the custom binary download and inline Compose marker, then test actual parallel dispatch in an isolated environment using `env_file` delivery and the npm installation.
3. Centralize hook documentation in `conventions/git-hooks.md`, preserve general Git/environment/report ownership, add the explicit human bypass authorization rule, and update the index/documentation boundaries/OpenSpec context map. Verify export attributes, assembled runtime/report adapters, and artifact parity. Those five convention-revision tasks are complete and remain recorded as historical implementation evidence.
4. Contributors bootstrap a missing dev env file from the example or add/update only `QA_HOOKS_SERVICE=dev` in an existing `docker/dev/.env`, preserving other values. Rebuild/recreate dev and run post-create setup or explicit `setup-git-hooks`; restarting an existing container does not load changed env-file values. Only pre-push is installed, with no change to how local commits run.
5. Authorized rollback removes only the owned pre-push launcher and retains logs. Reverting configuration does not itself remove installed launchers; rollback does not alter local Git content.
6. Section 9's mode entries and local/PHP supervision are implemented and verified. Its managed launcher still requires explicit installation/reinstallation; retain the frontend boundary and Lefthook `2.1.16` pin. Do not install contributor hooks automatically, add start/attach checks, or move the per-invocation marker into service env files.
7. Section 10's temporary-container creation/start/removal and direct Composer execution are implemented; the PHP supervisor and obsolete PHP-side cleanup were removed. Its 45-test acceptance remains evidence for the existing flat artifact layout and all 49 historical tasks stay checked.
8. Section 11 grouped paths/full retention remain historical schema-3 evidence. Sections 12 and 13 are complete: local OpenSpec, schema 4 and the six-PHP observed-completion/snapshot/removal lifecycle have current standard/native/PTY evidence. All 70 task checkmarks are complete, with the original 60 descriptions preserved. Composer scopes, local backend, authorization, summary schema and paths remain unchanged.
9. Native/PTY acceptance, final parity and removal checks succeeded, restoring archive readiness. Archive/sync and a Git commit remain separately requested operations. A rollback must restore a coherent future-run lifecycle and success contract while preserving old files, removal guarantees and bypass safeguards; merely re-enabling `--rm` is insufficient.
