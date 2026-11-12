## Context

See `proposal.md` for motivation. The Compose `codex` volume is mounted at `/home/dev/.codex` and survives rebuilding the development container. Its pre-transition configuration selected Headroom. During implementation, the user explicitly replaced the conversation/authentication preservation plan with a request to wipe this volume and recreate from scratch. No backup, metadata migration, or authentication restoration remains in scope. The active Codex session runs inside dev, so reset/recreation required a separate controller that survived that container stopping. Activation has since been accepted with the PHP container deviation recorded below.

## Goals / Non-Goals

**Goals:** Remove the runtime integration; recreate dev with an empty Codex volume; initialize context-mode and repository hooks through the maintained bootstrap.

**Non-Goals:** Preserving Codex conversations/login/preferences, a permanent migration service, changing package behavior, rewriting historical OpenSpec archives, or resetting GitHub CLI/PHP state.

## Decisions

- Remove the Headroom virtual environment, CLI symlink, exclusive pip/venv packages, helpers, startup hooks, dedicated tests, runtime variables, and current conventions. Keep Python 3, other tools, volume declarations, and service identities. Wait for `postCreateCommand` rather than the removed proxy startup.
- Keep a one-time reset/recreation controller and evidence under ignored `tmp/`. Do not install compatibility code in the development image.
- Resolve the running dev container from its Compose project/service labels and verify its immutable ID and `/home/dev/.codex` volume mount. Pin the intended Codex volume identity. Reject foreign consumers. Do not run `compose down`, prune volumes, or stop PHP.
- Build and validate the new development image before destruction. Prepare Dev Container recreation with the Docker feature and updated lifecycle metadata, preserving workspace path and the GitHub CLI volume. Use a controller with Docker access, a host-path workspace bind, and no mount of the real Codex or GitHub CLI volumes.
- Start the controller separately from dev and retain its logs/status in the ignored checkout. It stops/removes only the identified dev container, clears or recreates only its Codex volume after checking consumers, and starts the updated Dev Container. No old Codex data is restored. Context-mode setup and Git hook bootstrap run through the updated Dev Container lifecycle.
- Dispatch reset only after image/runtime/specification checks succeed. Inform the user before the session disconnects. Record dispatch separately from observed completion; never claim reset/bootstrap succeeded without controller evidence.
- Accept the observed PHP container identity/start-time change as an explicit user-approved exception to the original preservation constraint. Preserve the controller's failed status and distinguish successful reset/bootstrap verification from its failed PHP guard. The user suggested a prior Compose run as a possible explanation, but the cause is not established. Do not repeat the reset or remove containers to resolve this record.

## Risks / Trade-offs

- Reset permanently discards conversations and login: the user explicitly requested starting from scratch; require fresh login after reconnection.
- Stopping dev interrupts this session: detached orchestration survives independently and writes retained progress/status evidence.
- Incorrect volume or foreign consumers: verify exact project/service/container/mount identities and reject extra users before reset.
- Recreation or network failure: retain phase-specific logs, leave other services/volumes untouched, and provide the normal Dev Container reopen path.
- Fresh hook trust: review/trust hooks in Codex if prompted; do not preapprove on the user's behalf.

## Migration Plan

1. Implement removal, build Node tooling/development images, and run runtime, automation, and OpenSpec validation.
2. Prepare and validate the detached reset procedure and Dev Container build using host workspace paths. Test destructive volume handling on an isolated disposable volume before targeting real Codex state.
3. Notify the user and dispatch the independent controller. Verify its identity and start acknowledgement before the session ends. Stop only the pinned dev container, reset only the pinned Codex volume, then recreate dev with the updated configuration and run bootstrap.
4. After reconnection, verify Headroom is absent, the Codex home contains fresh bootstrap configuration with no old authentication/sessions, and context-mode/hooks are available. Authenticate Codex again as needed. Preserve controller logs until acceptance.

## Verification

Permanent runtime tests use fresh isolated state and verify context-mode bootstrap without network access, idempotence, credential-file preservation during ordinary bootstrap, context-mode MCP configuration, and hook generation. Headroom absence was verified during the removal transition; its executable, directory, provider, and MCP absence assertions and the transition-specific OpenAI provider/base URL assertions are not retained as permanent regression coverage. The development-without-Headroom scenario remains required, and actual recreated-environment acceptance verifies absence. A separate reset smoke proves only the selected disposable volume is cleared and unrelated state survives. Image builds, PR QA/Git hook automation, strict OpenSpec validation, and a final diff/reference audit precede dispatch. Actual reset and recreation acceptance is recorded separately below, including the accepted PHP deviation.

### Implementation validation

Node tooling, development, and complete Dev Container feature images built successfully. All four runtime tests passed; PR QA automation ran 22 tests successfully with six opt-in skips. The full Git hook suite ran 66 tests with one skip and one failure in `test_sigint_sigterm_every_phase_actual_npm_frontend`, at the `containers-tool-directory-atomic` SIGTERM subcase: the fake Docker fixture attempted to read an already removed record. That exact phase passed when rerun alone for both SIGINT and SIGTERM. No hook implementation was modified, and the full suite is not reported as passing. Strict validation passed for the change and all seven main specifications. The disposable-volume reset isolation/consumer guard smoke and the pinned real-target preflight passed.

After removing the transition-specific assertions, PR QA discovery passed with 16 executed tests and six opt-in skips. The separately enabled runtime suite passed all four tests against the existing QA images, including the renamed context-mode bootstrap test. Strict change validation and the diff whitespace check passed. That test follow-up did not reset volumes or recreate the active Dev Container; activation acceptance was still pending at that point.

### Activation acceptance

- The retained controller log records `armed`, `stopping-dev`, `codex-volume-cleared`, then `failed`. Dev Container recreation reported success for container `0e7b511751db`. The controller's checked fresh-state probe runs before the PHP guard that produced the retained error `PHP was unexpectedly recreated or restarted`. Reaching that guard establishes that the probe passed: no authentication, session/archive directories, or state databases remained, Headroom was absent, context-mode was configured, and the repository pre-push hook was executable. This is evidence from controller control flow, not a separately retained successful probe output or an overall successful controller run.
- The original failed status is timestamped `2026-11-12T00:08:29Z` (UTC). It and the original controller/recreation logs remain unchanged under ignored `tmp/remove-headroom/`; these paths are provenance, while the material results are recorded here. The user explicitly accepted the PHP container change. Its cause remains uncertain; no attribution to a specific Compose command is made.
- A subsequent dev container, `833ef1846c20`, was created at `2026-11-12T00:15:23Z` (UTC). Read-only checks confirmed the original `php-qa-scope_codex` and `php-qa-scope_github-cli` volume identities; no Headroom executable, helpers, dedicated directory, provider/MCP entries, or lifecycle metadata; availability of maintained tools and bootstrap helpers; configured context-mode MCP/hooks; and an executable repository pre-push hook.
- Current authentication-file modification time and session-file modification times are later than the reset. They corroborate subsequent use, rather than independently proving historical cleanup; the controller probe provides the initial clean-state evidence. Current login and conversations are preserved. Fresh login and any prompted manual hook review are user actions after recreation; no hook trust approval is inferred.
- The current PHP container, `2ea5da96ba4f`, was created during the recreation window and responds with PHP `8.5.10` and Composer `2.10.3`. These availability checks do not claim full package QA or identify why its container changed.
- Activation acceptance uses the completed reset/bootstrap evidence, current environment checks, and the user-approved PHP exception. This reconciliation performs no reset, container removal, or service recreation. Existing runtime/automation results are reused because only change records are being updated. Specification sync and archive remain the next lifecycle step.
