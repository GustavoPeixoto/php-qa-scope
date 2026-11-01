# Verification

The 2026-10-20 evidence and initial 2026-11-01 continuation below are historical.
Current design and validation are recorded under the individual-check revision.

Date uses America/Sao_Paulo; execution logs extend into 2026-10-21 UTC.

## Implementation and local evidence

The working tree adds shared Node/OpenSpec tooling, Composer distribution
extraction in PHP tooling, the native CI adapter, the seven-entry PR workflow,
defensive `QA Required` aggregation, contract/runtime/native tests, and contributor
conventions. Package behavior, dependency versions, Composer scripts, shared hook
helpers/runtime, release workflow files, and package version remain unchanged.
The release workflow test's explicit filename allowlist now includes `qa.yml`.

| Verification | Result |
| --- | --- |
| Standalone Node and PHP tooling builds | Passed without development arguments |
| Default Node development build and PHP development target | Passed with workspace argument |
| Real locked Composer install, development dependencies included | Passed; lock byte comparison unchanged |
| Focused runtime tests | 2 passed: shared Node/OpenSpec and PHP/Composer versions, Xdebug isolation, user/workspace, sudo, Lefthook, assistant tools, scripts, root/user OpenSpec configuration |
| Adapter and workflow discovery suite | 17 tests: 13 passed, 4 opt-in runtime/native tests skipped in default discovery; those probes were executed separately |
| Release workflow/CLI/authority/validation tests | 21 passed |
| Actionlint 1.7.12 | Passed |
| Zizmor 1.31.1 | No findings in offline mode |
| Seven real native checks and aggregate | Passed against the clean exported revision below |
| Intentional native QA Scope finding | Failed with genuine exit 1, valid native report, and retained diagnostics |
| Real missing-command startup and SIGTERM cancellation | Passed: null unknown native code, unsuccessful outcomes, preserved available stdout/stderr, owned container removed |
| Git diff whitespace validation | Passed |
| Strict selected-change and all-project OpenSpec validation | Passed; all 6 items valid (1 change, 5 specs) |

Native smoke used committed package revision
`e4c36dd0f1d1f11fc5f9df8dad6f4d74356bbec9` and the current working adapter.
The fixture exports committed blobs using read-only `ls-tree`/`cat-file`, with
read-only access to the original Git metadata for HEAD comparison. All seven
native validators ran through the new tooling images, and aggregate mode
revalidated their retained evidence. Full tracked-content comparisons against
HEAD passed before/after execution, and after restoring the deliberately changed
QA Scope target. Fixture-only environment examples/markers are removed after
those assertions to keep transient copies ignored. No contributor Git state was
changed. GitHub execution against an implementation merge revision is still
unverified.

Retained local provenance (the results above are self-contained):

- Successful direct-entrypoint native smoke and aggregate:
  `tmp/pr-qa-native-f5zjfwx3/logs/pr-qa/`; its downloaded artifact fixture retains
  all seven successful reports, while the check directory retains the intentional
  QA Scope failure.
- Final missing-command/cancellation probe:
  `tmp/pr-qa-cancel-71nt62zy/`; outcome is cancelled, code is null, available
  `native-started` stdout is retained, and the before/after owned-container
  inventory matches.

The adapter explicitly selects the shared executable as Docker's entrypoint.
This prevents a stock image entrypoint from interpreting an unavailable command
as another runtime's input. Docker/tini spawn failures retain startup diagnostics
without claiming a genuine native command exit. Normal native findings preserve
their actual codes, and invalid reports remain failures even after native zero.

## Hook verification limitation

The unchanged hook suite ran 61 tests: 3 failures, 1 error, 1 opt-in native skip.
The new adapter/workflow tests and native CI probes pass, but full hook acceptance
is **not green**; task 2.4 remains incomplete.

- `test_real_openspec_cli_valid_specs_unchecked_tasks_and_invalid_delta` assumes
  `configure-git-qa-hooks` is an active OpenSpec item. It was archived under
  `openspec/changes/archive/2026-10-16-configure-git-qa-hooks/`. The failure
  reproduced in isolation. The user explicitly requested leaving this test
  unchanged and recording the baseline failure.
- `test_installed_git_input_cancellation_and_empty_never_manual` encountered a
  disappearing `/proc/.../fd/3` while reading fixture process descriptors. Its
  targeted retry passed.
- `test_sigint_sigterm_every_phase_actual_npm_frontend` failed two cancellation
  subcases when the fake Docker engine tried to read an already-removed metadata
  file and emitted a traceback. Its targeted retry also failed two subcases,
  including `final-atomic`. No hook/runtime/fake-engine code was changed.

These timing results were observed in unchanged code during this session;
pristine-baseline reproduction and repair of the cancellation fixture remain
outstanding. They must not be presented as successful hook regression acceptance.
The adapter itself passed a real SIGTERM interruption with container cleanup.

## Remote rollout and enforcement

No authenticated GitHub administration session was established. GitHub CLI is
unavailable in this development shell. No live ruleset or check integration was
authenticated/reread, no implementation PR was created or integrated, and no
repository protections or Git refs were changed. Public documentation and local
tests cannot establish remote activation. Tasks 4.1–4.3 remain incomplete.

Local contracts establish scheduling eligibility for ordinary, documentation-only,
draft, fork, and release PRs, and preserve the release job's existing condition
and exact name. No real PR evidence exists yet for those categories. Fork runs
can require GitHub approval. Successful ordinary QA alongside an emitted skipped
release check, actual failed-QA merge blocking, zero approvals, up-to-date
enforcement, empty main bypass, and retained main/tag protections all require
authenticated rollout verification.

The next rollout must first disclose concrete Git/GitHub operations and obtain
the explicit authorization required by `conventions/git.md`. Integrate through
the existing infrastructure PR/check process, without a release branch, version
change, merge solely for a probe, or tag publication. Observe `QA Required` on the
intended merge revision and its actual GitHub Actions integration. Inspect the
current `Protect main` ruleset, append that identity alongside every existing
required check, then authenticate a reread of every retained protection. Historical
ruleset/integration IDs in conventions are discovery hints only. Coordinate
mutating enforcement probes explicitly and record remaining production limits.

Rollback ordering was reviewed against the design and release convention: restore
the prior required-check list **before** removing the QA workflow. Retain
`Validate Release Branch`, all other required checks, zero approvals, up-to-date
enforcement, empty main bypass, main deletion/force-push protection, and existing
App/tag rules. Do not remove hooks or historical evidence. No live rollback was
performed or claimed.

## Consistency and completion boundary

Proposal, design, spec, and tasks retain the same seven-check contract, shared
tooling scope, read-only PR authority, evidence rules, and remote activation
requirements. Temporary paths above are provenance; no implementation decision
depends on their continued availability. The change must remain active while
hook acceptance and remote rollout are incomplete; it has not been archived.
The apply handoff is 18/22 tasks complete, with task 2.4 and tasks 4.1–4.3
remaining open. No archive or Git/GitHub mutation is authorized by this handoff.

## Continuation — 2026-11-01

### Accepted rollout and starting state

Continue on `change/release-validation-tooling` with one PR targeting `main` in
`GustavoPeixoto/php-qa-scope`. Its reviewed scope includes the five existing
commits after main and the PR QA implementation. Each contributor Git/GitHub
mutation still needs its concrete operation-specific authorization. The user
declined intentional failed-QA probes and additional probe PRs; missing remote
eligibility/blocking evidence will remain explicit and task 4.3 stays open.

Starting HEAD is `32dafbbd8bc86e1b3bdcac5f03d33e666289f1eb`, including the completed,
archived synthetic-fixture correction. The index already contained new QA files;
other QA modifications were unstaged and the active change was untracked. The
initial staged-diff SHA-256 was
`8c9db160f82317f4da119ff4752d405663421ec2097473981be4efadc442a6c1`.
The only stash present at this continuation's start was
`9f5472b9588ae8fc75d3362cdd6bb797fd64ce36` (`On main: TODO`). This continuation
has not staged, committed, pushed, restored stashes, or changed branches.

Composer manifest/lock SHA-256 baselines are respectively
`b02cce4712d5e1e1d7d733a4c4a3a977f85439d65cb56b46fd90ffcaf4837b2e`
and `81fed68579e88618d755ada303516837f01802d14f577a39026844eec3665260`.
Package source, Composer scripts/dependencies, shared hook runtime, and release
workflow files are unchanged relative to this HEAD. Temporary evidence for this
continuation is under `tmp/pr-qa-continuation-gCkDQBKE/`; the substantive results
and decisions are recorded here rather than depending on those files.

### Fresh local validation

- Default PR QA discovery passed 17 tests, with the four runtime/native opt-ins
  skipped in that invocation and executed separately below.
- The complete release suite passed 23 tests after a retry. Its first run's
  PHP/Composer runtime test received empty attached stdout; no release test or
  runtime code was changed to obtain the successful rerun.
- All four images built from the current Dockerfiles, including both standalone
  tooling targets and the default Node/PHP development environments. The mutable
  Node base currently provides 24.22.1; Dockerfile version references and all tool
  pins remain unchanged.
- Both focused runtime tests passed after making the new probe helper inspect
  terminal container state and read retained Docker logs before removal. The
  original helper failed twice with empty OpenSpec stdout. A disposable proof
  container exited zero with empty attached stdout while `docker logs` contained
  `1.14.0`. The adjustment changes only the test helper and its contributor
  documentation; the CI adapter/workflow are unchanged.
- Real native adapter acceptance passed both tests, covering the seven checks,
  aggregate, locked dependency install, genuine local findings, missing-command
  startup, SIGTERM, retained streams, and owned-container cleanup. The successful
  baseline and downloaded artifact evidence are in `tmp/pr-qa-native-ti8e5kel/`;
  startup/cancellation evidence is in `tmp/pr-qa-cancel-2mejrmv2/`.
- Native smoke exported clean committed HEAD `32dafbb` and used the current
  working adapter. Tracked content and lock comparisons passed. A wrapper wrote
  a completion receipt on the mounted checkout before returning: exit code 0,
  2 tests in 27.470 seconds, no skips. This avoids trusting the local Docker
  client's attached exit/stream alone. It does not prove execution of the future
  PR merge revision on GitHub.
- Actionlint 1.7.12 passed; Zizmor 1.31.1 reported no findings in offline mode.

The first combined hook suite ran 66 tests with one failure, one error, and the
expected opt-in native skip. The error was the existing `/proc/.../fd/3` race in
`test_installed_git_input_cancellation_and_empty_never_manual`; its isolated retry
passed in 1.213 seconds. The phase matrix failed in
`containers-tool-directory-created` when the fake Docker engine read removed
metadata; its isolated retry passed in 166.174 seconds. Neither hook runtime nor
the terminal/fake-engine fixtures were changed. The subsequent full quiet rerun
passed all 66 tests in 383.379 seconds with one expected opt-in native acceptance
skip and no failures/errors. That hook-native opt-in was not rerun in this
continuation; the separately executed two-test native acceptance above exercises
the PR adapter. The fresh combined regression, adapter tests, and startup/signal
evidence now close task 2.4. Current progress is 19/22; only tasks 4.1–4.3 remain
open. Initial failures remain recorded rather than represented as first-run
success.

Both strict OpenSpec commands and `git diff --check` passed during this
continuation. Final read-only checks preserved the original staged-diff digest,
manifest/lock hashes, branch, parent HEAD and the sole starting stash. The only
new implementation edits beyond the restored QA work are the runtime test's
confirmed-state/log capture and its contributor documentation. The running dev
and PHP services remain present, and disposable native/runtime probe containers
have been removed.

### Authenticated remote baseline

GitHub CLI 2.23.0 is available in the current dev environment. Browser
authentication established account `GustavoPeixoto`; a repository API read
confirmed administrative access. Authentication did not configure a Git
credential helper or alter the SSH origin URL. There were no open PRs, and the
remote main head was `7ca2eb885eab285bd3988c21fc92da9ec9c86a23`.

Authenticated reads confirmed active `Protect main` (25322253), targeting only
`refs/heads/main`, with zero required approvals, an empty bypass list, deletion
and force-push protection, strict up-to-date enforcement, and required
`Validate Release Branch` from integration 15368. Active `Protect releases`
(25208186) retains deletion, non-fast-forward, creation and update restrictions,
with sole integration bypass actor 5338805. Mutable-field snapshots are retained
as `ruleset-25322253-before.json` and `ruleset-25208186-before.json` in the
continuation evidence directory. No ruleset was changed.

`QA Required` has not yet been emitted for this implementation in a real PR.
Authenticated baseline inspection is not required-check activation or enforcement
proof. Tasks 4.1–4.3 remain open. The workflow, its eventual PR execution, the
ruleset amendment, and merge each remain subject to their disclosed authorization
and verification steps. No remote failure probe, additional PR, release, package
version change, tag, or archive operation has been performed.

## Individual-check revision — 2026-11-01

### Accepted policy and implementation

The user replaced the aggregate gate with GitHub's native individual required
checks. The explicit merge condition is: every required check must be present
and completed with `success`, `skipped`, or `neutral`; every other state or
conclusion blocks merge, including missing, pending, running, failed, cancelled,
or timed-out checks. This is an explicit list, not an automatic requirement for
future checks. Conditional release validation remains skipped on ordinary PRs.
Skipped/neutral conclusions do not claim that a native validation executed.

The seven emitted names remain `QA (qa-scope)`, `QA (sniffer)`, `QA (fixer)`,
`QA (md)`, `QA (stan)`, `QA (test)`, and `QA (openspec)`. The revised workflow
retains only their matrix job, exact temporary-merge checkout, independent
execution, read-only authority, per-check native validation and always-attempted
uploads. A required upload failure still fails its own check. The aggregate
job, central downloads, cross-artifact gate, and internal `--aggregate` and
`--upstream-result` interfaces have been removed. The check/image/revision
interface, native reports, per-check outcomes and diagnostics remain.

The proposal, design, delta spec, tasks and contributor conventions now describe
this policy. Affected completed tasks were reopened for fresh verification.
Historical aggregate results above remain evidence of the former design, not
proof of this revision. No public package API, PHP source, Composer scripts,
dependencies, Dockerfiles, versions, shared hook runtime, or release workflows
were changed by this revision.

### Fresh local results

Evidence is retained under `tmp/pr-qa-individual-PQJI0U6b/`; the substantive
results and limits are recorded here independently of that temporary directory.

| Verification | Result |
| --- | --- |
| PR QA discovery | 15 tests: 11 passed, four opt-in runtime/native skips |
| Individual CLI and workflow contracts | Passed: required check/image/revision arguments, removed-flag rejection, unchanged seven matrix IDs/names, one checkout, no aggregate/download job, no failure-masking uploads |
| Complete release suite | 23 passed on retry; release identity and ordinary skip behavior unchanged |
| Native adapter acceptance | Two tests passed in 24.601 seconds, no skips, confirmed by mounted completion receipt and container exit 0 |
| Actionlint 1.7.12 | Passed |
| Zizmor 1.31.1 | No findings in offline mode |
| Strict OpenSpec selected-change and project validation | Passed |
| Whitespace and unchanged package inputs | Passed |

The first release run failed one runtime assertion after its attached Docker
client returned empty Composer-version stdout. The unchanged suite passed on
retry. This is retained as a local transport limitation, consistent with the
earlier confirmed-state/log evidence; no release test was altered to hide it.

Native smoke exported committed package revision
`338ae1397268047ab1aeea80115d21421653b177` and exercised the revised working
adapter. Every check passed with its exact identity/revision, genuine zero,
`report_valid: true`, null error, valid retained native report, and available
stdout/stderr files. Findings, missing executable startup and SIGTERM were
verified in controlled local fixtures; owned containers were removed. Native
evidence is in `tmp/pr-qa-native-pumyssys/` and
`tmp/pr-qa-cancel-w7nevdtm/`. These are local acceptance fixtures, not remote
failure probes. Tracked-content and lock comparisons passed.

The two image-version probes and full hook Python suite were not rerun for this
removal-only revision: Dockerfiles, runtime probes and shared hook code remain
unchanged. Their historical successful results are recorded above. The native
adapter's two opt-in cases were executed separately from default discovery.

### PR and protection boundary

The starting checkout was clean on `change/release-validation-tooling` at
`338ae1397268047ab1aeea80115d21421653b177`. PR #6 is open against `main` and has not
been merged. Its existing green seven-check/aggregate run belongs to that old
revision and must not certify the forthcoming update. The new revision still
needs its authorized commit/push and an update to the same PR's body; no new PR
or history rewrite is planned. No staging, commit, push, PR edit, review approval,
merge, ruleset update, stash mutation, release or tag operation was performed
during this revision's local preparation.

An authenticated ruleset read still showed only `Validate Release Branch`
(integration 15368) required in `Protect main` (25322253). No aggregate context
is configured there, so no remote aggregate rule needs undoing. A proposal in
`ruleset-proposed.json` beside its `ruleset-before.json` snapshot adds the seven
individual names, also with integration 15368. Comparing the prepared objects
confirmed that only the required-check list changes; there are eight proposed
contexts in total. All existing parameters, up-to-date enforcement, zero
approvals, empty bypass, main deletion/force-push protections are preserved.
The proposal does not target or change tag protections.

Publication requires a specifically authorized new commit/push/body-edit batch.
Protection application requires separate authorization after the seven checks
and their integration have been observed on the new PR revision, followed by
an authenticated reread. The user's no-review/no-merge and no-intentional-remote-
failure-probe limits remain in force. Missing ordinary/docs/draft/fork/release
or blocking evidence remains explicit and task 4.3 stays incomplete. Source for
the platform conclusion policy is GitHub's required-status-check troubleshooting
documentation; the full allowlist is stated in this change's own spec and does
not depend on that external page to be understood.
