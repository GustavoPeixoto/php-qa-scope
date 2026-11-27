## Why

The development environment routes Codex through Headroom and starts its proxy automatically. Remove that integration completely and initialize Codex from an empty volume, as explicitly requested by the user during implementation.

## What Changes

- Remove Headroom installation, exclusive dependencies, bootstrap/startup helpers, environment options, dedicated tests, and current documentation.
- Keep Codex, context-mode, OpenSpec, Lefthook, GitHub CLI, and the existing Compose service and volume identities.
- Prepare a one-time detached reset/recreation procedure that survives stopping the current development container.
- Clear the identified Codex volume without restoring conversations, authentication, or configuration. Regenerate context-mode configuration through the remaining bootstrap.
- Validate the replacement image and reset procedure before dispatching the operation that ends the active session.

## Capabilities

### New Capabilities

None. The backup/reset procedure is a one-time transition, not a supported package feature.

### Modified Capabilities

- `repository-pr-qa`: Development compatibility retains the maintained assistant tooling and bootstrap without Headroom; absence is verified during the removal transition and recreated-environment acceptance, while permanent runtime probes cover maintained tooling and bootstrap behavior.

## Impact

Changes affect the development Docker image, Dev Container lifecycle, runtime tests, environment examples, and operational conventions. No PHP package API or consumer configuration changes. Historical OpenSpec archives remain intact.

The user explicitly replaced the earlier selective-backup plan with a request to wipe the volume and start from scratch. The reset discards conversations, authentication, preferences, caches, plugins/skills, and context-mode state. The GitHub CLI volume remains outside the reset scope. The intended transition also preserved the PHP container; its identity changed during the recreation window, and the user accepted that deviation after inspection confirmed that PHP and Composer respond normally. The cause remains uncertain. The temporary procedure and execution evidence remain under ignored `tmp/`; the durable design contains the complete transition contract and observed acceptance results.

Activation was accepted after reconnection: the controller cleared the pinned Codex volume, recreated dev, and passed its initial fresh-state verification before failing the PHP identity/start-time guard. That original failure record is preserved. The current dev was subsequently verified without Headroom and with context-mode and repository hooks configured. Current authentication and session state are post-reset usage and are preserved. No repeat reset or container removal is required for completion.

Consulted sources: `AGENTS.md`, the workflow, environment, repository, artifacts, context-mode, Git, and Git hook conventions; development bootstrap and runtime tests; current Codex session/state storage.

## Open Questions

No unresolved design decisions. The PHP container deviation is explicitly accepted, with its cause unconfirmed. Fresh authentication was required after reset; subsequent login and any prompted manual hook review belong to normal use of the recreated environment. Hook trust is not approved on the user's behalf. No backup, conversation restoration, or further reset is requested.
