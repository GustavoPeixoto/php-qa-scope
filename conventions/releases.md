---
id: releases
title: Release Convention
when: Whenever preparing, validating, publishing, activating, or recovering a package release or changing release automation and protections.
---

# Release Convention

## Preparation

Infrastructure preparation and activation do not authorize a real release. Keep
production release branches, manifest version edits, tags and GitHub Releases
pending until the maintainer explicitly requests publication. Ordinary
infrastructure PRs need no version change and do not publish a tag.

Use an ordinary same-repository PR into `main`, from `release/vX.Y.Z`.
The branch is authoritative; the root `composer.json` must declare the identical
string `"version": "X.Y.Z"`. Use ASCII integers without leading zeros, whitespace,
prerelease suffixes, or build metadata. There is no `VERSION` file.

Install the release infrastructure without adding a manifest version. With no
stable remote tags, the first real release PR adds `"version": "0.1.0"`. Later
release PRs update that field. All product work can already be merged: this
manifest-only preparation diff is sufficient (preserve the manifest's other keys):

```diff
   "name": "gustavo-peixoto/php-qa-scope",
+  "version": "0.1.0",
```

Start from current `main`, create `release/v0.1.0` for that first release, edit the
manifest, validate, and submit the PR through the required PR/check process. Pushes
remain subject to the existing Git and pre-push conventions. Reserve version edits
for release preparation; ordinary feature PRs need no version change.

Read every remote tag page. The greatest numeric canonical `vX.Y.Z` or `X.Y.Z`
is the baseline; nonstable tags do not count. From `M.m.p`, choose exactly
`(M+1).0.0`, `M.(m+1).0`, or `M.m.(p+1)`, according to compatibility review.
For example, after `0.2.7`, choose `0.2.8`, `0.3.0`, or `1.0.0`; after `1.0.0`,
choose `1.0.1`, `1.1.0`, or `2.0.0`. Skips and maintenance lines are unsupported.
API failures never mean empty history. Finish one release before merging another.

## Validation and publication

The exact required job/check name is `Validate Release Branch`. It runs on every
PR to `main` when opened, reopened, synchronized, or marked ready. Ordinary PRs,
including forks, pass release-specific checks. Any `release/` prefix opts into
validation; malformed names and release-named forks fail.

Both release PR content and the exact integrated commit use Composer 2.10.3:

```sh
composer --no-plugins --no-scripts validate --strict --no-check-version
```

For the running PHP service, prefix that command with `docker compose exec -T php`.
The option suppresses only the advisory against explicitly declaring `version`.
Schema, publishability, other strict warnings, and existing lock consistency still
fail. Do not install dependencies, run scripts, enable plugins, suppress all
warnings, or disable lock/publishability checks. If lock metadata is stale, use
`composer --no-plugins --no-scripts update --lock --no-install` in the PHP
environment, review the diff, and confirm no dependency versions changed before
rerunning validation. Do not run this recovery command unless a stale lock needs
repair; it may contact configured repositories.

After an eligible merge, `Validate Merged Release` checks out `merge_commit_sha`
without persisted credentials and repeats validation. Squash and rebase releases
also use that integrated SHA. The dependent publisher has no checkout and imports
no repository code. It independently reads the PR, immutable manifest, and fresh
remote tag pages with a read-only token. Only after those checks pass does it
request a repository-scoped `release-bot` token with `Contents: write`, using
`RELEASE_APP_CLIENT_ID` and `RELEASE_APP_PRIVATE_KEY`. Only create-ref receives
that token. It creates a lightweight `refs/tags/vX.Y.Z` at the verified SHA.

Publication is serialized repository-wide with `cancel-in-progress: false`.
GitHub can replace a pending concurrency run; this is not a durable release queue.
A running publisher is not canceled by a newer attempt. The create-only API and
tag rules must prevent competing writers. Existing tags always fail, even when
they already reference the requested SHA. No step moves/deletes a tag or chooses
a fallback version.

## Activation gates

Infrastructure activation requires verified remote controls; actual publication
acceptance remains separate and pending until a later authorized real release.
See the change's `verification.md` for dated evidence and remaining blockers.

The initial single-maintainer policy requires PRs and automatic checks with
**zero required human approvals**. Independent reviewers, mandatory CODEOWNER
review, stale-approval dismissal and approval of the latest push are not
prerequisites. The maintainer may merge their own PR when the applicable checks
pass. This policy does not guarantee another person's review of workflow changes;
adding that requirement later needs an explicit policy revision.

Authenticated rollout verification on 2026-10-17 confirmed that `Protect main`
requires `Validate Release Branch` from GitHub Actions (integration `15368`), with
an up-to-date branch, zero approvals and no bypass. Infrastructure PR #1 merged
under those rules. The maintainer confirmed App `gustavopeixoto-releasebot`
(ID `5338805`) is installed for all account repositories with code read/write
access; this matches the sole tag bypass actor. Isolated authenticated probes
verified protected tag mutation, direct main push and failing-check merge denials,
plus a zero-review successful merge. See the change's `verification.md` for the
evidence and its limits. No real release or App token issuance was exercised.

1. Preserve active `Protect main` (ID `25322253`), targeting only
   `refs/heads/main`: PRs, zero approvals, deletion/force-push blocks and an empty
   bypass list. Integrate the tested workflows through an ordinary infrastructure
   PR, without release naming or a manifest version.
2. Let an ordinary PR emit `Validate Release Branch`, then require that exact
   check and any existing required CI, with an up-to-date branch before merge.
   A ruleset requiring only PRs is partial bootstrap. Do not declare full
   activation while required checks are absent. Keep the bypass list empty;
   `.github/` and `tools/release/` follow the same PR/check policy without
   mandatory CODEOWNERS or another person's approval.
3. Verify ordinary merges and a disabled merge queue before requiring the check.
   Queue integration is outside this change. Record platform or unverified-control
   limitations as blockers; the absence of another reviewer is not a blocker
   under this initial policy.
4. Verify the actual already provisioned App identity, installation, repository
   access, contents-write permission, Actions variable/secret presence and tag
   bypass. The logical name `release-bot` alone does not identify its public slug.
   Preserve `Protect releases` (ID `25208186`) coverage of `~ALL` and its
   creation/update/deletion/non-fast-forward restrictions. Limit the App bypass
   to tags, never main; do not print credentials or recreate the infrastructure.
   A repository-admin CLI OAuth session cannot substitute for App-specific
   credentials at installation endpoints; record that limitation rather than
   claiming installation access was verified.
5. Coordinate enforcement probes in isolated fixtures or a disposable repository.
   Prove ordinary-user/PAT protected tag creation/update/deletion, direct main
   pushes and failed-check merges are rejected, while a PR meeting the checks
   can merge with zero approvals from others. Do not disable rules or create
   disposable production tags. Configuration readback alone does not prove these
   mutations are rejected.
6. Keep real publication acceptance pending during infrastructure work. Only after
   separate maintainer authorization, publish the real next release through its
   manifest-change PR, re-read current tags, confirm the App actor and exact
   integrated SHA, and verify existing refs are unchanged.

## Recovery and rollback

If publication fails or is canceled, the merged code remains on `main` and its
tag may be absent. Inspect the original run, PR integrated SHA, current remote
tags, and error. Resolve the cause before retrying that existing merged-PR run.
Retry only when its exact target is absent and its candidate remains a permitted
successor of the current numeric maximum. A previous successful PR check is not
current publication authority. An existing target, even at the correct SHA, makes
a retry fail; verify the prior publication instead. Never treat an API error as
an absent ref.

For example, if `release/v1.0.1` merged but `v1.1.0` published before recovery,
`1.0.1` is stale: prepare a new PR for `1.1.1`, `1.2.0`, or `2.0.0`. Do not move
`v1.1.0`. If a pending attempt was replaced, inspect whether its tag exists and
apply the same retry prerequisites. If a published package needs correction,
publish a successor. No manual publication trigger or bypass is provided.

For an authorized rollback, stop future publisher runs and revert automation
through review, retaining protections and all published tags. Do not undo a release
by deleting or moving its ref.

## Distribution and verification

These workflows create Git tags, not GitHub Releases. Packagist discovers package
versions from VCS tags; its registration/webhook setup is separate and is not
automated here. The manifest version is an enforced copy of the branch intent,
not an independently selected version. `.github/`, `tools/`, and `conventions/`
are excluded from Composer dist archives; runtime files and `composer.json` remain.

Run release automation tests in dev with:

```sh
PYTHONPATH=tools python3 -B -m unittest discover -s tools/release -p 'test_*.py'
```

Keep local fixture evidence separate from authenticated protection verification
and the controlled real release. Unverified activation tasks remain unchecked.
