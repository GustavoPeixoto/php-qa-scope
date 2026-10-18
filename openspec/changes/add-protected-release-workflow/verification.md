# Protected release workflow verification

## Status

Local release helpers and workflows are implemented and integrated. Infrastructure
activation gates are verified for the initial policy: PRs and automatic checks
with zero required human approvals. Main's exact required check and up-to-date
policy are active; maintainer-observed App installation/permissions match the
authenticated tag bypass, and isolated negative enforcement probes passed.
Independent reviewer/CODEOWNER availability is not a prerequisite.
Tasks **23/23** are complete under the infrastructure-only scope. Actual App token
issuance and publication have not been exercised. The maintainer deleted the
authorized disposable fixture after evidence capture; cleanup is complete.
Real publication is outside this change and requires separate future authorization.
The manifest still has no `version`; a later authorized real release PR supplies it.

## Current execution scope

The maintainer explicitly requested infrastructure preparation and activation
without publishing any version. The subsequent approved scope revision removes
real publication from this change's task list and completion criteria. No
production release branch, version edit, tag, or GitHub Release is authorized
here. Actual App token issuance and full live publication remain unexercised
limitations, to be verified only in a separately authorized future release.
They are not unfinished implementation work in this change.

The dated sections below retain historical inspection and rollout evidence,
including blockers that were later resolved. They describe the state at each
snapshot; this status section and the completed infrastructure gates below
describe the final state.

The continuation installed the distribution's GitHub CLI 2.23.0 in the running
dev environment (no image definition or package files changed). Browser device
authentication completed as `GustavoPeixoto`, with Git credential-helper
reconfiguration declined to preserve the existing Git setup. The authorized
infrastructure branch/PR and main-check update are recorded below; no release ref
or version was created. Authenticated findings and the
App/control blockers observed at each stage are recorded below. The maintainer
subsequently created `Protect main`; its current authenticated readback is
recorded separately from the earlier snapshots.

## Initial local evidence — 2026-10-17

These results predate the zero-approval policy revision. Tasks 5.1–5.3 were
reopened for fresh acceptance; retain the earlier results as historical evidence.

All commands run from the repository's dev environment. Composer fixtures run in
the existing PHP service, which reports Composer **2.10.3**, PHP **8.5.10**.

| Check | Result |
| --- | --- |
| `PYTHONPATH=tools python3 -B -m unittest discover -s tools/release -p 'test_*.py'` | 13 test methods passed, including the shared version matrix and native Composer fixtures. |
| `actionlint` 1.7.12, both workflows | Exit 0; syntax, expressions, and embedded shell checked. |
| `zizmor` 1.31.1 `--offline --pedantic .github/workflows` | Exit 0; no reported findings (one built-in suppression). No repository suppression configuration was added. |
| Temporary-index `git archive` of the implementation tree | 105 entries; `.github/`, `tools/`, `conventions/`, and `openspec/` absent; `composer.json`, README, executable, and source retained. |
| `git diff --check` | Passed. Contributor index remains unstaged. |
| `composer --no-plugins --no-scripts validate --strict --no-check-version` in PHP | Root `composer.json` is valid. |
| `openspec validate add-protected-release-workflow --strict` | Change is valid; exit 0. |

The archive uses a separate `GIT_INDEX_FILE`, starts from HEAD, and overlays the
implementation paths, including untracked workflows/helpers. It therefore tests
the new files' exclusion rather than merely archiving the old HEAD. The contributor
index is not changed. Existing export-ignore rules remain intact.

### Scenario coverage

`tools/release/fixtures.json` is shared between `test_validate.py` and the actual
inline authority code extracted from `create-release-tag.yml`. The publisher never
imports that fixture or helper at runtime.

| Release-tagging contract/scenarios | Evidence |
| --- | --- |
| Branch/manifest agreement; missing, non-string, mismatched, prefixed, whitespace, Unicode, suffix, leading-zero and incomplete names; fork rejection | Shared fixtures; `test_shared_contract`, `test_same_fixtures_execute_actual_inline_logic`, early origin-step execution. |
| Numeric maximum over all pages; both stable prefixes; ignored nonstable tags; API failures and incomplete/repeated/malformed pagination | `test_pages_numeric_maximum_and_errors`, `test_all_tag_pages_and_incomplete_pagination`, malformed API tests. |
| Initial `0.1.0`; allowed successors of `1.0.0` and `0.2.7`; repetition, regression, skipped components, stale release | Shared fixture matrix; all three successor forms and explicit rejection cases. |
| Strict Composer validation with explicit version; other problems fail | Real Composer fixtures: valid version accepted; without the narrow suppression it fails; malformed JSON, invalid package name, absent description/license, unknown schema key, and stale lock fail. |
| No dependency installation, script execution or plugin activation | Exact flags in both workflows; fixtures retain no vendor directory or script marker. Fixture lock seeding/repair uses disabled repositories, no dependencies, no scripts/plugins and no installation. |
| Lock recovery without dependency changes | Real `update --lock --no-install` fixture followed by strict validation; package lists unchanged. |
| All PR events, ordinary/fork PRs, malformed release prefixes, updates | Actual workflow event/job invariants; ordinary path has no checkout/Composer requirement; exact PR head SHA; no path or release-only job filter; origin fixture execution. |
| Eligible integrated merge; ordinary/open/unmerged/wrong-base/fork PRs; squash/rebase SHA | Actual job condition evaluation and fresh API checks; integrated SHA differs from source and moving main in fixtures. |
| Fresh PR/manifest/tags before credentials; malformed responses fail | Executed inline code with mocked `gh` API results; no outputs or writes on failure; immutable contents endpoint includes the integrated SHA. |
| Different-version concurrency and stale publication | Repository-wide, noncanceling publisher concurrency inspected; fixture scheduler runs actual authority checks in serialized critical sections and rejects the second stale version. This simulates Actions semantics; no live concurrency claim is made. |
| Existing ref on same/different SHA, retries and create failures | Existing-ref fixtures fail before credentials; actual create shell executes against a fixture `gh`, checking exact POST/ref/SHA and nonzero propagation. Existing refs are retained and no fallback is attempted. |
| Read-only validation and isolated App credentials | Workflow invariants and native fixture client; no checkout/helper import in publisher; late scoped token action; only create receives installation token; normal reads use read-only fixture token; no token in captured console output. |
| Integrated event-to-create-ref path | `test_integrated_event_authority_token_and_native_create`: actual inline authority and native create shell, external App action substituted with a fixture token; eligible events publish exact ref/SHA, ineligible events skip, failed/stale authority cannot mint credentials, API failures preserve refs. |
| Governance and tag enforcement | Local contract implemented/documented; actual remote enforcement remains unverified and blocks activation. |
| Manifest-only preparation and safe failure/cancellation recovery | `conventions/releases.md` includes initial diff, successors, fresh-state retry conditions, pending replacement, corrective releases, rollback, and separate Git tag/Packagist/GitHub Release behavior. |

Action SHAs were resolved and version tags cross-checked against the upstream
GitHub APIs on 2026-10-17:

| Action | Version | Immutable SHA |
| --- | --- | --- |
| `actions/checkout` | v4.4.0 | `11d5960a326750d5838078e36cf38b85af677262` |
| `shivammathur/setup-php` | 2.40.0 | `eb7c497e18156a6bbabfef1d3a82760b9eda3962` |
| `actions/create-github-app-token` | v3.3.0 | `64ab729a6294000f5aa4a4bc0b73d1f32bc45510` |

The pinned App action's input definitions were checked for `client-id`,
`private-key`, `owner`, `repositories`, and `permission-contents`, and its post
cleanup is present. The two-workflow inventory contains exactly one publisher;
the authorized incompatible local `release.yml` draft was removed.

## Remote read-only evidence — 2026-10-17

Target: `GustavoPeixoto/php-qa-scope`, public repository; default branch `main`.
Anonymous GitHub API inspection returned:

- `/repos/GustavoPeixoto/php-qa-scope/tags?per_page=100`: empty tag list.
- `/repos/GustavoPeixoto/php-qa-scope/actions/workflows`: empty workflow list;
  these local workflow files have not been deployed by this implementation.
- `/repos/GustavoPeixoto/php-qa-scope/rulesets/25208186`: active tag ruleset
  `Protect releases`, include `~ALL`, no exclusions, rules `creation`, `update`,
  `deletion`, and `non_fast_forward`. Bypass actors are not disclosed anonymously.

Sources: [repository API](https://api.github.com/repos/GustavoPeixoto/php-qa-scope),
[tag ruleset](https://github.com/GustavoPeixoto/php-qa-scope/rules/25208186).
These are observations, not proof of authenticated enforcement.

At the initial inspection, no `GH_TOKEN`/`GITHUB_TOKEN` was present in the dev environment. The configured
Git credential helper could not return credentials (`git credential fill` exited
128 with prompting disabled). Authenticated inspection is consequently unavailable;
a `/user` request without usable credentials returns 401. The GitHub plugin was
discovered as available but not installed/connected, and a connection suggestion
was presented. No credential values were logged.

## Initial authenticated continuation — 2026-10-17

The maintainer completed GitHub CLI browser authentication as `GustavoPeixoto`.
Repository metadata confirms admin access. Only sanitized configuration is
recorded; variable values and credentials were not printed.

| Inspection | Authenticated result |
| --- | --- |
| Repository topology | `main` remains default; merge commits, squash and rebase are enabled; auto-merge is disabled. |
| Main protection | Classic protection endpoint returns 404; effective branch rules are empty. No main protection, required CI checks, or merge-queue rule is configured at this snapshot. |
| Tag ruleset 25208186 | `Protect releases` remains active, covers `~ALL` with no exclusions, and retains creation/update/deletion/non-fast-forward restrictions. |
| Tag bypass | Exactly one `Integration` actor, ID `5338805`, with `always` bypass. The authenticated ordinary user reports `current_user_can_bypass: never`. No branch ruleset or main bypass was added. |
| Actions configuration | `RELEASE_APP_CLIENT_ID` variable and `RELEASE_APP_PRIVATE_KEY` secret exist; presence only is recorded. |
| Workflow inventory/history | No registered workflows and no remote tags. Infrastructure rollout and an ordinary PR check emission remain pending. |
| Eligible reviewers | The full collaborator response contains only `GustavoPeixoto`, role `admin`, with push access. No independent collaborator with write access is currently available to approve that maintainer's PR or serve as the required independent CODEOWNER. |

App installation verification remains incomplete despite successful repository
administration authentication. `/repos/GustavoPeixoto/php-qa-scope/installation`
requires an App JWT (401); `/user/installations` explicitly requires a token
authorized to a GitHub App (403). The CLI OAuth token cannot substitute for these
App-specific credentials. GraphQL exposes the bypass mode but returns no App actor
identity. Therefore the App's actual installation, selected repository access,
contents-write permission and correspondence to actor `5338805` are not proven.

The public App at slug `release-bot` is ID `9671`; its client ID does **not** match
the configured variable. It must not be used to identify the provisioned App
or to claim misconfiguration: the planned `release-bot` name alone does not
establish that public slug as the installation's identity. Confirmation must use
the actual provisioned App and installation, without exposing its private key or
creating a replacement.

At that historical stage, activation stopped at the independent-review requirement. The maintainer was
asked whether to identify another reviewer with write access or discuss an
explicit policy revision for individual maintenance. No invitations, placeholder
CODEOWNERS, weaker approval settings, ruleset edits, commits, pushes or publication
were performed. No real release was authorized at that historical stage.

## Initial zero-approval policy — bootstrap readback

The maintainer explicitly removed mandatory approval by another person for this
initial phase and created `Protect main`. The revised planning artifacts adopt
that decision; `conventions/releases.md` now describes the same PR/check policy.

Fresh authenticated API reads confirmed:

| Control | Current observed state |
| --- | --- |
| `Protect main` | ID `25322253`, active, branch target only `refs/heads/main`, no exclusions and an empty bypass list. |
| PR gate | Required approvals `0`; mandatory CODEOWNER approval, latest-push approval and stale-approval dismissal are disabled. No independent reviewer is required. |
| Additional Copilot approval setting | Enabled, but its additional-approval condition requires a nonzero approval count; it does not create a human-approval prerequisite with the configured count of zero. |
| Main mutation restrictions | `deletion` and `non_fast_forward` are present; no blanket restrict-updates rule was introduced. |
| Merge topology | Merge, squash and rebase are enabled. The effective main rules contain no merge-queue rule; auto-merge is disabled. |
| Existing required CI | No required-status-check rule; the classic protection endpoint returns 404. Registered workflow count is still `0`. The planned required check is exactly `Validate Release Branch`. |
| Activation state | PR-only bootstrap. Integrate the infrastructure by ordinary PR, observe the check, then require it with an up-to-date branch. No full check-enforcement claim is made yet. |
| Tag protection | `Protect releases` ID `25208186` remains active over `~ALL`, with creation/update/deletion/non-fast-forward restrictions and sole Integration bypass actor `5338805`; ordinary user bypass is `never`. |

The earlier lack of another collaborator is not a blocker under this policy.
The App identity/installation/repository-access/contents-write limitation remains;
the maintainer was asked for the actual provisioned App link or slug. Current
configuration readback is distinct from mutating enforcement probes and actual
publication acceptance. No version was published during these checks.

## Fresh local checks for the revised policy

- Release helper/publisher/Composer fixture suite: all 13 test methods passed.
- `actionlint` 1.7.12: both workflow files passed (exit 0).
- `zizmor` 1.31.1 with `--offline --pedantic`: exit 0, no reported findings
  (one default suppression, no repository suppression configuration).
- OpenSpec strict validation and whitespace checks passed after the documentation
  update. The local PHP manifest and package/hook code remain unchanged.
- The bootstrap readback confirmed a zero-approval PR path without required checks;
  the later rollout below adds and verifies the check. Mutating direct-push,
  failed-check-merge and protected-tag probes are still task 4.5, not inferred
  from this readback or from the local publisher fixture client.

At that snapshot, the fixture suite alone did not prove live GitHub enforcement
or App installation, so task 5.1 remained pending. The subsequent settings
confirmation and coordinated group-4 evidence below complete that acceptance.

## Initial rollout pre-flight

GitHub Actions is enabled with all actions allowed. Local and remote `main` both
resolve to `9cec62231ce0bb53c5e7b0d02fbfed431734880a`. The actual dev environment
has the required `QA_HOOKS_SERVICE=dev` marker, both dev/php services are running,
and Lefthook reports the pinned version `2.1.16`.

The installed `.git/hooks/pre-push` is an older generic Lefthook launcher: it
invokes `call_lefthook run "pre-push" "$@"` but lacks the project ownership marker
and `QA_HOOKS_GIT_PUSH`/remote-context forwarding. The repository's
`docker/dev/bin/setup-git-hooks` explicitly rejects that unmanaged-hook conflict.
The Git hook convention requires explicit reinstallation and prohibits automatic
replacement during verification. A preserved backup of this exact old launcher
and installation of the current managed launcher need maintainer authorization
before push. No push or hook bypass was attempted during this pre-flight.

This local rollout prerequisite is independent of the App installation evidence
and does not authorize any release. The infrastructure remains eligible for an
ordinary PR once the local hook conflict is resolved.

## Verified infrastructure rollout — 2026-10-17 UTC

The maintainer explicitly authorized preserving and replacing only the old
pre-push launcher. Its exact backup remains at
`tmp/release-hook-backup/pre-push.f38e78508b124304f236f2eee344ce2ed679fba06dde9a84a3908d1ab0d7c095`.
The current repository's `docker/dev/bin/setup-git-hooks` installed the managed
launcher with the ownership marker and Git invocation/remote-context forwarding.
No hook bypass was used and no unrelated hooks were replaced.

The ordinary infrastructure branch `change/protected-release-workflow` was pushed
at commit `dcde19361387fcac1667cb7061420be0b099ff78`. The actual Git pre-push run
`20261017-231303-297` passed all seven checks: QA Scope, Sniffer, Fixer, MD, Stan,
Test and OpenSpec. Its schema-4 summary reports `passed`, exit 0; native reports
remain in `logs/prepush/20261017-231303-297/`. These paths are retained provenance;
the successful outcomes are reproduced here rather than inferred from a log link.

| Rollout evidence | Observed result |
| --- | --- |
| [Infrastructure PR #1](https://github.com/GustavoPeixoto/php-qa-scope/pull/1) | Ordinary same-repository PR into `main`, no release naming or manifest version edit. |
| [Required check run](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/39078233253/job/117529720149) | `Validate Release Branch`, completed successfully on head `dcde19361387fcac1667cb7061420be0b099ff78`; emitted by `github-actions`, integration ID `15368`. |
| Main-check activation | Only after that success, `Protect main` was updated to require the exact check from integration `15368`, with `strict_required_status_checks_policy: true` and `do_not_enforce_on_create: false`. Existing PR/deletion/force-push rules, zero approvals and empty bypass list were preserved. |
| Main integration | PR #1 merged at `2026-10-17T23:15:30Z`, producing integrated commit `97e75b5a7a40ed15dbe04d1bf577a08aec5357a2`; the PR had zero reviews. The merge request matched the expected head SHA and used no bypass. |
| Main rules evaluation | GitHub rule suite `4580733094` for that exact before/after main update reports `pass`; required-status-check, PR, non-fast-forward and deletion evaluations all passed under active `Protect main`. This proves the successful zero-approval path, not the separate negative probes. |
| [Closed-PR publisher run](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/39078320153) | `Validate Merged Release` and `Publish protected release tag` were both skipped for the ordinary infrastructure PR. |
| Release state | The post-merge tag API response is still empty; the package manifest still has no `version`. No release was published. |

Fresh effective-rule reads confirm the required check and up-to-date policy on
`main`, the original zero-approval settings, and no main bypass. `Protect releases`
continues covering `~ALL` with the original restrictions and sole Integration
bypass `5338805`. App-specific installation/permission proof and isolated negative
enforcement probes remained outstanding at that snapshot; real publication had
not been authorized.

## Documentation rollout and App identification — 2026-10-17 UTC

The maintainer identified the provisioned App settings page as
`https://github.com/settings/apps/gustavopeixoto-releasebot`. This establishes
the intended slug, `gustavopeixoto-releasebot`, but does not yet prove its App ID,
installation, selected repository or granted contents-write permission.
An authenticated `GET /apps/gustavopeixoto-releasebot` returns 404 with the CLI
OAuth session. A private App may not be visible through that endpoint; this is
not evidence that the App is absent or misconfigured. Maintainer confirmation
from the authenticated App settings and installation configuration is pending.
No credentials were requested or disclosed, and no replacement App was created.

The maintainer subsequently inspected the authenticated App/installation settings
and confirmed App ID **5338805**, access to **all repositories** on the account
(including `php-qa-scope`), and **Read and write access to code**. The App ID
matches the sole Integration bypass actor in `Protect releases`. This is
maintainer-observed installation/permission evidence, rather than a successful
App-authenticated API request or an exercised installation token. Fresh CLI API
readback independently confirms the variable/secret names remain present and the
active all-tag rules retain the same sole bypass actor. Task 4.2 is complete on
that combined evidence; credential validity and real publication remain
unexercised, for verification during a future separately authorized release.
The existing all-repository grant was preserved; the workflow requests a token
scoped to this repository and contents-write only.

The activation evidence and convention updates were committed as
`297306561d9bee72ff8e5582f5a2b8212d225dab` and integrated through ordinary
[PR #2](https://github.com/GustavoPeixoto/php-qa-scope/pull/2).
Its actual pre-push execution `20261017-231939-504` passed all seven checks,
with schema-4 overall status `passed` and exit 0.
The exact-head [Validate Release Branch check](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/39078625127/job/117530860350)
completed successfully under GitHub Actions integration `15368`.
The SHA-matched, ordinary merge completed at `2026-10-17T23:30:44Z`, with
zero reviews, producing `31ece9db9da6d6c18cfcd7edcef0709030c4d688`.
The [closed-PR publication workflow](https://github.com/GustavoPeixoto/php-qa-scope/actions/runs/39079311446)
was skipped. Fresh authenticated readback confirms unchanged main/tag controls,
an empty tag list and no manifest `version`.

The proposed isolated enforcement fixture is a new public repository,
`GustavoPeixoto/php-qa-scope-rules-fixture-20261017`, containing only a README
and a minimal read-only check workflow. It would test non-version fixture tags,
direct main updates, failing-check merges and a successful zero-review merge
under matching relevant protections. No fixture has been created; maintainer
coordination is pending. The CLI lacks `delete_repo`, so the proposed cleanup
requires the maintainer to delete the fixture through GitHub after evidence is
recorded. These proposed probes are not completed acceptance evidence.

## Isolated authenticated enforcement probes — 2026-10-17 UTC

The maintainer authorized creating the public disposable repository
`GustavoPeixoto/php-qa-scope-rules-fixture-20261017` and agreed to delete it
manually after evidence capture. The repository contained only a README and the
minimal `Isolated rules fixture` workflow. It had no package, secrets, release
publisher, semantic-version tags or GitHub Releases. The existing App's
all-repository access may include this new fixture; no installation settings
were changed and no App credentials or tokens were used in the fixture.

Fixture main ruleset **25323724** was active only on `refs/heads/main`, with no
bypass, zero required approvals, PRs, deletion/force-push restrictions and strict
up-to-date `Validate Release Branch` from GitHub Actions integration `15368`.
Fixture tag ruleset **25323726** was active over `~ALL`, with no bypass and
creation/update/deletion/non-fast-forward restrictions. This reproduces the
relevant ordinary-user restrictions; it does not exercise the production App's
separate bypass or token generation. No production rules were disabled.

All probes used the ordinary authenticated `GustavoPeixoto` CLI account. A
non-version tag `fixture-existing` was seeded before enabling the fixture rules,
at initial main **79cc81c17d37905c07d64d4bf878f5a98499167c**.

| Probe | Actual result and retained evidence |
| --- | --- |
| Create `fixture-new` | HTTP 422. The generic `Reference update failed` response alone was insufficient; authenticated rule suite **4580883299** independently reports active `creation` failure: `Cannot create ref due to creations being restricted.` The ref remained absent. |
| Move `fixture-existing` to another commit | HTTP 422, `Cannot update this protected ref.` Rule suite **4580887612** reports active `update` failure. The original SHA remained unchanged. |
| Delete `fixture-existing` | HTTP 422, `Cannot delete this tag`. Rule suite **4580887826** reports active `deletion` failure. The ref remained present at its original SHA. |
| Direct main ref update without a PR | HTTP 422; suite **4580893372** reports active `pull_request` and `required_status_checks` failures. Main remained unchanged. |
| Actual Git push to main without a PR | Commit **2b3c25fd452519e2be3c2abc61fe447add78c03c** was rejected remotely with `GH013`, including `Changes must be made through a pull request` and the missing required check. Rule suite **4580893720** confirms both active failures. No hook bypass or force push was used; main remained unchanged. |
| Direct update/push of the failing-check PR commit | API and Git both rejected it for the failing `Validate Release Branch`; suite **4580888500** confirms the required-status-check failure. Its PR association passed the PR rule, so the separate commit without a PR above establishes that gate. |
| Merge failing-check fixture PR #1 | The real Actions check failed on **f12789f1e88a04623609a4d3bec8f6acd9b1b2d2**; a SHA-matched merge attempt returned HTTP 405 with `Required status check "Validate Release Branch" is failing.` Suite **4580895683** reports that failure for the attempted merge commit. Main remained unchanged. |
| Merge passing-check fixture PR #2 | The real Actions check passed on **7eb46cfca0307951207412075afb08aacdc4b1a4**. With zero reviews, an ordinary SHA-matched merge succeeded as **3bdd5817af12779d2a76199f86b305465b009c2b**; all four active evaluations passed in suite **4580895951**. Main became that integrated SHA; the seeded tag retained its original SHA. |

The failing check was [run 39079847932, job 117534387903](https://github.com/GustavoPeixoto/php-qa-scope-rules-fixture-20261017/actions/runs/39079847932/job/117534387903);
the successful check was [run 39079850266, job 117534395111](https://github.com/GustavoPeixoto/php-qa-scope-rules-fixture-20261017/actions/runs/39079850266/job/117534395111).
Both checks report the exact expected head SHA and App integration `15368`.
The passing PR was observed as `clean`, the failing PR as `blocked`.
Final readback retained both active rulesets and empty bypass lists. The only
fixture tag was still `fixture-existing`; no production refs were mutated by
these tests. Probes completed at `2026-10-17T23:41:26Z`.

Raw sanitized receipts remain in ignored `tmp/release-rules-probe-evidence.json`;
the outcomes and identities above are durable evidence independent of that file
or the disposable repository's later deletion. The maintainer subsequently
confirmed manually deleting `GustavoPeixoto/php-qa-scope-rules-fixture-20261017`.
Authenticated repository readback now returns HTTP 404 (`Not Found`), consistent
with that confirmation; the same CLI session retains admin access to the
production repository. The maintainer's confirmation establishes deletion,
rather than inferring it from HTTP 404 alone. Cleanup is complete without granting
the CLI `delete_repo` scope. Fixture links above are historical provenance; their
recorded outcomes remain available in this artifact. Task 4.5 is complete.

## Final infrastructure acceptance checks

After the settings confirmation, all 13 release helper/publisher/native Composer
test methods passed again. The suite includes the integrated event-to-create-ref
simulation and actual inline publisher logic; the external App action still uses
a fixture token. Both workflows passed actionlint **1.7.12**. Zizmor **1.31.1**
with `--offline --pedantic` reported no findings (one default suppression).
Group-4 evidence separately covers initial PR-only bootstrap, activation of the
real required check, ordinary production zero-review merges and isolated
negative/successful enforcement probes. Task 5.1 is complete on that combined
evidence, without claiming a live publication or actual App token execution.

A baseline comparison against `9cec62231ce0bb53c5e7b0d02fbfed431734880a`
confirmed no changes to package CLI/source/tests, Composer manifest/lock,
Lefthook configuration, repository hook setup or hook runtime code. The separately
authorized local launcher replacement does not modify versioned hook behavior.
The final documentation update passed strict OpenSpec and whitespace validation.
Its initial push at `06ffd835fd00d5a990b15b64aa93f57e750c7e28` passed all seven
native pre-push checks in `20261017-234426-519`, without bypass.

## Infrastructure-only scope reconciliation — 2026-10-18 UTC

The maintainer approved removing the former real-publication task rather than
reporting it as executed. The proposal, design, delta requirements and tasks now
define completion as implemented, activated, validated and documented
infrastructure. The task list retains its original numbering for historical
traceability and contains 23 tasks. Task 4.7 aligns this convention/evidence with
that scope; no live-publication task remains.

This documentation-only continuation preserved the zero-approval policy,
required check, verified protections, App settings evidence, recovery guidance
and confirmed fixture deletion. Strict OpenSpec and whitespace checks passed.
The current update changes no workflow, helper, package code, manifest/lock or
versioned hook behavior. Authenticated readback before completion found no tags,
no GitHub Releases and only `main` and `change/protected-release-workflow` branches;
the manifest still has no `version`. No production release branch, version, tag
or GitHub Release was introduced. Actual App token issuance and live publication
remain explicitly unexercised; their future verification is outside this change.

The scope-reconciliation commit `5fb0f16` passed all seven native pre-push checks
in execution `20261018-002322-302`, without bypass. The schema-4 summary reports
`passed`, exit 0, with all seven validation outcomes passed.

## Completed infrastructure gates

| Task | Evidence / next action |
| --- | --- |
| 4.2 | Completed: maintainer-observed App ID/installation/all-repository code read/write access match bypass actor `5338805`; API readback confirms variable/secret presence and unchanged all-tag restrictions. Actual token execution is untested. |
| 4.3 | Completed: ordinary-merge, CI and zero-approval settings are authenticated above. Independent reviewer availability is not an activation gate; preserve the confirmed settings. |
| 4.4 | Completed: ordinary PR #1 integrated the workflows after successful `Validate Release Branch`; the exact GitHub Actions check and up-to-date policy are required, with the existing controls and zero approvals preserved. |
| 4.5 | Completed: authorized isolated probes prove tag creation/update/deletion, direct main push and failing-check merge denials, plus a successful zero-review merge. Production PR #1 separately proves the ordinary production path. The maintainer deleted the fixture after evidence capture; cleanup is complete. |
| 4.7 | Completed: convention and evidence describe infrastructure-only completion, the zero-approval policy, verified gates and fixture cleanup. Actual App token issuance/live publication remain unexercised limitations outside this change. |

Infrastructure acceptance combines authenticated API readback, maintainer-observed
App installation settings and isolated enforcement evidence. Production publication
is not inferred from those checks. Before a later authorized real release, re-read
the remote state. If merge queue is active or platform/control
constraints make the policy unsatisfiable, stop activation and resolve
that scope explicitly. Live tests must not consume disposable production versions.

## Artifact and scope review

Proposal, design, delta requirements, tasks, implementation and convention agree
on branch authority, explicit manifest copy, exact succession, strict Composer
validation, immutable integrated tagging and separate activation gates. There are
no temporary-input dependencies. The general operational instructions are indexed
in `AGENTS.md`; public README/package behavior remains unchanged. The package CLI,
Composer manifest/lock, local pre-push code/configuration and unrelated files were
not changed. The initial untracked change artifacts were preserved and updated only
for task completion and this evidence note.

OpenSpec strict validation passed. Final review covered both tracked diffs and the
new workflow/helper/test/convention files, including the action pins, read-only
boundary, create-only ref request and the untouched package/hook files. Local
completion is supported by the separate settings/enforcement evidence above;
it does not claim actual App token issuance or live publication has been exercised.
That future verification is outside the completed infrastructure change.
