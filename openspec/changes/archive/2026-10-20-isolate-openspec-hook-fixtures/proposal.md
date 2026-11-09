# Proposal

## Why

Hook integration tests copy the repository's live `openspec/` tree and expect a
particular real change to remain active. Archiving `configure-git-qa-hooks`
therefore broke a test even though the hook's validation behavior did not change.
Test-owned synthetic OpenSpec projects will make those results reproducible
through the project's normal planning and archive lifecycle.

## What Changes

- Generate a minimal synthetic OpenSpec project for hook test repositories,
  including explicit valid-spec, valid-pending-change, invalid-delta, and archived
  change scenarios.
- Replace the live-tree copy in `assembled()` and the separate Docker/native
  acceptance fixture with that shared preparation helper.
- Replace assertions about real change IDs with exact expectations for
  test-owned identities and validation results.
- Keep real OpenSpec 1.14.0 execution in integration/native acceptance; existing
  CLI doubles remain available for scheduler, report-error, and signal tests.
- Verify that fixture construction does not read the contributor's OpenSpec
  directory, inherit project/store configuration, or modify contributor state.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `repository-git-hooks`: Require self-contained synthetic OpenSpec inputs for
  automated hook fixtures, with lifecycle-independent acceptance scenarios and
  continued real-CLI verification.

## Impact

Affected implementation is limited to test fixture preparation and assertions in
`tools/git_hooks/`, including integration/terminal consumers of `assembled()` and
the opt-in native acceptance setup. A small standard-library fixture helper and
focused tests may be added. Contributor test instructions in
`conventions/git-hooks.md` should describe the isolation boundary.

Hook runtime, command vectors, report validators/formats, seven-check scheduling,
container cleanup, PHP package behavior, dependencies, versions, and distribution
remain unchanged. The helper still copies the package/automation inputs needed
by existing tests; only OpenSpec project content becomes synthetic.

Out of scope: the separate `add-required-pr-qa` implementation and rollout,
restoring its stash, production specs/archive cleanup, and the independently
observed terminal cancellation/fake-Docker metadata races. Those failures must
be reported separately rather than hidden or treated as repaired by this change.

The main risk is changing a helper shared by integration and terminal tests, or
accidentally replacing real OpenSpec acceptance with a mock result. Run the
focused fixture/CLI cases and the existing hook suite, and report native
acceptance prerequisites/skips explicitly.

Consulted durable sources: `conventions/workflow.md`,
`conventions/git-hooks.md`, `conventions/artifacts.md`,
`openspec/specs/repository-git-hooks/spec.md`,
`tools/git_hooks/test_hooks_integration.py`,
`tools/git_hooks/test_hooks_terminal.py`, and
`tools/git_hooks/fake_openspec_fixture.py`. This proposal records the required
problem and scope without depending on an active unrelated change or temporary
verification logs.

## Open Questions

No unresolved scope or design questions. **Verification prerequisite:** real-CLI
acceptance needs OpenSpec 1.14.0 and pinned Lefthook; opt-in native acceptance
additionally needs the documented dev/PHP services and Docker. Unavailable
prerequisites must be reported as unverified coverage, not successful checks.
