# Proposal

## Why

Before the first package version is published, the existing protected-tag workflow should also publish its GitHub Release automatically. This gives each successfully tagged version a visible release page with GitHub-generated notes while preserving the tag-based version contract and the existing Packagist integration.

## What Changes

- Extend the existing post-merge workflow with `github-release`, named `Publish GitHub Release`, dependent on successful protected-tag publication.
- Keep the Release coordinator in `tools/release/github_release.py`, loaded through a full checkout of the executing workflow revision with persisted credentials disabled, and invoke it from a single-line workflow command.
- Export the publisher's already validated `tag` and `sha` as job outputs without changing the `authority` step's interface or permitting existing tags during tag publication.
- Verify the exact remote tag and integrated SHA before publishing a normal, non-draft, non-prerelease Release titled with its tag, using generated notes even for `v0.1.0`.
- Use the new job's `GITHUB_TOKEN` with `contents: write`; retain the App token exclusively for protected-tag creation and preserve existing jobs' permissions, eligibility, check names, and serialization.
- Make Release recovery independent of tag publication: reuse successful job outputs, accept an existing normal published Release without edits, reject conflicting drafts/prereleases, and fail on lookup errors.
- Extend mocked workflow tests and contributor release guidance to cover the job boundary, publication, repetition, and failure recovery.

## Capabilities

### New Capabilities

None. GitHub Release presentation extends the existing release lifecycle.

### Modified Capabilities

- `release-tagging`: add automatic GitHub Release publication after protected-tag creation, scoped credentials, validated output handoff, and independent recovery.

## Impact

The implementation will affect `.github/workflows/create-release-tag.yml`, the dedicated Release coordinator and automation tests under `tools/release/`, and `conventions/releases.md`. The added automation interface consists of the publisher job's `tag` and `sha` outputs; package APIs and Composer metadata remain unchanged. The Release job uses the runner's GitHub CLI and checks out the exact `github.workflow_sha` with `persist-credentials: false`, following the protected publisher's existing pattern without new dependencies. This replaces the initial no-checkout implementation; it does not change version authority or recovery behavior.

Packagist is already integrated and continues discovering versions from VCS tags independently of GitHub Release presentation. No PAT, secrets, publication triggers, App permission changes, protection changes, or distribution assets are introduced. Existing automatically offered GitHub source archives are sufficient.

This is infrastructure preparation only. Implementation and validation must not create a production release branch, declare a manifest version, create a tag or Release, or publish a disposable version. The existing first-version contract remains `0.1.0`. Git/GitHub state changes, including commits, pushes, PRs, and merges, require their own concrete authorization under `conventions/git.md`.

The main operational risk is a valid tag without its Release after a presentation failure. Recovery therefore reruns only the Release job; it never weakens the publisher's rejection of existing tags. API errors and conflicting Releases must remain visible failures instead of causing edits or duplicate publication attempts.

### Consulted Context

Planning consulted `AGENTS.md`, `openspec/config.yaml`, the complete `release-tagging` specification, and the applicable language, workflow, release, Git, Git hook, environment, repository, artifact, and context-mode conventions. Inspection also covered both release workflows, `authority.py`, the shared GitHub API transport, and the existing workflow and Composer tests.

Read-only inspection on November 27, 2026 found no remote tags, GitHub Releases, or open PRs in `GustavoPeixoto/php-qa-scope`. The 23 existing release tests passed with the documented host-workspace mapping, and all eight existing specifications passed strict validation. These are local and read-only baseline observations; they do not prove future App-token issuance or live Release publication. No temporary handoff or conversational history is required to understand this change.

## Open Questions

None. There are no unresolved scope, design, or acceptance decisions before implementation. Live publication remains deliberately unexercised until a separately authorized real release; it is not a prerequisite for completing this infrastructure change.
