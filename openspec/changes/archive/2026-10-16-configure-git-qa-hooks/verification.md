# Implementation Verification

## Sections 12–13: Verified Completion And Complete Collection

The completion/capture revision is implemented. PHP tools execute directly in
owned temporary containers without `--rm` or attached startup. The executor
observes coherent daemon terminal state, persists genuine native code separately
from client return, collects separate non-follow stdout/stderr snapshots, validates
native results and removes each container explicitly. Consolidation verifies
matching current-run/immutable-ID completion/collection/removal proof. Schema 4,
the seven jobs, original Composer args/scopes, local OpenSpec backend and grouped
artifact paths remain unchanged. No container-side supervisor was added.

Current acceptance on 2026-10-15 (UTC):

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py' -v
```

The complete 60-case suite passed in **513.813 seconds**, with real Docker/native
acceptance and actual npm/Node/Lefthook terminal tests enabled and no skips.
An additional explicit historical-schema-4 regression then passed in 0.017 seconds:

```sh
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_reports.ReportTests.test_historic_schema4_false_positive_is_not_migrated_or_recovered
```

Together these runs exercised the current inventory of **61 distinct tests**.
The additional case makes the historical QA Scope false positive explicit:
an older schema-4 passed record with empty QA Scope output remains byte-for-byte
unchanged while a fresh seven-result execution completes under the new rules.
It adds no implementation change after the complete-suite result.

The isolated Docker feasibility control also passed. It independently observed
native exits 0 and 7 and compared exact expected stdout/stderr bytes and SHA-256
digests. In the large-output case, start-client exit was 0 while the container
was still running; terminal inspection later recorded native exit 7. Non-follow
collection retained 1,048,590 stdout bytes and 1,048,587 stderr bytes, including
both end markers. Small-output collection also matched exactly. Both control
containers were explicitly removed and successful absence queries followed.
The control script/output under `tmp/git-hooks-completion-control.*` are provenance;
the expected behavior and measured outcomes are reproduced here.

Real native acceptance retained **16 runs** for fixture project
`qa-hooks-native-a26c608e0f3f`, UTC run IDs
`20261015-233606-993` through `20261015-233822-630`:

- Three successes: one installed Git push to the disposable bare remote and
  manual validation of clean attached and detached checkouts.
- Three intentional rejections: Git/manual QA Scope drift and an invalid active
  OpenSpec delta. Other PHP checks continued and native reports remained valid.
- Ten interrupted manual runs covering creation/start phases, held native work,
  repeated signals, descendants, overlapping runs and unrelated-process isolation.

All 16 finalized summaries recorded confirmed container removal. Representative
successful native report sizes were QA Scope 54 bytes (all three expected OK
lines), Sniffer 5,407, Fixer 146, PHPMD 126, PHPStan 62, PHPUnit 41,890 and OpenSpec
2,582. Sizes such as Fixer's timing JSON vary between runs; native structures and
successful semantics, not fixed byte sizes, determine validity. All six PHP jobs
had matching `confirmed` native completion, `complete` collection and `removed`
cleanup proof; local OpenSpec retained null ID and `not_applicable`.

Recorded coordinator cancellation-to-summary intervals ranged from **2.085 to
4.850 seconds**, derived from cancellation deadline minus the shared ten-second
budget and final UTC summary time. Forced/repeated-signal records measured 3.085
and 4.751 seconds. Native/PTY assertions also verified outer frontend exit within
ten seconds and repeated native escalation within five, no owned survivors,
no traceback/stuck stdin spinner and unaffected overlapping/shared resources.
Forced cleanup now sends Docker kill before removal so an in-flight graceful
stop cannot delay escalation. Fixture readiness has its own twenty-second budget;
the post-signal shared cleanup deadline remains ten seconds.

Regression coverage includes early client zero while native work is still alive,
genuine nonzero, missing/failed/truncated logs, arbitrary structured output,
empty/incomplete QA Scope statuses, actual JUnit cases/counts, missing/foreign/
contradictory terminal proof, byte-count mismatches, backend spoofing, complete
seven-result collection, atomic state/report publication, new observation/log
phases, late creation, unavailable Docker, retention and old-run immutability.
Native fixture control independently waits for run-scoped completion receipts and
captured files, rather than interpreting an exec client's return as remote exit.
These fixture-only control helpers are not part of production hook execution.

Final checks include strict all-items OpenSpec validation (four items passed),
diff/link/reference checks, unchanged historical 60 checked task descriptions and
unchanged public package/Composer/dependency/image boundaries. The last Docker
queries for `php-qa-scope.execution` and this session's control containers were
empty. Contributor hooks, index, stash, branches and remotes were not used by
acceptance; commits/pushes existed only in disposable fixture repositories.

Fresh native reports remain in `tmp/git-hooks-verification/native-reports/` and
the complete/focused logs in `tmp/git-hooks-state-full.log` and related diagnostic
files. Those transient paths supplement this self-contained record. Earlier
failed attempts and the pre-correction native transport limitation below are
historical evidence, superseded by the verified state/snapshot/receipt boundary.

## Historical Section 12: Native Acceptance Pending Before Section 13

This section records the pre-correction status as observed on 2026-10-14; its
pending task/acceptance statements are historical, superseded by the current
evidence above. Earlier evidence is retained for the behavior actually verified.

The section 12 implementation adds the ordered seventh check, `openspec`, using
OpenSpec 1.14.0 in dev and exactly
`openspec validate --all --strict --no-interactive --json`. The six PHP checks
keep their existing native Composer commands and temporary containers. Schema 4
binds each outcome to the registered backend; OpenSpec uses null container ID and
`not_applicable`, while passed PHP jobs still require confirmed `removed` cleanup.
All Docker lifecycle loops use the six-ID PHP subset. Local process ownership is
published before startup and retained when a completed leader has live descendants.
Full file retention and old schema/layout immutability remain required.

Fresh verification on 2026-10-14:

- The standard-library/unit/integration command below passed 41 tests in 36.095 seconds, including
  actual OpenSpec 1.14.0/Node validation of all copied main specs and the active
  change with unchecked tasks. An intentionally invalid delta produced genuine
  nonzero findings with a retained valid bulk JSON report. All six PHP fixture
  checks completed after local failure. Malformed stdout remained available.
- Focused reports/adapters/pre-flight and actual Node-descendant cancellation
  checks passed 21 tests in 6.422 seconds. They cover backend/cleanup/identity
  spoofing, bulk version/root/totals, genuine/null codes, missing/incompatible
  tooling, and SIGINT/SIGTERM termination of local Node plus PHP fixture workers.
- The expanded 12-case actual npm/Node/Lefthook PTY suite passed in 280.989 seconds.
  Its phase matrix now includes `openspec-probe`, `openspec-launch`, and
  `openspec-report`, with SIGINT and SIGTERM, alongside the existing directory,
  atomic-write, installed Git/manual, repeated-signal, overlap, and cleanup cases.
  Two focused actual Node/descendant cases subsequently passed in 14.913 seconds:
  version-probe interruption before allocation and validation interruption with
  concurrent PHP fixture jobs. Together these runs exercise 13 distinct terminal
  cases; all assert no owned process/container survivors and return within the
  shared ten-second deadline, without tracebacks or a stuck frontend.
- Strict all-items OpenSpec validation passed all four items (three durable
  specs and this active change). No contributor index, stash, hooks, branches,
  remotes, Composer scripts, dependencies, or PHP-image tooling were changed.
- Final static review passed `git diff --check`, confirmed valid local links in
  both updated conventions, and compared all 55 historical checked task
  descriptions against HEAD unchanged. Discovery lists 55 tests: 41 standard
  cases plus 13 terminal cases passed; the remaining real-native case is blocked
  as described below. OpenSpec apply reports 60/62 tasks complete (`ready`).

```sh
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_reports test_qa test_runner test_containers test_preflight test_hooks_integration.HookIntegrationTests
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_terminal
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_integration.NativeAcceptanceTests
```

The required real Docker/native acceptance is **not verified**. On this daemon,
both `docker exec` and Compose `exec -T` exit zero before their remote process
finishes. A standalone `sleep 2; echo native-exec-complete` returned in about
0.56 seconds without its completion output; inspection during the initial
acceptance attempts showed `git push`, Lefthook, the hook coordinator, and the
OpenSpec version probe still running after the client had returned. This makes
the returned code/output unusable as evidence of native command completion.

The native fixture now checks a delayed completion sentinel before starting any
hook work. Its latest attempt failed that environment prerequisite in 7.522 seconds
with `Docker exec returned before its process completed; native acceptance is
unavailable`. The fixture includes a real invalid-delta case for the next run,
but it has not reached that case. Earlier attempts could leave late-created QA
containers after fixture shutdown; nine containers were identified by their exact
test-run ownership/project labels and removed explicitly. A subsequent query for
`php-qa-scope.execution` containers was empty. Existing unrelated services remain
outside fixture cleanup scope.

Tasks 12.6 and 12.7 remain unchecked, and archive readiness remains suspended.
Next, restore reliable Docker exec/attach completion, rerun the complete native
acceptance (including valid/invalid OpenSpec reports and cancellation), confirm
owned-container absence, and finish the parity/evidence review. Logs under
`tmp/openspec-*-tests.log`, `tmp/openspec-local-cancellation.log`, and
`tmp/openspec-native-test.log` are supplementary provenance; the commands,
outcomes, limitation, and next action are recorded here independently of them.

## Historical Six-Check Evidence

The original push-only implementation, env-file centralization, Yarn installation,
and hook convention revision completed 33 tasks. Their native/runtime/documentation
evidence is retained below for the behavior actually verified.

The eight Git/manual and complete cancellation tasks (9.1–9.8) are historical
evidence for shared-service QA with a PHP supervisor. Section 10 replaced that
boundary with owned temporary containers and confirmed removal, verified by 45
tests using the flat artifact layout. Section 11 groups retained artifacts by
validation and purpose, verified by 48 tests. Historical grouped-layout evidence is
recorded first below; earlier records remain evidence for the behavior and layout
they actually verified.
Composer dependencies/scripts, public package interfaces, and native tool scope
policies were not changed in the working repository. Controlled script mutations
exist only in disposable acceptance fixtures.

## Grouped Artifact Layout And Full Retention Evidence

The implementation stores outcomes under `jobs/{id}.json`, container metadata
and creation/cleanup evidence under `containers/{id}/`, and native reports plus
`execution.log` under `results/{id}/`. QA Scope uses `result.log`,
Sniffer/Fixer/PHPMD/PHPStan use `result.json`, and PHPUnit uses
`result.junit.xml`. Staged stdout uses `results/{id}/stdout.log` with unchanged
atomic publication and malformed-output handling; scheduler output uses root
`runner.log`.

Runtime, summary, process, and cancellation paths, record schema version 3,
ownership, scopes, genuine/null codes, and cancellation/removal semantics stay
unchanged. Composer/script arguments change only their report destination paths.
Every generated evidence file remains until manual cleanup after success, failure,
and interruption; Docker removal never deletes that evidence.

All **48 discovered tests passed**, with no skips, across the complete inventory:

```sh
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_reports test_qa test_runner test_containers test_preflight test_hooks_integration.HookIntegrationTests
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_terminal
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_integration.NativeAcceptanceTests
openspec validate configure-git-qa-hooks --strict
git diff --check
```

The 36 unit/policy/container/dispatcher cases passed in **14.462 seconds**,
the 11 PTY/process cases in **278.565 seconds**, and real Docker/native acceptance
in **153.579 seconds**. Three new regression cases cover grouped-directory
symlink/context rejection, interruption inside directory creation with retained
partial evidence, and rejection of native JSON as a substitute for a missing job.

[Terminal fixtures](../../../tools/git_hooks/test_hooks_terminal.py) cover both
signals before, inside atomic creation, and after publication of the new jobs
and per-validation report/container directories. The manual matrix has 42 phases
and the installed Git matrix 17 phases, each with SIGINT and SIGTERM, alongside
existing input/probe/native/publication, repeated-signal, overlap, late-create,
and unavailable-Docker cases. The actual frontend recovers without EOF, traceback,
spinner, or owned local/native/container survivors within the shared deadline.

[Native acceptance](../../../tools/git_hooks/test_hooks_integration.py) retained
fifteen grouped-layout runs, UTC IDs `20261013-002850-607` through
`20261013-003059-877`, under
[`tmp/git-hooks-verification/native-reports/`](../../../tmp/git-hooks-verification/native-reports).
They contain one permitted Git push, two permitted attached/detached manual runs,
one intentional Git rejection, one intentional manual rejection, six signals at
creation/identity/start barriers, and four active-native-work cancellations
including repetition and overlap. The five completed runs retain all six native
reports, execution logs, job records, container metadata/creation evidence,
runtime/process identities, and scheduler output at the agreed paths. Job and
summary references use execution-relative grouped paths; process registrations
use the revised creation-receipt paths.

An existing flat-layout fixture retained identical filenames and bytes throughout
native success, rejection, and interruption. Unit fixtures also confirm old-run
retention during collisions and overlapping allocation. No historical run is
migrated, renamed, pruned, or used for recovery.

Successful daemon queries confirmed complete current-run container absence after
every native outcome. Shared services, mounts/networks, existing volumes, unrelated
work, and overlapping executions survived; no newly allocated temporary anonymous
volumes remained. The ten interrupted summaries were published 3.514, 5.083, 3.051,
4.481, 3.222, 4.454, 5.459, 3.405, 2.953, and 4.218 seconds after cancellation
began, all within ten seconds without unconfirmed cleanup. A final successful
execution-label query returned no containers.

[Artifact conventions](../../../conventions/artifacts.md) define the grouped layout
and all-outcome retention; [hook conventions](../../../conventions/git-hooks.md)
reference that contract. Python AST, local Markdown references, strict OpenSpec,
and diff checks passed. All 49 historical checked task descriptions are preserved.
Package/consumer files and Composer scripts/dependencies were unchanged. No
contributor hook installation/reinstallation, staging, commit, push, or archive
operation occurred. All six section 11 tasks and the final tracking/parity review
are complete: **55/55 tasks**. The change is ready for archive review.

## Historical Temporary Containers And Complete Removal Evidence

The implementation executes each existing Composer/script/report argv directly
in a temporary container using the active PHP image, environment, user, working
directory, mounts and modes, and project networks. Creation uses automatic
removal, Docker init, and `--pull never`; no dependency installation, image build,
service restart, persistent QA service, or container-side PHP/shell supervisor is
introduced. `php-process.php` and its obsolete cancellation adapter were removed.

Per-run reserved names/ownership labels and immutable Docker IDs are recorded
before native startup. A registered local create-request owner retains its
acknowledgement when a Lefthook job is killed. Cleanup reconciles pending/late
creation, removes created-but-never-started and running/stopped objects, and
requires successful daemon queries proving current-run absence. Docker absence,
not client exit or stopped state, enables successful completion. Native success
with unconfirmed cleanup remains unsuccessful.

Current verification uses the complete standard-library case inventory, split
between native acceptance and the remaining policy/report/PTY/container cases:

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_integration.NativeAcceptanceTests
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_hooks_terminal test_containers test_qa test_reports test_runner test_preflight test_hooks_integration.HookIntegrationTests
openspec validate configure-git-qa-hooks --strict
git diff --check
```

All **45 tests passed**, with no skips: the remaining 44 policy, report,
container, dispatcher, and PTY cases passed in **253.882 seconds**, and the
native acceptance case passed in **157.400 seconds**. It retained fifteen
runs, `20261012-215849-054` through `20261012-220058-810`, under
[`tmp/git-hooks-verification/native-reports/`](../../../tmp/git-hooks-verification/native-reports).
They cover one permitted Git push, two permitted attached/detached manual runs,
one intentional Git rejection, one intentional manual rejection, six signals
at real creation-acknowledgement/ID/start barriers, and four native-work
cancellations including repetition and overlap. All five completed runs retain
six valid native reports and the correct mode. Manual runs leave remote refs
unchanged.

Successful Docker queries verified that every owned created/running/stopped
container was absent after each run. Native work and its PHP descendant were
alive in the temporary container before cancellation; removal terminated that
work while unrelated shared-service work and a simultaneous execution survived.
The ten interrupted summaries were published 2.875, 5.266, 3.248, 4.436, 3.393,
4.332, 5.280, 3.823, 3.196, and 3.990 seconds after their cancellation starts,
all within the shared ten-second deadline, with no unconfirmed cleanup.

Actual image, configured environment, user, working directory, network IDs,
mount destinations/modes, Docker init, automatic removal, disabled TTY/stdin,
and Composer entrypoint were verified against the active PHP template. Docker
Desktop reports inherited bind sources with VM-internal aliases; acceptance
compares mounted device/inode identity as well as access modes, rather than
requiring equivalent host paths to have identical spelling. No newly allocated
anonymous volumes appeared; existing mounts and shared resources remained intact.

The container/PTY cases cover genuine fast zero/nonzero outcomes with automatic
removal, unknown creation/start/client-interruption codes, missing identities,
foreign names/IDs, creation finishing after frontend/job death, atomic ID
publication, both signals across lifecycle/removal phases, repeat escalation,
six-container cleanup, overlap isolation, and unreachable Docker. A missing or
unreachable daemon is diagnosed as unconfirmed cleanup; it is never inferred
from an inspect/list/remove error that resources disappeared.

Only contributor automation, conventions, tests, and change evidence were
updated. Package source/public interfaces, Composer dependencies/scripts, native
scopes, the Lefthook pin, marker/bootstrap, Git policies, and human bypass
authorization remain preserved. No contributor hooks were reinstalled, and no
staging, commit, real push, or archive operation was performed.

Strict OpenSpec validation, Python module parsing, diff whitespace, and all 13
local references in the changed Markdown documents passed. Final review confirms
that the 41 historical task descriptions and checkboxes are preserved and that
the 45 discovered cases are covered by the two passing invocations above.
Successful Docker queries after verification found no remaining containers with
the execution ownership label. At section 10 completion, its eight tasks were implemented and
verified. That readiness applied to the flat layout; current grouped-layout
acceptance and tracking are recorded above.

## Historical Manual Invocation And Cancellation Evidence

Fresh complete verification on 2026-10-12:

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py'
openspec validate configure-git-qa-hooks --strict
git diff --check
```

All **34 tests passed**, including native acceptance, in **89.181 seconds**, with
no skips. Strict OpenSpec validation, PHP helper syntax, Python module parsing,
diff whitespace, and changed Markdown local-reference checks passed.

[Terminal fixtures](../../../tools/git_hooks/test_hooks_terminal.py) exercise the
actual npm/Node/Lefthook 2.1.16/Python chain. They verify:

- Exact manual invocation on clean attached/detached checkouts with terminal stdin
  open, six outcomes, manual mode, and unchanged fixture remote references.
  Dirty/unborn checkouts, invalid context, and forged frontend identities reject.
- SIGINT/SIGTERM across 23 manual lifecycle/publication phases, including signals
  inside initial, result, and final atomic writes. Repeated interruption during
  consolidation leaves parseable interrupted metadata and retains completed work.
- Cancellation inside seven actual Git/runtime probe classes and the real
  open-input selector, rather than only before those operations.
- Installed launcher cancellation during actual local Git pushes across eight
  phases, including active six-job QA, with unchanged remote refs/index/stash.
  Empty Git input remains an early return and never selects manual QA.
- One five-second graceful interval followed by forced cleanup of an ignoring
  local probe; a second received signal forces cleanup earlier. All owned fixture
  processes stop within ten seconds, without EOF, traceback, or a surviving frontend.
- Overlap isolation and explicit unsuccessful PHP-cleanup diagnostics when
  confirmation is unavailable.

The terminal reproduction showed that native cancellation can kill the command
group, including an ordinary guardian. The implemented guardian lives in a
separate session, verifies parent/frontend identities, and retains the cancellation
owner through teardown. Local and PHP startup gates publish ownership before
external commands begin; lifecycle helpers supervise processes without scheduling
the six validations themselves.

[Native acceptance](../../../tools/git_hooks/test_hooks_integration.py) used
separate dev/php services, real Composer/native tools, read-only dependencies,
the installed npm package/platform binary, and a fixture-only bare remote.
The latest nine runs are retained in
[`tmp/git-hooks-verification/native-reports/`](../../../tmp/git-hooks-verification/native-reports):
`20261012-195355-416` through `20261012-195429-904`.
They contain one permitted Git push, two permitted attached/detached manual runs,
one intentional Git rejection, one intentional manual rejection, and four
interrupted manual runs. All five completed runs retain all six native reports
and outcomes with the correct mode. Manual runs leave remote references unchanged.

Cancellation verified both the real PHP process and its descendant were alive
before interruption and stopped afterward. An unrelated native session and a
simultaneous execution remained alive when the first run was cancelled. Interrupted
summary publication took 0.248, 0.312, 0.534, and 0.243 seconds from the respective
cancellation deadlines' start, all below ten seconds, with no unconfirmed cleanup.
Repeated received signals publish the forced-cleanup flag without extending the
shared deadline. Completed reports remain available; unknown codes stay null.

[Hook conventions](../../../conventions/git-hooks.md) and
[artifact conventions](../../../conventions/artifacts.md) now describe both modes,
explicit launcher reinstallation, process identities, cancellation deadlines,
and truthful interrupted/incomplete states. Existing bypass authorization,
distribution exclusions, branch/tag/deletion policies, pin/setup/runtime failure
checks, native argv/report adapters, and contributor-state isolation remain verified.
No contributor hooks were reinstalled and no staging, commit, push, or archive
operation was performed in this working repository.

## Hook Convention Revision

`conventions/git-hooks.md` now owns the five migrated sections:

- `Git Hook Dispatcher`, `Pre-push Runtime And Installation`, and
  `Pre-push Validation And Result Ownership` moved from the environment convention.
- `Pre-push Policy` and `Agent Response To Hook Failure` moved from the Git convention.

Section comparison confirmed that the pin, commands, environment migration,
runtime prerequisites, reference/checkout policies, report adapters/context,
automation verification, and existing failure-response instructions were retained.
Relative links were adapted to the new location. The Git/environment conventions
retain their general responsibilities and refer to the new hook convention;
canonical report formats and retention remain in `conventions/artifacts.md`.

The negative rule begins `Agents MUST NOT bypass repository hooks` and requires
explicit human authorization for the specific operation. Review of the three
spec scenarios confirmed:

| Scenario | Documented authorization outcome |
| --- | --- |
| Human authorizes a push before any failure | Push authorization does not authorize bypass. |
| Human requests a fix or retry after a failure | The instruction does not authorize bypass, and existing failure diagnosis/response obligations remain. |
| Human explicitly authorizes bypass for one operation | Authorization is limited to that operation and does not carry over to another. |

The rule covers `--no-verify`, `LEFTHOOK=0`, disabling hooks, and equivalent
mechanisms, before and after failures. The existing requirement to explain failures
and await a new instruction before corrective actions/restaging/retries remains.
The scoped installation flag `CI=1` is documented as a package postinstall control.

The new front matter declares `id: git-hooks`, title `Git Hooks Convention`, and
read triggers for installation, configuration, execution, verification,
troubleshooting, documentation, and bypass decisions. `AGENTS.md`, repository
documentation boundaries, and the current OpenSpec context map direct agents to
the new source. All 29 local file/anchor links in the affected convention/index
documents resolved. Migration ownership, artifact parity/self-sufficiency, strict
OpenSpec validation, and diff checks passed.

The completed convention revision changed documentation and the OpenSpec context
map. Its runtime files, Composer/native QA configuration, and canonical report
convention were unchanged.
The prior image build and all-25-test native acceptance remain valid evidence for
the unchanged runtime; builds and Python/native suites were not repeated for this
documentation revision. Tasks 8.1–8.5 supplement the preserved 28 completed tasks.

## Yarn Installation Evidence

The revised dev Dockerfile built successfully on Linux amd64 as
`php-qa-scope-hooks-yarn:verification`. It installs `lefthook@2.1.16` through Yarn
after `corepack enable`, with installation-scoped `CI=1` and the retained exact
version smoke check. The custom architecture/download/checksum block and unused
`TARGETARCH` argument were removed; shared tools remain available. The hook
convention now documents the pin, existing Node/package dependencies, and recreation
prerequisite. Yarn/package metadata supplies integrity instead of independent
hardcoded GitHub asset checksums. Arm64 execution was not tested locally.

The installed command resolves to the official package's `bin/index.js`, and
`get-exe` resolves the version-matched `lefthook-linux-x64` native dependency.
Both wrapper and native binary report `2.1.16`; `setup-git-hooks` is executable
and retains its exact version check. In a disposable Git repository with a valid
pre-push configuration, a forced Yarn package installation with `CI=1` created no
hook; subsequent explicit `lefthook install pre-push` succeeded. CI is absent from
the image environment outside that installation command. Activation remains
owned by `setup-git-hooks`.

Isolated fixtures now link to the installed command rather than copying its Node
wrapper, preserving relative imports and platform package files. Restricted PATH
tests provide Node when checking missing Python. The generated launcher retains a
native-binary fallback, so an unavailable explicit `LEFTHOOK_BIN` tests dispatcher
failure without accidentally exercising that fallback. A separate wrapper check
verifies that missing Node fails clearly. The implicit fallback to the old
downloaded verification binary was removed from test discovery.

The complete standard-library suite passed all 25 tests with no skips, including
native acceptance:

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 \
QA_HOOKS_NATIVE_DEV_IMAGE=php-qa-scope-hooks-yarn-acceptance:verification \
QA_HOOKS_TEST_LEFTHOOK="$PWD/tmp/git-hooks-verification/yarn-prefix/bin/lefthook" \
PYTHONPATH=tools python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py'
```

The local test command came from an isolated Yarn installation of the same pinned
package. The native acceptance image uses the rebuilt dev image plus Docker and
Compose executables from the active feature-enabled dev image. No replacement
Lefthook executable is mounted. Acceptance verifies the package identity/version,
Node wrapper, resolved platform binary, and exact version inside the image before
installing hooks in its disposable repository. It preserves env-file bootstrap,
service `env_file` delivery, and read-only dependency mounts.

- Run `20261012-163308-087` permitted the content push: all six commands returned
  0, all six reports were valid, and the scheduler/summary passed.
- Run `20261012-163315-420` rejected the intentional managed PHPCS text drift:
  QA Scope returned 1, the other five commands returned 0, all six reports were
  valid, and the scheduler/summary failed after all jobs completed.
- Both fixture checkouts/indexes remained clean, stash stayed empty, and disposable
  services were removed. The suite also reverified concurrent dispatch, overlapping
  runs, signal handling, launcher forwarding, installation conflicts, and archive
  exclusions. No Python caches remained or real repository hooks were installed.

Reports remain under `tmp/git-hooks-verification/native-reports/` as supporting
evidence; the durable results above do not depend on that ignored directory.
Strict OpenSpec validation and diff checks passed after the Yarn revision.
These outcomes remain the runtime evidence for the completed convention revision.

## Env-file Centralization

`QA_HOOKS_SERVICE=dev` is declared in `docker/dev/.env.example` and the ignored
local `docker/dev/.env`. Its inline Compose declaration was removed; the existing
dev `env_file` now supplies it. Other local values were preserved, and the local
file remains ignored by Git.

`docker compose config --format json` resolved the marker to `dev` with no inline
override. Isolated bootstrap checks confirmed that a fresh file copies the updated
example and rerunning bootstrap preserves an existing custom file byte for byte.
Missing/incorrect marker checks still reject invoked pushes. The hook
convention now documents targeted migration of existing files and dev recreation;
there are no automatic env rewrites or new lifecycle checks.

## Prior Automated Evidence

The complete standard-library suite passed all 25 tests with native acceptance
enabled after the env-file revision:

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools python3 -B -m unittest discover -s tools/git_hooks -p 'test_*.py'
```

Policy fixtures use real temporary SHA-1/SHA-256 repositories for reference
classification, source-branch identity, detached annotated/lightweight/non-commit
tags, cleanliness, and ignored output. Report fixtures verify exclusive UTC
allocation, collisions, independent outcomes, valid/missing/malformed reports,
foreign/incomplete result records, scheduler launch failures, and summary failure.

Pinned Lefthook integration verifies actual simultaneous six-job execution with
a synchronization barrier, continuation after failure, overlapping independent
runs, real SIGTERM handling, unchanged checkout/index/stash state, opaque remote
argument/stdin forwarding, missing dispatcher/Python diagnostics, idempotent
installation, custom hook paths, unmanaged conflicts, and pre-push-only installation.

## Prior Native Acceptance

Disposable Compose dev/php services and a local bare Git remote exercised the
assembled Git → Lefthook → Python → Compose → Composer flow. The fixture uses the
existing feature-enabled dev/php images, mounts the verified pinned dispatcher,
bootstraps `docker/dev/.env` from the current example, and loads the dev marker
through the service's `env_file`, with no inline service `environment` assignment.
It confirms `printenv QA_HOOKS_SERVICE` returns `dev` and supplies the Docker
socket's actual group. Development dependencies are mounted read-only; the fixture
never uses contributor remotes/index/stash.

- A permitted branch push returned success. All six native commands returned 0,
  all six primary reports parsed, and the scheduler/summary recorded success.
- An intentional managed PHPCS text drift (`.` → `./`, preserving native scope)
  made QA Scope return 1. The other five checks returned 0, all six reports were
  valid, and the scheduler/summary rejected the push after all checks completed.
- Both runs left their fixture checkout/index clean and stash empty. Fixture
  services were removed. No hook was installed in the contributor's repository.

Retained local evidence is under `tmp/git-hooks-verification/native-reports/`.
That ignored path is supporting evidence; the acceptance behavior and outcomes
are reproduced here so this record does not depend on transient files.
The env-file acceptance runs are `20261010-162621-637` (passed) and
`20261010-162628-167` (QA Scope rejected), using the UTC report naming convention.

## Prior Build, Distribution, And Scope

The prior dev Dockerfile built successfully on Linux amd64. The resulting image
reported Lefthook `2.1.16` and an executable `setup-git-hooks`. Published SHA-256
checksums pin official amd64/arm64 assets; arm64 execution was not tested locally.
An isolated Git archive excluded Lefthook/internal tooling/logs/conventions and
retained package metadata. No Python bytecode files or fixture containers remained.

Diff/scope review confirmed Lefthook-owned parallelism, one Python scheduler
invocation, exclusive per-run evidence, coordinator-only summaries, manual
retention, and no lock/stash/recovery/index-fingerprint or corrective commands.
The Python suite is not in the pre-push matrix. No start/attach checks were added.

`openspec validate configure-git-qa-hooks --strict` and `git diff --check` passed
after the env-file revision. Contributors must supply the marker in the dev env
file and
recreate dev to load it; a restart does not reload env-file values. Initial hook
activation still requires dev rebuild/recreation and post-create or explicit
`setup-git-hooks`. The completed Yarn installation evidence above supersedes the
previous binary-installation mechanism; the hook convention revision records
the prior documentation verification. Current implementation evidence is recorded
in `Temporary Containers And Complete Removal Evidence` above; these older
results do not establish the temporary-container lifecycle or removal guarantees.
