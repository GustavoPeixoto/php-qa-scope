# Tasks

## 1. Scope and previous acceptance

- [x] 1.1 Reconcile proposal, design, requirements and tasks with the approved thin-adapter plan; record the previously confirmed real rebuild separately from new validation and pass strict OpenSpec validation.

## 2. Simplification

- [x] 2.1 Replace the helper with readiness plus official process delegation, removing reset and local configuration/recovery/locking code; verify focused tests for readiness, argument handling, inherited environment and exit/signal propagation.
- [x] 2.2 Adapt real-package probes to fresh and existing v2 state, retaining cold lifecycle, idempotence, state preservation, doctor, MCP and hook checks; verify the focused runtime probe against the rebuilt image.
- [x] 2.3 Update the context-mode convention for the reduced interface and upstream-owned recovery/concurrency; audit active references for removed reset and local-preservation guarantees.

## 3. Final validation

- [x] 3.1 Build the final development image, run the relevant runtime-enabled Python suite, record evidence and limitations, validate OpenSpec strictly, audit artifact self-sufficiency and inspect the final diff.
