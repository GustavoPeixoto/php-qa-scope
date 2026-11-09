# Design

## Context

See `proposal.md` for the failure and scope. `assembled()` currently copies
`PROJECT / "openspec"` before committing its temporary repository. Integration
and terminal tests share this helper. The real-CLI integration case then expects
the historical `configure-git-qa-hooks` ID; its invalid-delta branch creates its
own broken input, but its successful branch depends on the copied project.

The opt-in `NativeAcceptanceTests` setup independently includes `openspec` in its
package-input copy list. Fixing only `assembled()` would leave native acceptance
coupled to the live project. The existing fake OpenSpec command is intentional
for process/report/signal tests; replacing it is unnecessary.

## Goals / Non-Goals

**Goals:** Provide one deterministic source of synthetic OpenSpec inputs for both
fixture setup paths; preserve real-CLI coverage and complete hook result checks;
make each validation scenario independent of earlier scenarios and repository
planning state.

**Non-Goals:** Change the hook executable, command/report contracts, runtime
versions, scheduler or teardown; repair unrelated cancellation races; restore or
implement the stashed PR QA change.

## Decisions

### Generate test-owned files through one small helper

Add a standard-library-only test helper, for example
`tools/git_hooks/openspec_test_fixture.py`, with an explicit temporary repository
root and scenario selection. It writes a minimal local `openspec/config.yaml`,
one valid durable spec, and only the scenario-specific change/archive files.
Use test-owned identifiers such as `fixture-spec`, `fixture-pending-change`, and
`fixture-invalid-change`; no production change names, rules, context, or store
pointers are inputs. The fixture's local root is asserted in the real report.

The helper creates files directly and deterministically. It does not run an
interactive bootstrap, install tools, invoke archive operations, copy parent
OpenSpec content, or touch contributor Git state. Keep it outside hook runtime
imports. Reject an existing fixture OpenSpec tree rather than merge stale inputs.

An assertion-only replacement of the historical ID was rejected because copied
unrelated invalid changes could still fail the test. Maintaining a copied
snapshot of the real project was rejected because it obscures what each test
needs and creates unnecessary maintenance.

### Give each scenario a fresh committed repository

Use these explicit inputs and expected results:

| Scenario | Synthetic input | Real bulk result |
| --- | --- | --- |
| Base | One valid durable spec, no active changes | Exit 0; only the expected spec |
| Pending | Base plus a valid active delta and an unchecked task | Exit 0; expected spec and valid synthetic change |
| Invalid | Base plus a delta missing its required scenario | Nonzero; invalid synthetic change identified |
| Archived | Base plus an intentionally invalid archived delta and unfinished tasks | Exit 0; archived identity absent |

Each integration scenario gets its own prepared and committed fixture, avoiding
the existing valid-then-invalid loop's accumulated state. Fixture metadata and
supporting proposal/design/tasks, where needed, are test-owned literals. Assert
identities, validity, root, native code, report validity, seven-result collection,
and unchanged temporary tracked state. Expected outcomes are assertions on the
real report, not a precomputed success response.

### Migrate both preparation paths without changing execution backends

`assembled()` defaults to the base project and accepts an explicit scenario for
real-CLI cases. Replace its OpenSpec copy with the helper before the existing
fixture commit. Terminal tests retain their established fake CLI and lifecycle
instrumentation.

Remove `openspec` from the separate native acceptance copy list and invoke the
same helper before that fixture's initial commit. Its successful baseline uses
the pending scenario to retain real acceptance of unfinished tasks. Its
intentional invalid-delta step uses a synthetic identity and preserves existing
Git/manual, all-seven-result, and report checks.

Add a regression guard that makes access to the contributor's OpenSpec source
fail during fixture preparation. Exercise both preparation paths without
requiring Docker for this construction-only check; extract the native source
preparation into a test helper if needed. Never mutate the contributor's actual
OpenSpec tree merely to simulate contamination. Update the hook convention to
explain synthetic input generation and real-versus-fake CLI coverage.

## Risks / Trade-offs

- Shared setup changes can affect many terminal tests. Run focused fixture/CLI
  tests first, then the full existing hook suite; preserve separate failure
  records for the known cancellation/fake-engine races.
- Handwritten inputs can drift from OpenSpec's accepted syntax. Execute the real
  pinned CLI over every scenario and retain the local-root assertion.
- Minimal fixtures deliberately stop validating this repository's real specs as
  part of hook automation tests. Ordinary repository OpenSpec validation remains
  responsible for those specs; run it separately during verification.
- Native acceptance needs existing dev/PHP services and Docker. Record unavailable
  coverage explicitly and retain current prerequisites instead of silently
  substituting CLI doubles or adding infrastructure changes.

## Migration Plan

Implement the helper and migrate both test preparation paths, update assertions
and contributor test guidance, then run the focused and full verification.
Reverting these test-only changes restores the prior fixture preparation; no
runtime deployment, configuration migration, Git branch change, or stash restore
is part of this plan. Resuming `add-required-pr-qa` is a separate later action;
its hook regression task can be rerun after this change is implemented.
