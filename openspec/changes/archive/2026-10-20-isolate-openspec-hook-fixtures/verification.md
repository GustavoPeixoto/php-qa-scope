# Verification

Date: 2026-10-20 (America/Sao_Paulo).

## Implementation evidence

- `tools/git_hooks/openspec_test_fixture.py` owns deterministic base, pending,
  invalid, and archived OpenSpec projects. It rejects an existing tree and has
  no contributor OpenSpec inputs or hook-runtime imports.
- `assembled()` generates the selected project before its fixture commit.
  Its real-CLI test uses four fresh repositories and asserts exact native
  item identities/validity, nearest fixture root, exit codes, report validity,
  all seven outcomes, retained layout, unchanged OpenSpec bytes, and clean Git
  state. Pending and archived unchecked tasks remain unchanged.
- `prepare_native_sources()` excludes contributor OpenSpec content and generates
  a pending project before native acceptance initializes Git. Its invalid-delta
  step uses the same helper's synthetic change, retaining equivalent native
  report and unchanged-state assertions.
- Construction tests reject contributor OpenSpec reads, traversal, and metadata
  access in both preparation paths. The native construction test requires no
  Docker. Terminal consumers retain the existing fake CLI and instrumentation.
- `conventions/git-hooks.md` documents generation, the four real-CLI scenarios,
  focused/default commands, native acceptance, and prerequisite skips.

## Focused checks

OpenSpec 1.14.0 and Lefthook 2.1.16 were available on PATH.

```sh
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_openspec_fixture test_hooks_integration.HookIntegrationTests.test_real_openspec_cli_synthetic_scenarios
```

Passed: 6 tests in 13.624 seconds, no skips. The real-CLI method covers all four
scenarios. Base and archived reports contain only valid `fixture-spec`;
pending also contains valid `fixture-pending-change`; invalid also contains
invalid `fixture-invalid-change` with the missing-scenario diagnostic. Native
OpenSpec codes are base=0, pending=0, invalid=1, and archived=0.

```sh
PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest test_openspec_fixture test_hooks_integration.HookIntegrationTests.test_openspec_findings_and_bad_output_collect_all_seven test_hooks_terminal.TerminalTests.test_openspec_version_probe_node_descendants_cancel_before_allocation test_hooks_terminal.TerminalTests.test_openspec_local_descendants_cancel_with_php_jobs test_hooks_terminal.TerminalTests.test_manual_attached_detached_stdin_open_and_no_remote_change
```

Passed: 8 tests in 29.375 seconds, no skips. This run preceded addition of the
fifth construction test; that test is included in the six-test focused run above.
An initial guard failure incorrectly treated directory-relative temporary-tree
cleanup as contributor access. Resolving `dir_fd` paths fixed the test guard;
the reported focused results are from subsequent successful runs.

## Native acceptance

```sh
QA_HOOKS_NATIVE_ACCEPTANCE=1 PYTHONPATH=tools:tools/git_hooks python3 -B -m unittest -v test_hooks_integration.NativeAcceptanceTests
```

Passed: 1 opt-in test in 203.847 seconds, no skips. Docker and both running
dev/PHP services were available. The test verified the actual npm/Node/native
Lefthook 2.1.16 frontend and the pinned OpenSpec runtime, successful Git push,
attached/detached manual validation, intentional QA Scope rejection, intentional
OpenSpec rejection, cancellation at container lifecycle barriers, native PHP
descendant teardown, repeated interruption, overlapping runs, unrelated process
survival, unchanged remote refs after manual runs, and owned-container cleanup.

Sixteen report directories are retained under
`tmp/git-hooks-verification/native-reports/` (UTC execution names):

| Execution | Result and evidence |
| --- | --- |
| `20261021-020310-410` | Git push passed; exact valid synthetic spec and pending change, all seven passed. |
| `20261021-020325-093` | Attached manual run passed; same exact valid synthetic items. |
| `20261021-020338-434` | Detached manual run passed; same exact valid synthetic items. |
| `20261021-020352-473` | Intentional QA Scope Git rejection; OpenSpec passed. |
| `20261021-020408-151` | Intentional QA Scope manual rejection; OpenSpec passed. |
| `20261021-020423-870` | Intentional OpenSpec rejection: native code 1, valid failure report, exact valid spec/pending items plus invalid `fixture-invalid-change`; all six PHP checks passed. |
| `20261021-020442-262` through `20261021-020604-961` | Ten interrupted runs covering lifecycle barriers and native cancellation/overlap checks; retained evidence and owned cleanup verified. |

The successful and invalid-delta stages checked unchanged synthetic files and
clean tracked state. Existing flat-layout evidence was preserved. Native
acceptance completed without prerequisite gaps or cancellation failures.

## Full regression suite

```sh
PYTHONPATH=tools python3 -B -m unittest discover -v -s tools/git_hooks -p 'test_*.py'
```

Passed: 66 tests in 424.973 seconds, with 65 passing and one expected skip.
The skip is `NativeAcceptanceTests`, which requires
`QA_HOOKS_NATIVE_ACCEPTANCE=1`; its separate successful opt-in run is documented
above. There were no missing OpenSpec/Lefthook prerequisite skips and no failed
tests. The previously noted cancellation/fake-engine races did not reproduce;
no runtime or race fixes were needed. The actual npm frontend phase matrix,
real Git cancellation paths, container lifecycle/report checks, and all five
new construction tests passed.

## Scope and contributor state

Changes are limited to the shared test generator, its construction tests,
integration/native fixture preparation and assertions, hook contributor guidance,
and this OpenSpec change's tracking/evidence. Hook runtime, command vectors,
report validators/formats, scheduler, teardown, pins, PHP source/configuration,
Composer files, and terminal test code remain unchanged.

The contributor checkout started at
`e4c36dd0f1d1f11fc5f9df8dad6f4d74356bbec9` on
`change/release-validation-tooling`, with only this untracked OpenSpec change.
Final read-only checks confirmed the same branch/HEAD, an empty staged diff,
and only the intended fixture/convention/change-artifact worktree changes.
Contributor index, branch, HEAD, stash, remotes, and hooks were not altered by
this work. The stash tip remains `51a96168b06e7dcefe98623831c7f8b1aa750f54`:
`wip: add-required-pr-qa before isolate-openspec-hook-fixtures`; the older
`On main: TODO` entry remains present. Test Git operations occur only in
disposable fixture repositories.

## Artifact consistency and validation

Proposal, design, delta scenarios, and task scope map to the implementation
evidence above. The artifacts explain the historical-ID regression and both
preparation paths without depending on a temporary handoff or an active real
change. Temporary native report paths are supporting evidence only.

Both required validations passed:

```sh
openspec validate isolate-openspec-hook-fixtures --strict --no-interactive
openspec validate --all --strict --no-interactive --json
```

The change is valid. Repository validation selected `/php-qa-scope` as the
nearest root and reported 6/6 valid items: one active change and five durable
specs, with no failures. `git diff --check` passed. Final contributor state
checks matched the recorded baseline; dev and PHP services remained running.
