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

## Required-check activation — 2026-11-01

The user specifically authorized applying the prepared `Protect main` amendment,
without review approval or merge. Authenticated confirmation completed at
2026-11-02T00:47:22Z (2026-11-01 21:47:22 America/Sao_Paulo).

Before applying, the live mutable configuration still matched the reviewed
baseline. All seven checks for PR #6 head
`632b549eb23e0c8c63532f9fd015b6419aeef45b` were present, completed successfully,
and attributed to GitHub Actions integration 15368. The authorized PUT to
`repos/GustavoPeixoto/php-qa-scope/rulesets/25322253` succeeded. Its required
contexts are now:

- `Validate Release Branch`
- `QA (qa-scope)`
- `QA (sniffer)`
- `QA (fixer)`
- `QA (md)`
- `QA (stan)`
- `QA (test)`
- `QA (openspec)`

All eight are bound to integration 15368. An independent authenticated GET after
the update exactly matched the authorized mutable payload. Active enforcement,
the main-only target, strict up-to-date policy, zero required approvals, empty
bypass, deletion/force-push blocks, and every other existing parameter were
preserved. A separate before/after read of `Protect releases` (25208186) matched
exactly; no tag rule was targeted. The resulting snapshots are retained as
`ruleset-after.json`, `tags-before-activation.json` and
`tags-after-activation.json` under `tmp/pr-qa-individual-PQJI0U6b/`, alongside
the already recorded baseline/proposal.

PR #6 remained open and unmerged at the same head, with `auto_merge: null`.
GitHub reported `mergeable: true` and `mergeable_state: clean`, consistent with
the seven successful QA checks, skipped ordinary release check, and updated
required list. This is live evidence for successful ordinary-PR eligibility;
it is not a failed-check enforcement probe or a merge attempt.

Task 4.2 is complete. Progress is 20/22: task 4.1 still requires actual
integration, which has not been authorized, and task 4.3 remains open for missing
blocking/eligibility evidence. No intentional remote failure probe or additional
PR was created. No PR approval, merge, Git staging, commit, push, stash change,
release or tag operation was performed as part of this activation. These local
evidence/tracking edits have not been staged or committed.

## Optional preparation caches — 2026-11-02 (UTC)

The accepted cache revision adds separate GitHub Actions caches for PHP tooling
layers, Node/OpenSpec tooling layers, and PHP Composer package downloads. It
preserves the seven independent checks, merge-revision checkout, native adapter,
mandatory locked install, required report uploads, and existing main protection.
The earlier decision to start without caches is superseded, not erased from the
historical execution evidence above.

Official action refs were resolved through authenticated read-only GitHub API
queries: `docker/setup-buildx-action` v3 is pinned to
`8d2750c68a42422c14e847fe6c8ac0403b4cbd6f`; both `actions/cache` v4 subactions
are pinned to `0057852bfaa89a56745cba8c7296529d2fc39830`. BuildKit exports to
a fresh local directory in max mode, loads `pr-qa-tooling`, and replaces its old
export only after success. Only cache restore/save steps tolerate errors.
Composer caches downloads, never installed dependencies or credentials.

### Current local verification

- PR QA discovery: **20 tests, 16 passed, four opt-in runtime/native skips**.
  The new cases execute the actual workflow shell with controlled Docker exits:
  cold build, warm import/export rotation, fatal build failure with preserved old
  cache/log, and successful/failed Composer install with the cache mount and
  temporary Composer home. Contract checks cover family/runtime/input key
  boundaries, current manifest/lock inclusion, publication before QA, all seven
  identities, and tolerance limited to the four cache operations.
- Actionlint **1.7.12** passed for the revised workflow. Its first run caught
  `runner.temp` being unavailable in job-level env; cache-root initialization was
  moved after checkout through `GITHUB_ENV`, then revalidated successfully.
- Zizmor **1.31.1**, offline mode: no findings for the revised workflow.
- Strict selected-change and all-project OpenSpec validation passed: **6/6 items
  valid** (one active change and five specs). Diff whitespace validation passed.
- Real PHP tooling cold build/export: **21.675 s**, exit zero, no cached steps.
  A second build took **1.612 s** and reported two cached steps. An additional
  build using a **fresh isolated BuildKit daemon** successfully imported the
  exported directory, reported two cached steps, and took **7.028 s**. The fresh
  daemon confirms external exported layers work independently of the first
  builder's internal state. Each build retained its log and loaded the image.
- Two clean Composer fixtures used the repository's current manifest and lock.
  The first installed all locked development dependencies in **7.078 s** and
  cached **72 package archives**. A separate empty-vendor fixture installed in
  **2.278 s with Docker networking disabled**, using those downloads. Both
  generated `vendor/autoload.php` and preserved the lock's SHA-256 exactly.
- Native smoke evidence is retained under `tmp/pr-qa-cache-validation/`, including
  summary, build/export/import logs, separate fixture installs, and download
  cache. The statements above record the result independently of those ignored
  paths. The two dedicated BuildKit builders are removed after verification;
  shared services, images, caches, index, and stash are not pruned or rewritten.

These local timings are observations, not a GitHub performance claim: runner,
registry, transfer, and cache-service costs differ. Manifest/lock key invalidation
and warning-only service steps are verified as workflow contracts; actual GitHub
cache restore/save, visibility, eviction, concurrent publication, and observed
cold/warm runtime remain **unverified pending authorized publication**. No package
source, dependency version, Dockerfile, release workflow, or shared hook runtime
changed, so their older native acceptance evidence remains historical rather than
being presented as a new run.

Task 4.5 remains open for real GitHub cache evidence, alongside the existing
integration task 4.1 and missing enforcement/eligibility evidence in task 4.3.
No additional PR, artificial warm-up commit, intentional remote failure, review
approval, merge, ruleset update, staging, commit, push, or stash operation is part
of this local implementation. The existing staged activation evidence is
preserved; this revision is added only to the working tree until authorized.

An authenticated read-only inspection confirmed that `Protect main` still requires
the same eight contexts under GitHub Actions integration 15368 with strict
up-to-date enforcement. PR #6 is still open at `632b549`, unmerged, with auto-merge
disabled. No live rules were changed by this revision. Current progress is
**23/26 tasks complete**; tasks 4.1, 4.3, and 4.5 remain open.

## Cache publication and observed GitHub reuse — 2026-11-02 (UTC)

After explicit authorization of the reviewed eight-file batch, staging and commit
created `9d5588a40f27fd0f60eab3dd527930a797c6e755`
(`ci: cache PR tooling and Composer downloads`). The normal push to
`origin/change/release-validation-tooling` ran the installed hook without bypass:
all seven native pre-push validations passed, with evidence retained under
`logs/prepush/20261102-013101-955/`. The exact approved PR #6 body was applied
and independently compared with its source file. Title, source/base branches,
open state, disabled auto-merge, reviews, and protections were not changed.

The push started run **41372908956**. The authorized body edit naturally started
run **41372936727**; the existing concurrency policy cancelled the older run.
The older run had already offered PHP layers for publication. This was a normal
superseding event, not a failure probe, extra PR, or artificial warm-up commit.

### Latest-revision acceptance

[Run 41372936727](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/41372936727)
completed successfully at **2026-11-02T01:33:36Z**, for head `9d5588a` and actual
temporary merge revision `0153ceb98221779003063f0992bba13b23ef458a`.
All seven individual `QA (<id>)` checks succeeded, no aggregate was emitted, and
`Validate Release Branch` completed as skipped. All eight contexts were attributed
to GitHub Actions integration **15368**.

All seven `qa-<id>` artifacts were available and downloaded through authenticated
read-only API calls. Each contained its expected nonempty native report and an
outcome for that same temporary merge revision, with native exit zero, valid
report, and `passed` status. PR #6 remained open, unmerged, with `auto_merge: null`;
GitHub reported `mergeable: true` and `mergeable_state: clean`. No approval or
merge was performed.

### Actual cache behavior

- **Across runs:** the earlier run missed the PHP tooling key. Its publication
  was visible to every PHP job in the latest run. Each restored that exact key,
  reported two `CACHED` BuildKit steps, and skipped redundant cache publication.
  GitHub retained **45,544,198 bytes** for that PHP layer entry.
- **Between checks in one run:** `QA (qa-scope)` missed the Composer key,
  installed the locked dependencies, and published downloads at
  **01:32:41.670Z**. `QA (test)` restored that exact key at **01:32:41.981Z**,
  installed its own dependency tree, and passed. The stored entry was
  **20,631,158 bytes**. Other concurrent save attempts logged the normal
  key-reservation warning and their jobs still succeeded, demonstrating
  first-publication behavior without intentional errors.
- **Node/OpenSpec:** its cold build succeeded and published a separate
  **622,727,283-byte** layer entry. No warm Node restore was observed.
- The cache API reported all three entries under **`refs/pull/6/merge`**.
  The exact key boundaries remain those documented in the design: format,
  OS/architecture, tooling family/runtime Dockerfile, and Composer input hashes.

Observed GitHub step durations, rounded to seconds by the jobs API:

| Preparation | Cache restore | Build or install | Cache save |
| --- | --- | --- | --- |
| PHP tooling, latest-run warm entries | 1–2 s | 4–6 s, with two cached steps | Skipped |
| Composer, cold `QA (qa-scope)` | 0 s, miss | 6 s | 1 s |
| Composer, warm `QA (test)` | 2 s | 2 s | Skipped |
| Node/OpenSpec tooling, cold | 0 s, miss | 51 s | 4 s |

These are actual observations, not a controlled speed benchmark. Cache transfer
and extraction have their own cost. Native installation and validation still ran
in every applicable job; no cached success result was substituted.

Read-only inspection provenance and detailed per-job observations are retained in
`tmp/pr-qa-cache-validation/remote-inspection.json`. This section contains the
relevant results independently of that ignored snapshot. Reuse on a different
commit, warm Node restoration, expiration/eviction, and same-runtime fallback
after a changed Composer lock have not been observed remotely. Task 4.5 therefore
remains partially verified and open. Tasks 4.1 and 4.3 also remain open; overall
progress remains **23/26**. The change is not archived.

The authorized Git/GitHub operation batch is consumed. These additional remote
evidence/tracking edits are local only, unstaged and uncommitted; another staging,
commit, push, or PR edit requires fresh specific authorization. The existing stash
is unchanged. No tag, release, ruleset update, review approval, or merge occurred.

## Disposable laboratory preparation — 2026-11-03

The developer accepted an independent laboratory for the remaining 4.3/4.5
observations. Revised 4.3 acceptance combines authenticated original protection
configuration with equivalent laboratory enforcement and explicitly retains the
unobserved real-fork, emitted-neutral, and direct original-main blocking cases.
Functional requirements are unchanged. No second owner is available for a real
fork. Controlled failure fixtures are restricted to the separately authorized
laboratory; original-repository probes remain excluded. Task 4.1 still requires
integration and is outside this validation.

Read-only discovery confirmed public laboratory name
`GustavoPeixoto/php-qa-scope-validation-20261103` returned HTTP 404. The original
`Protect main` remains active with eight required contexts under Actions
integration 15368, strict up-to-date enforcement, zero approvals, empty bypass,
and existing deletion/force-push restrictions.

Local preparation exported **218 tracked files** from immutable source
`9d5588a40f27fd0f60eab3dd527930a797c6e755`, preserving bytes and modes. This
revision has no symlinks. The export is outside the original repository at
`/tmp/php-qa-scope-validation-20261103/checkout`, with no `.git`, copied commit
history, tags, remotes, or installed hooks. Hashes, creation/PR/protection payloads,
and exact Batch 01 scope are prepared under
`tmp/pr-qa-disposable-validation-20261103/`. These paths are provenance; the scope
and acceptance are fully recorded in proposal/design/spec/tasks.

Fixtures cover documentation-only draft/cross-commit revisions, managed PHPCS
scope failure, an omitted test matrix entry, a test-only one-minute timeout with
a controlled wait, exact baseline restoration, and version-0.1.0 Composer inputs
for later fallback and release validation. The existing image's actual Composer
code computes the fixture hash, and offline
`composer --no-plugins --no-scripts validate --strict --no-check-version` passes.
Every lock field other than its content hash is unchanged, so dependencies have
not been upgraded.

Actionlint 1.7.12 and offline Zizmor 1.31.1 passed for both instrumented workflow
variants. Selected/all strict OpenSpec validation passed: **6/6 items valid**.
Diff whitespace validation passed. No remote fixture has executed; tasks 4.3 and
4.5 remain unchecked and progress remains **23/26**.

The first concrete mutation batch is ready for review: create the independent
public repository, initialize/stage/commit/push its root snapshot, disable only
laboratory tag publication, install/reread the copied main ruleset, then
create/stage/commit/push the documentation-only branch and open its draft PR.
Only read-only cold-run observation follows that batch. Later transitions,
probes, reruns, the release PR, closure, and deletion need their own disclosed
authorization. The original repository receives no remote writes; these local
acceptance/evidence edits remain unstaged and uncommitted.

## Laboratory Batch 01 — executed 2026-11-03 (UTC)

The developer specifically authorized the disclosed first batch. Created the
independent public repository
`GustavoPeixoto/php-qa-scope-validation-20261103` (repository ID 1444157567,
`fork: false`). No original-repository Git/GitHub state was written.

The isolated checkout at `/tmp/php-qa-scope-validation-20261103/checkout`
received a new Git database and fixture-local author configuration. Root commit
`cc6c362f18fc9a304dea1cecfac6a8e35d5a5cbf` contains exactly the source snapshot's
218 tracked files, with tree
`85599979ea41eb56c8828a7d13ab675785fd6fe4` identical to source `9d5588a`.
There is one root commit, not copied source ancestry. A second fixture commit,
`c74b9e3f0b54a7a1760d5d44a0add9f942859bef`, adds only the three-line
`LAB_VALIDATION.md` on `qa/acceptance`; code and workflows remain byte-identical
to the seeded main. Both normal pushes targeted only laboratory origin.

The laboratory's `create-release-tag.yml` was disabled through its workflow API,
with file bytes preserved. New laboratory ruleset **26443022**, `Protect main`,
was created from the reviewed original payload. An independent authenticated GET
matched all normalized mutable fields: eight required contexts under Actions
integration 15368, strict up-to-date enforcement, zero approvals, empty bypass,
and the original deletion/force-push and PR parameters. The API confirmed
`current_user_can_bypass: never`. No ruleset was changed in the original.

Opened [laboratory PR #1](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/pull/1)
as draft, `qa/acceptance -> main`, with the exact approved title/body. The copied
workflow ran despite draft status and a documentation-only diff.
[Cold run 41622977546](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41622977546)
completed successfully at **2026-11-03T10:54:51Z**, testing actual temporary merge
revision **`c4e8eccde7a0d3314eead9f2fe38b89228135316`** for head `c74b9e3`.

- All seven individual QA checks succeeded; `Validate Release Branch` was
  skipped. All eight emitted contexts belonged to Actions integration 15368.
- All seven `qa-<id>` artifacts were downloaded. Each contains its expected
  nonempty native report and a passed outcome for the same merge revision,
  with native exit zero and report validity true.
- Logs confirm cold misses for PHP tooling, Node/OpenSpec tooling, and Composer
  downloads. Three entries were published under laboratory cache scope
  `refs/pull/1/merge`: PHP **45,549,773 bytes**, Composer **20,631,008 bytes**,
  and Node/OpenSpec **622,853,249 bytes**. Keys have the same structural inputs
  as production but are isolated by repository and PR scope.
- Observed API-rounded preparation examples: QA Scope's cold PHP build **6 s**
  and locked install **6 s**; OpenSpec's cold build **55 s** and cache save
  **4 s**. These are observations, not a comparative speed benchmark.
- Draft state is deliberately retained. Its inherent merge restriction is not
  reported as evidence that required checks caused blocking.

The export at
`tmp/pr-qa-disposable-validation-20261103/evidence/cold-draft/` retains run/PR/job
metadata, full job logs, seven raw artifact ZIPs, validated outcomes/report
inventory, cache and rule snapshots, and an export manifest with SHA-256 digests.
This section contains the relevant results independently of that ignored path.

Read-only postchecks confirmed original PR #6 remains open, unmerged, with
auto-merge disabled at head `9d5588a`; original stash `9f5472b` is unchanged.
The fixture has exactly two commits and a clean working tree. The original's
index remains untouched; local OpenSpec acceptance/evidence edits remain
unstaged and uncommitted. No ready transition, controlled failure, cancellation,
rerun, release PR, review, merge, tag/release, closure, or deletion occurred.

Batch 01 authorization is consumed. The next concrete batch is prepared for
review: ready transition, same-head warm run, a documentation-only cross-commit
run, and Composer-input/fallback plus exact restoration. The fallback fixture
temporarily adds before/after SHA-256 receipts and `cmp` only in the laboratory,
so its claimed manifest/lock immutability can be checked from native artifacts.
That fixture passed Actionlint 1.7.12 and offline Zizmor 1.31.1. It has not been
published. Tasks 4.3 and 4.5 remain open; progress remains **23/26**.

## Laboratory Batch 02 — cache acceptance (2026-11-04, America/Sao_Paulo)

After specific authorization of the reviewed Batch 02, laboratory PR #1 was
marked ready. The authorized three additional commits were published only to
`GustavoPeixoto/php-qa-scope-validation-20261103:qa/acceptance`: documentation-only
cross-commit reuse, Composer-input/fallback instrumentation, and exact baseline
restoration. No original-repository Git/GitHub state was written.

All four resulting runs passed **seven QA checks**, retained ordinary release
validation as **skipped**, and ended with authenticated ready-state eligibility
(`mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`). Export checks selected the
actual current-run check IDs rather than reusing earlier green results for the
same head. All eight contexts came from Actions integration 15368.

| Case | Run | Head | Actual tested temporary merge |
| --- | --- | --- | --- |
| Same-head warm run after ready transition | [41932050685](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41932050685) | `c74b9e3` | `c4e8eccde7a0d3314eead9f2fe38b89228135316` |
| Documentation-only new commit | [41932498824](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41932498824) | `b1b11d5` | `92d13e958df8ca54f15f25d9d61fd38d46b8b335` |
| Composer fallback with hash receipts | [41932987828](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41932987828) | `f42178f` | `f0689eb5bbbde6e9fdc30b804071df9dc7591c75` |
| Exact production-input/workflow restoration | [41933692112](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41933692112) | `a6a7fff` | `778baed6eeb16288018d54336486bd31c0b1cb05` |

### Cache and native-install observations

- Warm-ready and cross-commit logs confirm restoration of the exact initial PHP,
  Node/OpenSpec, and Composer keys. A different head SHA did not invalidate these
  keys when runtime/Composer inputs were unchanged. Every applicable job still
  performed its build/install and native validation; no success outcome was
  reused from cache.
- The Composer fixture added root version 0.1.0 and changed only the lock content
  hash semantically, preserving dependency names/versions and all other lock
  fields. The primary Composer key suffix changed from
  `e02ba976432e425174a79894feb472484f6e2824f54676e2c15194cedb6ac96b`
  to `ccfe96e31fadf28e00055b60cc67aa906a16df767a5fb5a1d0a858012ed84d30`.
  Logs prove restoration from the earlier key through the unchanged PHP runtime
  prefix and subsequent publication of the new primary key.
- Only this laboratory fallback revision instrumented installation with SHA-256
  receipts before/after the unchanged Composer command and a fatal `cmp` check.
  All six PHP artifacts contain matching receipts, independently compared with
  the exact prepared fixture bytes: `composer.json` SHA-256
  `080da0048f34018a2328d9c509beb24806725330ea62d238bd60a3e847d58e8b`;
  `composer.lock` SHA-256
  `8b198e524c7d675c2b565a0e7b718ea57ca624055df3be39fd763ce0eb8cb8c1`.
  This directly establishes input immutability during each locked install.
- The restoration commit returned `composer.json`, `composer.lock`, and the QA
  workflow to exact seeded-main bytes, including removal of the instrumentation.
  Its run restored the baseline Composer primary key and passed all seven checks.
  The final diff from laboratory main contains only `LAB_VALIDATION.md`.
- All **28 artifacts** from these four runs were downloaded. Each contains its
  expected nonempty native report and passed outcome for its own tested merge
  revision, with native exit zero and valid report. Full job logs, run/job/check/
  PR metadata, cache snapshots, copied protection, eligibility, and digest
  inventories are exported for each case.

API-rounded timing examples are observations, not a controlled benchmark:

| Case | Node cache restore / build | QA Scope PHP cache restore / build | QA Scope Composer restore / install |
| --- | --- | --- | --- |
| Warm-ready | 5 s / 50 s | 1 s / 3 s | 1 s / 2 s |
| Cross-commit | 4 s / 52 s | 1 s / 3 s | 1 s / 3 s |
| Composer fallback | 4 s / 54 s | 1 s / 5 s | 1 s / 2 s |
| Baseline restored | 6 s / 57 s | 2 s / 5 s | 1 s / 3 s |

In particular, Node layer restoration was real but its build step still took
50–57 seconds versus 55 seconds in the cold observation. These runs do not
establish a Node setup latency improvement; local image loading/export and cache
transfer remain part of preparation. No performance optimization beyond the
accepted cache design is inferred or introduced by this validation.

### Required-check and isolation observations

On new documentation head `b1b11d5`, the retained authenticated snapshot records
a ready PR, unchanged base `cc6c362`, `mergeable: MERGEABLE`, and
`mergeStateStatus: BLOCKED` with required QA pending. Later authenticated API
reads also observed OpenSpec in progress while the six PHP checks succeeded and
the PR remained blocked. After completion the PR returned to CLEAN. This is
check-induced eligibility evidence without draft restrictions or merge attempts.

Each positive export reread and matched laboratory ruleset 26443022 against the
reviewed mutable payload, confirmed no bypass, and confirmed the tag workflow
remained disabled. No rule, review, merge, tag/release, cancellation, controlled
failure, release PR, or cleanup operation was included in Batch 02. The original
PR #6, source refs/index/stash, workflows, protections, and caches remain outside
the mutation scope. Local acceptance/evidence edits remain unstaged/uncommitted.

Exports are retained under
`tmp/pr-qa-disposable-validation-20261103/evidence/{warm-ready,cross-commit,composer-fallback,baseline-restored}/`,
with the pending-state snapshot at `evidence/inflight-cross-commit.json`. This
section records the relevant findings independently of those ignored paths.

Task **4.5 is complete** under the accepted laboratory criterion. Progress is
**24/26**, with tasks **4.1** and **4.3** still open. Remaining 4.3 observations
are controlled failure/recovery, missing-check/recovery, cancellation/rerun,
timeout/recovery, and a same-repository release PR. Real fork, emitted neutral,
and direct original-main blocking remain explicitly unverified as accepted.
Batch 02 authorization is consumed. The next reviewed fixture batch requires
new specific authorization; source integration and archive remain excluded.

## Laboratory Batch 03 — halted at the first fixture

The developer authorized the disclosed Batch 03. Initial guards confirmed ready
PR #1 at `a6a7fff`, unchanged base `cc6c362`, the exact copied ruleset with no
bypass, disabled tag publication, and no tags/releases. Only the first intended
fixture was committed and normally pushed: **`d673d82d7f6fbe25d2d474a934b57f4e15c72d1b`**,
`test: introduce managed-scope mismatch`, changing `<file>.</file>` to
`<file>src</file>` in laboratory `phpcs.xml`.

[Run 41938101666](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41938101666)
tested temporary merge **`6fe0bcbed8211c245268e03a973828d9c1597308`**. Actual
results were:

- QA Scope: genuine exit **1**, valid retained report, `OUT-OF-SYNC phpcs.xml`,
  failed outcome without a diagnostic execution error.
- Sniffer: genuine exit **16** and empty/invalid JSON report. Native stderr:
  `ERROR: No files were checked.` followed by
  `All specified files were excluded or did not match filtering rules.`
  The changed entry and existing relative filters left no files for PHPCS.
- The other **five** QA checks succeeded; release validation was skipped.
- Authenticated eligibility showed a ready PR, current unchanged base, no merge
  conflict or review requirement, and **BLOCKED** state under the copied rules.

This proves actual check-induced blocking but does not meet the planned isolated
QA Scope failure with six successful siblings. The approved batch explicitly
requires stopping on an unexpected failure, so no restoration commit, missing
matrix, timeout, cancellation/rerun, release branch/PR, or cleanup followed.
All seven artifacts, full job logs, outcomes/native diagnostics, protections,
eligibility, and SHA-256 inventory were exported under
`tmp/pr-qa-disposable-validation-20261103/evidence/scope-fixture-unexpected/`.
No failed run was deleted or masked.

A replacement was prepared locally, **not applied to the laboratory checkout**:
`fixtures/phpcs-noncanonical.xml` preserves all baseline native inputs and adds
only an XML comment inside the managed block. QA Scope's canonical text
comparison rejects that block, while PHPCS ignores the comment. Its diff from
the current committed fixture is reviewable in
`fixtures/phpcs-noncanonical.patch`.

Native local preflight exported baseline package bytes into an ephemeral PHP
tooling container, mounting existing development dependencies read-only. It
confirmed actual daemon exit zero for the combined probe, QA Scope native exit
**1**, and PHPCS native exit **0** across **67 files** with zero errors/warnings.
Both reports were independently accepted through the actual shared
`pr_qa.cli.validate_report` validators. QA Scope reported only the intended
out-of-sync PHPCS managed block. The owned probe container was removed; no
installed original hook, service, index, ref, or stash was modified. Receipts,
terminal state, reports, and logs remain at `evidence/scope-fixture-local-probe/`.
These local observations are not claimed as replacement remote evidence.

The amended operation scope is prepared in `batch-03-amendment.md`: one extra
laboratory commit/push with the exact replacement fixture, observe the intended
one-failure/six-success result, then resume the previously disclosed recovery,
missing-check, timeout, cancellation/rerun, and release-PR operations. This
changed fixture and added commit require fresh specific authorization; no
mutation retry or automatic rollback was performed. The lab checkout remains
clean at `d673d82`, and the source repository receives no remote writes.

Progress remains **24/26**: task 4.5 is complete; tasks 4.3 and 4.1 remain open.
No approval, merge, tag/release, PR closure, laboratory deletion, or archive
occurred. Local OpenSpec evidence remains unstaged and uncommitted.

## Laboratory Batch 03 — completed under the accepted criterion

After the developer specifically authorized `batch-03-amendment.md`, the exact
noncanonical-comment fixture was committed/pushed as `48d5ec1`. Only QA Scope
failed with genuine native exit 1 and a valid report; all six siblings passed.
The ready PR was BLOCKED. Each subsequent recovery/case was observed and
exported before the next mutation. All Git/GitHub mutations remained within the
independent laboratory; the original repository received no test state.

| Case | Run / attempt | Head | Observed result |
| --- | --- | --- | --- |
| Isolated canonical-block failure | [41939871281](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41939871281) | `48d5ec1` | QA Scope failed with valid findings; six siblings passed; ready PR BLOCKED |
| Managed-block recovery | [41940412078](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41940412078) | `4a62744` | Seven QA passed; ready PR CLEAN |
| Missing required test check | [41940723119](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41940723119) | `d3c20fe` | Six emitted QA passed and workflow succeeded; current-head `QA (test)` absent; ready PR BLOCKED |
| Complete-matrix recovery | [41941002527](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41941002527) | `28f3376` | All seven QA identities returned and passed; ready PR CLEAN |
| One-minute test-job budget | [41941335575](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41941335575) | `96efce4` | Runner explicitly exceeded 1m0s; test check cancelled automatically; six siblings passed; ready PR BLOCKED |
| Production-workflow recovery | [41942044250](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41942044250) | `c09ff0c` | Seven QA passed with exact production workflow restored; ready PR CLEAN |
| Explicit workflow cancellation | [41942480753](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41942480753), attempt 1 | `ed95ca2` | One cancellation request matched the uniquely authorized active run; all seven job checks cancelled; ready PR BLOCKED |
| Same-revision reexecution | Same run, attempt 2 | `ed95ca2` | One rerun request; fresh attempt/check IDs and seven native successes; ready PR CLEAN |
| Canonical release PR #2 | QA [41943359408](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41943359408), release [41943359585](https://github.com/GustavoPeixoto/php-qa-scope-validation-20261103/actions/runs/41943359585) | `76d15b9` | Seven QA plus actual release validation succeeded; ready PR CLEAN; no tag/release created |

The actual tested merge revisions were retained with each exported outcome:
`672a68655f234b738290ce3dd882e813cef2a05a` (isolated finding),
`3a37660986a3bfa8e16edd98c8b63d2b5d68f6a8` (scope recovery),
`17fb00040de3eb94d8f77ff199b5cb7743878483` (missing check),
`91a7099e053cffef06500dd0d6eb8ef122017cc9` (matrix recovery),
`3963a4c90cf2dbba1c58c98663f23000f7b91ce7` (timeout cause),
`3bf10c829ac743f16f1577b6f265be4dae70aa7f` (timeout recovery),
`74940d0dcfaa359911f2874c171f5e837cc50567` (both cancellation attempts), and
`1ea16319ae0f727e273b29d32ca676ceecb5f4e7` (release QA).
Release validation checked its intended direct head
`76d15b9c880b57d07912f4fa1538666449c5ced5`, not a substituted merge/head revision.

### Timeout representation and cancellation evidence

The one-minute fixture produced the runner annotation
`The job has exceeded the maximum execution time of 1m0s`. Its deliberate wait
was cancelled and native PHPUnit validation never started; no successful native
test outcome was manufactured. GitHub reported both job/check and workflow
conclusions as **`cancelled`**, rather than emitting a literal `timed_out`.
The collector's initial assumption about that enum was corrected only after
checking the actual runner annotation and [GitHub's documented automatic
cancellation for job budgets](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes).
The timeout scenario and its blocking effect were observed; a literal emitted
`timed_out` conclusion is not claimed as tested.

The separate explicit cancellation targeted only the first QA run generated by
the authorized documentation fixture, after all seven QA jobs were in progress.
Its retained native outcomes were actually passed/zero/valid, while GitHub's job
checks were cancelled and the PR was BLOCKED. Thus successful diagnostic
outcome files alone did not satisfy required-check policy. This case verifies
workflow/job cancellation gating; it is not relabeled as proof that a native
tool was interrupted mid-execution. Previous local adapter interruption evidence
remains separately dated. The user subsequently confirmed on 2026-11-05 that the
observed blocked PR satisfies cancellation acceptance; no additional remote
mid-tool interruption probe is required.

### Artifact availability finding

All seven first-attempt cancellation artifact ZIPs and logs were exported before
the single rerun request. The second attempt passed and produced fresh artifacts
with current-attempt creation timestamps. Subsequent authenticated GETs for
**all seven original artifact IDs returned HTTP 404**. No agent artifact DELETE,
overwrite option, protection relaxation, or result-forcing operation was used.
Both attempts' raw evidence remains available locally and passed digest checks.

At the initial review, this finding left preservation across attempts unresolved
under the then-current retention requirement. The 2026-11-05 decision recorded
below supersedes that pending review by explicitly accepting current-attempt
retention without a guarantee across reruns. It does not establish why the
original artifact IDs became unavailable or attribute their loss to a specific
workflow or platform mechanism.

### Release, audit, isolation, and completion

Only the two prepared Composer files were committed on laboratory
`release/v0.1.0`; dependency versions and all non-content-hash lock fields stayed
unchanged. Release validation confirmed same-repository origin, strict coherent
manifest/lock, version **0.1.0**, empty stable-tag baseline, and eligible target
tag **v0.1.0** without creating it. Both laboratory PRs remain open/unmerged,
auto-merge disabled. `create-release-tag.yml` remains disabled. Tags/releases
remain empty.

An authenticated final comparison found original ruleset **25322253** and copied
laboratory ruleset **26443022** identical across reviewed mutable fields: all
eight contexts under integration 15368, strict up-to-date enforcement, zero
approvals, empty bypass, and retained PR/deletion/force-push parameters. Base
`cc6c362` stayed fixed and ready-state observations had no merge conflicts or
review blocker. No merge attempt was used as a probe.

The final audit verified **343 exported files** against SHA-256 manifests across
**15 complete case exports**, including the initial unexpected fixture result,
all cache cases, all controlled cases/recoveries, both cancellation attempts,
and the release PR. Export provenance is retained under
`tmp/pr-qa-disposable-validation-20261103/evidence/`, independently of the
disposable checkout. Its `final-audit.json`, case summaries, raw job logs,
artifact ZIPs, policies, eligibility snapshots, and digest inventories preserve
the supporting evidence. This section contains the essential results even if
the laboratory's remote links are later removed.

Task **4.3 is complete under the explicitly accepted laboratory criterion**;
task 4.5 is also complete. Real-fork execution, emitted neutral, and direct
failed-check enforcement against original main remain explicitly unverified.
Progress is **25/26**, with only original integration task **4.1** open.
No original-repository Git/GitHub mutation, review approval, merge, tag/release,
source staging/commit/push, or archive was performed. Source evidence/acceptance
edits remain local, unstaged and uncommitted; the original stash is unchanged.

Batch 03 and its amendment are consumed. Cleanup has not been executed. Its
separate review must cover closure of exactly laboratory PRs #1/#2, deletion of
repository ID **1444157567**, and removal of only the disposable checkout while
retaining the exported evidence. The CLI token currently lacks `delete_repo`;
any scope expansion/browser grant and deletion require fresh specific consent.

## 2026-11-05: Accepted current-attempt retention policy

The user explicitly accepted retaining available reports from the current workflow
attempt without guaranteeing access to earlier-attempt artifacts after a rerun.
This revises the artifact requirement and resolves the prior operational retention
review; it is not a production workflow fix or proof of the underlying cause.
Required uploads after success or failure, valid current-attempt evidence for a
successful check, and job failure on a failed required upload remain mandatory.
No artifact-naming, action, workflow, cache, protection, dependency, or public API
change is needed for this decision. No additional remote retention probe is
required for acceptance.

The exported records distinguish the first attempt of the cancellation case from
the earlier laboratory runs:

| Observation | Recorded value (UTC) |
| --- | --- |
| Cancellation run / attempt | `41942480753` / 1 |
| First attempt started | 2026-11-05 00:35:39 |
| Seven original artifacts created | 2026-11-05 00:36:01–00:36:53 |
| All seven original expiration timestamps | 2027-02-03 00:35:39 |
| Original expiration flags at export | All seven `expired: false` |
| Same-run attempt 2 started | 2026-11-05 00:38:32 |
| Recovery evidence | Seven fresh artifacts available; all seven QA checks passed |
| Subsequent original-ID lookup | All seven returned HTTP 404 |

These timestamps do not support expiration at the recorded retention deadline as
the explanation. The exact cause of unavailability remains unproven. Reports of
similar rerun behavior exist in the action's [issue 585](https://github.com/actions/upload-artifact/issues/585),
including reports involving attempt-specific names; these reports support an
investigation hypothesis, not attribution of the laboratory result.

Source records remain under `tmp/pr-qa-disposable-validation-20261103/evidence/`:
`cancelled/run.json`, `cancelled/artifacts.json`, `cancel-recovered/run.json`,
`cancel-recovered/artifacts.json`, and
`cancel-original-artifact-availability.json`. Both attempts' exported ZIPs,
logs, manifests, and hashes are preserved. Local exports safeguard this
experiment and are not a new production archival requirement.

Cancellation acceptance is also settled: all seven cancelled required checks
blocked the ready laboratory PR. That satisfies the agreed merge-gating objective
without requiring proof that a native tool was interrupted mid-execution. Real
fork execution, emitted `neutral`, and direct failed-check enforcement on original
main remain explicitly accepted coverage limits.

Tasks 4.3 and 4.5 remain complete. Progress remains **25/26**, with integration
task **4.1** open; PR #6 is not approved or merged, and the change is not archived.
Before this revision, the five change artifacts already had staged modifications.
This revision edits only their worktree contents; it does not update the index,
change the stash, publish documentation, or clean up the laboratory. Those
Git/GitHub operations still require their own specific authorization.

Local validation for this documentation revision:

- `openspec validate --all --strict --no-interactive`: **6 passed, 0 failed**.
- `git diff --check HEAD`: passed.
- Task checklist: **25/26**, with only task **4.1** open.
- Before/after comparisons confirmed identical HEAD, stash, index entries, and
  staged diff, plus unchanged contents of the other 213 tracked files and all
  398 files under the exported evidence directory.
- No new remote execution, publication, approval, merge, or cleanup was performed.

## 2026-11-05: Same-PR closure criterion and laboratory deletion

The user explicitly accepted closing the implementation checklist and archiving
within PR #6 before integration. This supersedes earlier statements that task
4.1 must remain open until merge. Its revised criterion is publication of the
implemented seven-check workflow and observation of the published implementation,
not a merge that has not happened. The update/apply/sync/archive sequence does
not authorize staging, commit, push, PR editing, review approval, merge, or local
laboratory cleanup.

Authenticated readback confirmed latest implementation run
[41372936727](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/41372936727),
at source revision `9d5588a40f27fd0f60eab3dd527930a797c6e755`, completed successfully.
Its seven independent QA checks passed and the ordinary-PR release check was
skipped; no aggregate is required. These are implementation publication results,
not evidence for the as-yet-unpublished final documentation/archival revision.
The final commit must receive fresh checks after separately authorized push.
PR #6 remains open on `change/release-validation-tooling -> main`, unmerged and
without approval submitted by this agent.

The user deleted `GustavoPeixoto/php-qa-scope-validation-20261103` manually through
the browser. A subsequent read of the exact repository returned authenticated
HTTP 404 under account `GustavoPeixoto`; this was confirmed again during closure
preparation. The agent issued no repository deletion or PR closure request and
did not expand CLI permissions. Thus earlier proposals to close laboratory PRs
and grant `delete_repo` are no longer pending actions. The exported evidence
contains 398 files, including both cancellation attempts' ZIPs and manifests.
It remains separate from the intact, clean disposable checkout at
`/tmp/php-qa-scope-validation-20261103/checkout`; neither is removed here.

All accepted laboratory scope limits and the current-attempt retention policy
remain as documented above. No functional code, workflow, cache, protection,
dependency, version, or public API change accompanies this closure decision.

### Completed local closure

The revised task 4.1 was verified against the authenticated implementation run
above and marked complete through the apply workflow: **26/26 tasks complete**.
All ten requirements and 31 scenarios were synced to the new main specification,
`openspec/specs/repository-pr-qa/spec.md`. Purpose and the complete requirement/
scenario body were compared verbatim with the delta and matched. Main-spec
format contains `## Requirements` without delta operation headers.

After successful sync, all six change files were moved without content changes
to `openspec/changes/archive/2026-11-05-add-required-pr-qa/`. This closure record
was then appended to the archived verification document. The change is no
longer active; PR #6 remains unmerged. Archive records completed implementation,
not integration, and does not substitute old check results for the final commit.

Local validation:

- Selected-change strict validation passed before archival.
- Strict main-spec validation passed after sync: **6/6**.
- `openspec validate --all --strict --no-interactive --json` passed after
  archival: **6 passed, 0 failed**; `openspec list --json` reported no active
  changes. Informational long-description hints do not indicate failed checks.
- `git diff --check HEAD` and whitespace checks covering the new and moved
  files passed; the archived checklist contains **26/26** completed tasks.
- Before/after comparisons confirmed unchanged HEAD, stash, index entries,
  staged diff, all other 212 tracked files, and all 398 exported evidence files.
- The laboratory checkout was preserved. No staging, commit, push, PR edit,
  review approval, merge, or cleanup was performed during local closure.

Next gate: specifically authorized staging/commit of the reviewed documentation,
followed by separately authorized push and PR-body update. Fresh checks for that
new revision must be observed before presenting any separately authorized merge.
