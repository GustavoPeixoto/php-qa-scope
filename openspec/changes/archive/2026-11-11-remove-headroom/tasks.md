## 1. Context and transition preparation

- [x] 1.1 Read applicable conventions and current bootstrap, runtime tests, and Codex storage; verify the design and proposal are self-contained and match the approved plan.
- [x] 1.2 Prepare the ignored detached reset/recreation procedure and instructions; verify exact container/volume targeting and test reset isolation using disposable volumes. The user replaced the backup/restore plan with a full reset during implementation.

## 2. Remove the runtime integration

- [x] 2.1 Remove Headroom installation, exclusive pip/venv dependencies, helpers, dedicated tests, Dev Container lifecycle commands, and example/local environment variables; verify Python and remaining bootstrap commands are retained and startup no longer waits for the proxy.
- [x] 2.2 Verify Headroom absence during the removal transition and context-mode bootstrap idempotence on isolated state; verify the updated development image with the runtime suite. Retain the removal results as transition evidence rather than permanent Headroom-specific assertions.
- [x] 2.3 Remove the Headroom convention and references from current operational documentation and AGENTS.md; verify only historical/change records mention Headroom after removing the transition-specific negative tests.

## 3. Integration verification

- [x] 3.1 Build shared Node tooling/development images and run applicable PR QA and Git hook automation tests; retain evidence and report any failures without resetting the active volume.
- [x] 3.2 Validate the OpenSpec change and all specifications in strict mode, inspect the diff, and audit artifact parity and transient references; verify no PHP package interface, archive, or unrelated volume declarations changed.
- [x] 3.3 Remove transition-specific Headroom and OpenAI provider/base URL assertions from runtime tests, rename the context-mode bootstrap test, and retain offline execution, idempotence, authentication preservation, MCP configuration, and hook generation coverage; run PR QA automation, the opt-in runtime suite, strict change validation, and review the diff.

## 4. Activation after the active Codex session ends

Activation is accepted using the retained reset/recreation evidence, the controller's checked fresh-state probe before its failed PHP guard, and read-only verification of the current dev and PHP containers. The user explicitly accepted the PHP identity/start-time deviation; its cause remains uncertain. The original controller status remains `failed` and is not relabeled as success. See `design.md` for the self-contained acceptance results; ignored `tmp/remove-headroom/` holds the original evidence as provenance. No reset or container removal is repeated.

- [x] 4.1 Dispatch the detached controller to stop the identified dev container, reset only its Codex volume without backup/restore, and recreate dev; reconcile actual completion from controller evidence after disconnection, preserving the failed PHP guard and recording the user-accepted PHP container deviation.
- [x] 4.2 Verify the recreated Dev Container's initial fresh Codex state without old conversations/login, and confirm the current dev has no Headroom and has configured context-mode/hooks bootstrap; record fresh login and any prompted manual hook review as post-recreation user actions, preserving subsequent authentication and sessions.
