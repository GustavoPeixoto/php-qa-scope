# Design

## Context

See `proposal.md` for motivation and scope. The current `create-release-tag.yml` workflow has two jobs: `validate` checks the exact integrated commit, and `publish` independently revalidates authority inside the `protected-release-publication` concurrency group before generating an App token and creating a lightweight tag. The `authority` step already emits the exact `tag` and `sha` through `GITHUB_OUTPUT`.

Existing tags are deliberately fatal to the publisher, even when their SHA matches. Release presentation must therefore be a separate downstream job rather than another publisher step. Current workflow tests execute real shell blocks with mocked GitHub responses, but several extract `publish` as everything through the end of the workflow; these selectors need explicit job boundaries before another job is appended.

## Goals / Non-Goals

**Goals:** Keep validated version/SHA identity across jobs, isolate Release credentials, detect conflicting Releases, and support recovery without reentering tag authority. Make the workflow's actual commands executable under the existing fixture approach.

**Non-Goals:** Change the shared version contract, relax duplicate-tag rejection, execute package content in the Release job, introduce a new release entry point, backfill historical tags, or change repository/App/Packagist configuration. This proposal does not authorize implementation or any real release.

## Decisions

### 1. Add a downstream job with an explicit authority handoff

Expose `publish.outputs.tag` as `${{ steps.authority.outputs.tag }}` and `publish.outputs.sha` as `${{ steps.authority.outputs.sha }}`. Do not change `authority.py`, its step ID, or its output format. Outputs become usable for Release publication only after the publisher job succeeds, including successful tag creation.

Add `github-release`, named `Publish GitHub Release`, with `needs: publish`, on `ubuntu-24.04`. Retain the default success-dependent job condition; do not add `always()` or another eligibility expression. Existing validate/publish conditions and concurrency blocks stay verbatim. The new job needs no additional concurrency group: the original group continues serializing protected-tag authority and creation, and Release conflicts fail safely without modifying tags.

Supply `TAG` and `MERGE_SHA` from `needs.publish.outputs` and use `GITHUB_REPOSITORY` for every explicit repository endpoint. These environment values are data, never interpolated into Python source or unquoted executable expressions. Neither the current `main` nor the source branch tip supplies version or SHA authority.

Putting Release creation in the publisher was rejected because a Release failure would make recovery reenter tag creation. A tag-push workflow or manual dispatch was rejected because it adds a publication trigger and loses the existing explicit job-output handoff.

### 2. Keep credential grants confined to their jobs

| Boundary | Normal token | App credentials |
| --- | --- | --- |
| Workflow default and integrated validation | Existing `contents: read` | None |
| Protected-tag publisher | Existing `contents: read`, `pull-requests: read` | Existing token action; installation token only in create-ref step |
| GitHub Release job | Job-local `contents: write` | None |

Set `GH_TOKEN` in the Release execution step from `${{ github.token }}`. Do not promote write permissions to workflow level, introduce PATs/secrets, or reuse the App token for presentation. The new job performs no dependency installation, Docker build, or package-code execution.

Use `tools/release/github_release.py` as an independent coordinator with `main()` and a guarded entry point, using only the standard library and subprocess calls to the runner's `gh`. Run it with `python3 -I -B tools/release/github_release.py`, retaining the current environment inputs, diagnostics, exit behavior, and publication/recovery logic. Shared release-authority modules remain unchanged and are not imported by the new job.

Before execution, add `Checkout repository` using the existing publisher's pinned checkout action, `repository: ${{ github.repository }}`, `ref: ${{ github.workflow_sha }}`, and `persist-credentials: false`. Use the default workspace and a full checkout without optional `path` or sparse settings. This is the fourth checkout across the release workflows; the other three retain their names, revisions, and credentials policy. The checkout action uses the job's normal token; the App remains exclusive to protected-tag creation.

The approved extraction replaces the initial no-checkout constraint to follow the repository's established loading pattern and keep Python outside YAML. Downloading executable content through the API was considered but would add another loading mechanism. The selected automation revision is independent of `MERGE_SHA`: missing checkout content or a missing script fails before Release API activity, without fallback to a moving branch, candidate directory, previous path, or inline code.

### 3. Verify the tag, then discover Releases through successful pagination

Reject missing or malformed tag/SHA inputs before API calls. Retrieve `repos/{repository}/git/ref/tags/{tag}` through `gh api --method GET`. Require the exact `refs/tags/{tag}` reference, `object.type == commit`, and `object.sha == MERGE_SHA`. The existing publisher creates lightweight tags; an unexpected reference type is an error, not an invitation to repair or retag.

After tag verification, retrieve Release pages from `repos/{repository}/releases?per_page=100&page=N` with the write-capable normal token. Use the existing automation's bounded-pagination approach: require valid arrays and Release records, detect repeated pages/identities, and fail if enumeration cannot complete. A short final page establishes completion. Collect exact `tag_name == TAG` matches, including drafts and prereleases. A successful empty result is the only absence signal; every failed request, including HTTP 404, remains fatal. Do not parse human-readable error text to decide absence.

If any matching record is a draft or prerelease, fail with the conflict identified. Otherwise, an existing normal published Release completes the step without writes, regardless of its existing title, notes, or assets. If no match exists, proceed to creation. Invalid or inconsistent matching publication state fails rather than being treated as success.

Listing was chosen over relying exclusively on get-by-tag because the latter is documented as retrieving a published Release, while the listing supports draft discovery for callers with push access. Full successful enumeration also avoids conflating absent Releases with inaccessible resources. Relevant API behavior is documented in [GitHub's Releases REST reference](https://docs.github.com/en/rest/releases/releases#list-releases); all required behavior is stated here and in the delta spec.

### 4. Publish normal Releases with generated notes

Invoke the equivalent of the following argument vector through `subprocess`, without a shell or asset arguments:

```sh
gh release create "$TAG" \
  --repo "$GITHUB_REPOSITORY" \
  --verify-tag \
  --target "$MERGE_SHA" \
  --title "$TAG" \
  --generate-notes \
  --draft=false \
  --prerelease=false
```

The explicit integrated target avoids a moving-branch fallback; `--verify-tag` prevents creation when the tag is absent. Apply the same command to `v0.1.0` and later stable versions. Do not specify custom notes, `--notes-from-tag`, a notes-start tag, uploaded assets, or a special latest-release policy. GitHub's automatic source archives remain available.

The command uses an explicit title because automatic note generation can also generate a title. These flags are documented in the [GitHub CLI reference](https://cli.github.com/manual/gh_release_create). Creation failure is reported immediately without tag cleanup or automatic retries.

### 5. Recover only the presentation job

Once the tag publisher succeeds, a failed Release job can be rerun independently using the successful publisher's stored outputs. Rerunning `github-release` repeats tag verification and discovery, but never authority, progression checks, App-token generation, or create-ref. An existing normal Release is a no-op success, including when an earlier create request succeeded remotely before the client observed failure.

Do not catch every create error and declare success, or edit/delete conflicting Releases automatically. Resolve the cause and rerun the failed job; any corrective Git/GitHub mutation needs its own authorization. Keep the existing tag-publication recovery instructions for cases where tag creation did not succeed, and explain why rerunning all jobs after a successful tag is the wrong presentation-recovery procedure.

GitHub documents that jobs excluded from a partial rerun retain their outputs for the rerun's consumers in [Re-running workflows and jobs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs). Recovery remains subject to platform rerun limits; this change adds no alternative trigger.

### 6. Test actual commands within bounded jobs

Add a job-section selector to `tools/release/test_workflows.py` and migrate helpers/assertions that currently treat the workflow suffix as `publish`. Scope conditions, steps, checkout selection, token references, and permissions to their actual jobs. Preserve the existing fixture coverage rather than weakening global assertions to accommodate write permissions elsewhere.

Extend the fixture pipeline with explicit `validate`, `publish`, and `github-release` outcomes and a stateful fake `gh`. Execute the actual single-line workflow command against the coordinator copied into a temporary selected checkout, with synthetic tokens and API data. Assert argument vectors, ordered requests, unchanged refs and Release content, dependency scheduling, and recovery call counts. Use later-page matches/failures, differing main/head/integrated SHAs, malformed data, conflicts, creation failures, and uncertain remote-success cases. Verify the exact checkout configuration and test a missing script alongside poison candidate/fallback files to prove failure before API activity without executing another source.

Update `conventions/releases.md` alongside the relevant workflow behavior. Replace the current statement that workflows create only tags, retain the existing tag-recovery contract, and document presentation recovery and Packagist independence.

## Risks / Trade-offs

- A tag can publish while its Release fails -> Preserve the tag and recover only the downstream job; Packagist remains tag based.
- State can change between discovery and creation -> Protected tags remain immutable; a competing Release creation may fail this attempt and a later rerun recognizes a normal published Release.
- Pagination adds API requests -> Use 100 records per page and fail closed on incomplete enumeration rather than accepting limited lookup results.
- A full checkout makes package files available in a write-capable job -> Execute only the fixed workflow-revision coordinator with isolated Python; do not import package code or install dependencies.
- Local simulations do not prove live token grants or publication -> Record their limits and defer live verification to a separately authorized real release, without production test versions.

## Migration Plan

Complete and review these planning artifacts first. A later explicit `openspec-apply-change` request may implement the workflow, tests, and release guidance. Validate in `dev` with the release suite and strict OpenSpec checks before presenting a concrete diff for any separately authorized Git operations.

No data migration, Composer version change, infrastructure activation change, or production publication is required. Future integration follows the existing ordinary PR/check policy with unchanged required-check names. If rollback is later authorized, revert only the added presentation automation and corresponding guidance through review, retain protections and existing tags/Releases, and stop future presentation attempts without deleting published versions.
