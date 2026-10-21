# Tasks

## 1. Synthetic project generator

- [x] 1.1 Recheck proposal/design/spec against `conventions/git-hooks.md`, `conventions/artifacts.md`, both OpenSpec source-copy sites in `test_hooks_integration.py`, and the terminal consumers before durable edits; confirm the implementation stays within test fixtures and their documentation.
- [x] 1.2 Add the shared standard-library synthetic-project helper with documented scenario inputs and test-owned config/spec/change/archive content; test deterministic output, rejection of an existing OpenSpec tree, no inherited store/context/rules, and construction without reading contributor OpenSpec files.

## 2. Integration and terminal fixtures

- [x] 2.1 Replace the OpenSpec copy in `assembled()` with the helper and use fresh committed fixtures for base, pending, invalid, and archived real-CLI scenarios; run the focused integration cases and verify exact synthetic item identities/validity, native codes, fixture root, seven outcomes, retained reports, and unchanged tracked fixture files.
- [x] 2.2 Add regression coverage that forbids contributor OpenSpec source access during assembled fixture preparation; verify construction still succeeds and terminal/report/signal consumers retain their existing fake-CLI and execution contracts without historical change-ID expectations.
- [x] 2.3 Update `conventions/git-hooks.md` to explain test-owned OpenSpec inputs, the four real-CLI scenarios, and the distinction from scheduler/report/signal doubles; verify its focused/default test commands match the implemented suite.

## 3. Native acceptance fixture

- [x] 3.1 Remove OpenSpec from the native acceptance source-copy list and invoke the shared generator before its initial fixture commit, using a valid pending baseline and a synthetic invalid-delta rejection; test this source preparation with contributor OpenSpec access forbidden without requiring Docker.
- [x] 3.2 Run the documented opt-in native acceptance when its dev/PHP/Docker prerequisites are available; verify real pinned OpenSpec acceptance/rejection and preserved Git/manual/all-seven evidence, or record the exact unavailable prerequisite and leave native coverage explicitly unverified.
- [x] 3.3 Extend the hook convention's native acceptance guidance to state that the same synthetic project generator is used and retain existing prerequisites, evidence paths, and lifecycle expectations; check the guidance against the native setup and observed execution or limitation.

## 4. Regression and consistency

- [x] 4.1 Run the complete hook Python suite and record dated results in this change's `verification.md`, separately identifying any unchanged cancellation/fake-engine failures and prerequisite skips; confirm hook runtime, command/report contracts, PHP inputs, contributor Git state, and the stashed PR QA work were not modified, without claiming green regression coverage when failures remain.
- [x] 4.2 Audit proposal/design/spec/task parity and temporary/unversioned references, then run `openspec validate isolate-openspec-hook-fixtures --strict --no-interactive` and `openspec validate --all --strict --no-interactive --json`; verify all planning artifacts are self-contained and both validations succeed.
