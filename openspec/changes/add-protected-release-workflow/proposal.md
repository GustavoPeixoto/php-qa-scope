## Why

The package needs a PR-based release process that keeps its Composer metadata consistent with its Git tags and rejects invalid version progression before publication. Release preparation must also produce a meaningful PR when all product changes are already on `main`; updating `composer.json` provides that change without introducing a separate version file.

## What Changes

- Introduce release PRs from same-repository branches named `release/vX.Y.Z` to `main`. The branch declares the intended version; the PR must set `composer.json`'s `version` to the identical `X.Y.Z` string.
- Accept only stable versions with canonical non-negative integer components. Reject prerelease/build suffixes and leading zeros. With no published stable tags, require `0.1.0`; otherwise allow exactly the next patch, minor, or major relative to the greatest published stable version.
- Run a required `Validate Release Branch` check on every PR to `main`. Ordinary PRs pass the release-specific checks without requiring release naming or a version bump. Release PRs also undergo strict Composer validation, with only Composer's advisory about declaring `version` explicitly disabled.
- After an eligible PR merges, revalidate the merged manifest and current remote tags, then create a lightweight `vX.Y.Z` tag at the PR's integrated commit using the `release-bot` GitHub App. Serialize publication, fail safely on stale versions or existing tags, and never move/delete tags.
- Require PRs and successful automatic checks on `main`, with zero required human approvals in this initial phase. Independent reviewers, mandatory CODEOWNER review, stale-approval dismissal, and approval of the latest push are not activation prerequisites. Preserve tag protection and the main deletion/force-push restrictions without adding main bypasses.
- Complete this change with the release infrastructure implemented, activated and validated, including its operational guidance and evidence. Executing a real release is outside this change's scope and is not a completion prerequisite. Document bootstrap, failure recovery, and the distinction between verified infrastructure and unexercised live publication.

Out of scope: executing a production release or its live acceptance; a `VERSION` file; automatic version selection; prereleases or build metadata; maintenance release lines; GitHub merge queue integration; GitHub Release creation; changelog generation; deployment; automatic Packagist registration or webhook configuration; and changes to package CLI behavior or local pre-push policy.

## Capabilities

### New Capabilities

- `release-tagging`: PR-based release validation, synchronized Composer version metadata, strict version succession, and protected post-merge Git tagging.

### Modified Capabilities

None. Existing package behavior and repository Git hook requirements remain unchanged.

## Impact

- Repository target: `GustavoPeixoto/php-qa-scope`, package `gustavo-peixoto/php-qa-scope`, release destination `main`.
- Initial authenticated API inspection on 2026-10-17 confirmed default branch `main`, no remote tags or registered Actions workflows, and active tag ruleset `Protect releases` (ID `25208186`). The workflows have since been integrated, while tags remain empty. The ruleset covers `~ALL` tags with creation/update/deletion/non-fast-forward restrictions and a single Integration bypass actor (ID `5338805`). Preserve that broader coverage. The maintainer confirmed App `gustavopeixoto-releasebot`, ID `5338805`, installed for all account repositories with code read/write permission. This settings evidence is distinct from App-authenticated API/token execution, which the CLI OAuth session cannot perform.
- The maintainer created `Protect main` (ID `25322253`), active only for `refs/heads/main`, with an empty bypass list, a PR requirement, zero required approvals, no mandatory CODEOWNER/latest-push approval, and deletion/force-push blocks. The initial PR-only bootstrap was incomplete; rollout subsequently required the actually emitted `Validate Release Branch` from integration `15368` and an up-to-date branch. Ordinary zero-review production merges and isolated negative enforcement probes are recorded in `verification.md`.
- Add a PR-validation workflow and replace the existing local release-workflow draft with the agreed two-workflow design. The observed draft reads `VERSION` and does not provide the required PR check or progression validation; this proposal contains the replacement contract and does not depend on retaining that draft.
- Introduce internal release-validation helpers/tests under `tools/`, release operation guidance under `conventions/`, and an entry in `AGENTS.md`. Exclude repository-only GitHub support files from Composer dist archives using `.gitattributes`.
- The first release PR adds `version: 0.1.0` to the currently unversioned manifest. Do not add it prematurely while installing the workflow; later release PRs update it. Keep Composer lock consistency checks enabled and refresh lock metadata only when necessary, without dependency upgrades.
- This change must not create a production release branch, add a manifest version, publish a tag, or create a GitHub Release. A future real release requires separate explicit maintainer authorization and its own live verification; it is not unfinished work in this change.
- Packagist obtains release versions from VCS tags. The manifest value is an intentionally synchronized copy enforced by automation, rather than a second authority.
- The `release-bot` App, tag ruleset, Actions variable `RELEASE_APP_CLIENT_ID`, and secret `RELEASE_APP_PRIVATE_KEY` are already provisioned. Verify their effective configuration and enforcement; do not recreate them or expose credentials. The App must be installed for this repository with `Contents: write`, and its bypass must be confined to the relevant tag rules.
- Main protection must require a PR, zero human approvals, and `Validate Release Branch` plus any existing required CI checks once the release check has actually run on an ordinary PR. Workflow and ownership changes follow that same PR/check policy; mandatory CODEOWNERS is not required for this initial single-maintainer phase. Preserve the current main restrictions and empty bypass list. Introducing an approval requirement later needs a separate explicit policy decision.
- Risks: stale PR checks after another release, concurrent or delayed publication, credential misuse, and a merged release whose tag creation fails. The initial policy provides no independent human review of workflow changes. Fail without retagging and document recovery; verify remote controls before declaring infrastructure activation complete. Actual App token issuance and end-to-end live publication remain unexercised limitations of the evidence; completing this infrastructure change does not claim they passed.
- Consulted durable project context: `AGENTS.md`, `composer.json`, `.gitattributes`, repository/language/workflow/environment/artifact conventions, and the existing OpenSpec capability inventory. No temporary-file content or references are needed to interpret this change.

## Open Questions

- **Resolved — App verification:** Maintainer-observed authenticated installation/permissions match the API-observed tag bypass; variable/secret presence remains confirmed. Actual App token issuance remains untested and belongs to future live publication verification outside this change.
- **Resolved — required-check activation and topology:** The workflows were integrated by ordinary PR; `Validate Release Branch` is required with an up-to-date branch. Merge queue is disabled, zero human approvals and no main bypass are preserved. Isolated probes verified denials and a successful zero-review merge.
- **Resolved — completion scope:** A real release and its live acceptance are outside this change. Their unexercised status is a documented limitation, not a pending implementation task. The maintainer deleted the authorized isolated fixture after evidence capture; cleanup is complete.
- No relevant open questions remain. Version-source, manifest-synchronization, suffix, version-progression, initial approval-policy and infrastructure-only completion decisions are settled. Task 4.7 tracks the remaining alignment of operational guidance and verification evidence with this scope.
