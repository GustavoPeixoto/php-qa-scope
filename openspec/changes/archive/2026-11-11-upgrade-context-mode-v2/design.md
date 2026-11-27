# Design

## Context

See proposal.md for motivation and scope. The development image already pins context-mode 2.1.8 and supplies Codex through the VS Code extension launcher. Post-create repairs ownership and installs Git hooks; post-attach waits for the extension before setup. Real activation of that lifecycle was confirmed before this simplification.

## Decisions

- Keep a small Python standard-library adapter, targeting roughly 70–100 readable lines without a line-count test. Preserve `--wait-for-codex SECONDS` and manual fail-fast behavior; remove `--reset` with no replacement tool.
- Readiness probes `codex --version`, retrying only a missing executable or launcher exit 127 every two seconds. Use a monotonic total deadline and cap each probe at five seconds or the remaining budget. Actual executable errors and probe timeouts fail immediately with diagnostics. Validate positive integer durations and reject unknown arguments before probing.
- After readiness succeeds, call `os.execvp` for `context-mode setup --yes --agents codex`. Inherit the environment, including `CODEX_HOME`, without rewriting it. This forwards exit status and signals and lets upstream own provisioning.
- Remove local TOML/JSON edits, hook ownership detection, trust-index remapping, deletion validation, snapshots, rollback and per-home locks. Upstream 2.1.8 already records backups, rolls back failed setup and holds an exclusive setup lock in its data root. Competing setup returns the upstream lock diagnostic; the adapter does not wait or retry that error.
- File handling, permission behavior and recovery follow the pinned package rather than a second local contract. The adapter does not mutate configuration, skills or data itself. Normal repeated setup must retain history and unrelated state, as verified against the real package.
- Keep `postCreateCommand`, `waitFor: postCreateCommand`, `postAttachCommand: setup-codex-context-mode --wait-for-codex 180`, the extension-only launcher and package version unchanged.

## Risks And Alternatives

- The extension arrives after post-create: retain bounded post-attach readiness instead of adding a second Codex installation.
- Removing local locking changes overlapping-call behavior: upstream may reject a competing setup instead of waiting for it. Propagate its error; reconnect or retry after the running setup finishes.
- Upstream owns recovery and permissions: do not promise the deleted wrapper's additional preservation rules or reimplement them in tests.
- Legacy cleanup is no longer a permanent bootstrap feature: the one-time cleanup has already occurred; any future destructive cleanup needs separate scope.
- Moving the reset into another script would retain its maintenance burden. The user chose complete removal.

## Validation Plan

Focused adapter tests cover missing/delayed Codex, launcher 127, deadline/sleep/probe caps, actual errors and probe timeout, manual fail-fast behavior, invalid durations, unsupported arguments including `--reset`, exact delegation, inherited environment and propagated exit status/signals.

Real-package probes use the existing launcher, a copied real Codex executable, synthetic account state and network-disabled disposable containers. Retain the cold post-create/delayed-extension/reconnection probe. Test fresh and already-configured v2 homes for repeated setup, unchanged history and unrelated configuration/hooks/trust/credentials, clean doctor, exact CLI/package version, SQLite FTS5, all nine MCP tools, tool calls and four actual handlers including large-read denial. Do not test removed reset or local recovery machinery.

Build the development image, run focused and runtime-enabled Python checks, validate this change strictly and inspect the final diff. Do not recreate the active container for this work.

## Prior Activation Evidence

The earlier upgrade work established the 2.1.8 pin, performed the authorized one-time clean installation and corrected extension-dependent initialization. The superseded wrapper's final suite had 43 cases: 41 passed and 2 opt-in native-adapter tests skipped. That result is historical, not validation of the simplified adapter.

After the user performed the coordinated real rebuild, CLI and MCP both reported context-mode 2.1.8 with Node 26.13.1 and Codex 0.167.0-alpha.4.1. Terminal doctor and all MCP doctor checks passed, including old entries, hook round trip, double-fire, MCP, database and shell. The nine v2 tools were available in a fresh session; its database recorded prompt and Bash/tool events. Docker inspection confirmed the original `php-qa-scope_codex` volume and the intended lifecycle commands.

Lifecycle markers showed post-create before extension installation. Remote-agent logs confirmed automatic installation of `openai.chatgpt`; the user confirmed that post-attach setup completed without repair commands or manual installation. This completes the former activation tasks 4.2 and 5.4. It proves the already-active lifecycle, independently of the new adapter's disposable validation.

No active-container recreation, reset, data deletion, commit, push or archive is authorized by the simplification.

## Simplification Validation Evidence

- The helper is now 67 lines instead of 369. It retains argument parsing and bounded readiness, then uses `os.execvp` for official setup. Reset, configuration editing, local snapshots/rollback, deletion validation and locking are absent.
- `PYTHONPATH=tools python3 -B -m unittest pr_qa.test_context_mode -v`: all 10 focused adapter tests passed, including inherited environment, unsupported arguments, readiness limits and propagated process status/signals.
- Built the final development image successfully with `docker build --file docker/dev/Dockerfile --target development --build-arg WORKSPACE_DIR=/php-qa-scope --tag php-qa-scope-pr-node-development .`. Its pinned CLI assertion passed; the package pin and Dev Container lifecycle were not changed by this simplification.
- `PR_QA_RUNTIME_TESTS=1 PYTHONPATH=tools python3 -B -m unittest discover -s tools/pr_qa -p 'test_*.py' -v`: 32 cases in 58.552 seconds, 30 passed and 2 opt-in native-adapter tests skipped because `PR_QA_NATIVE_TESTS` was not enabled. All four image runtime probes ran.
- The real-package probe passed for fresh and already-configured v2 homes: repeated setup, unchanged credentials/history and unrelated preferences/MCPs/hooks/trust/skills, clean doctor, enabled MCP, exact CLI/package release, SQLite FTS5, all nine MCP tools, tool calls and four actual hook handlers including large-read denial.
- The cold lifecycle probe retained the image's launcher, ran post-create without extensions, observed bounded post-attach waiting, delivered a real executable into a synthetic extension directory and verified successful setup/reconnection, clean doctor and preserved state. All probes used disposable containers, synthetic credentials and disabled network.
- Strict OpenSpec validation, whitespace/syntax checks and active-reference review passed. The remaining reset/recovery references describe rejected arguments, upstream responsibilities or historical work. Artifacts are self-sufficient and record the prior live acceptance separately.
- No active-container recreation or real configuration/history cleanup was performed. The new image/adapter was validated in disposable containers; the running environment was left unchanged. No commit, push, sync or archive was performed.

## Post-simplification Real Activation

- The user subsequently rebuilt the Dev Container. The installed `/usr/local/bin/setup-codex-context-mode` is 67 lines and byte-for-byte identical to the simplified repository helper.
- The real environment reports context-mode 2.1.8, Node 26.13.1 and Codex 0.167.0-alpha.4.1. `codex mcp list` shows context-mode enabled. Terminal doctor passes all Codex setup checks, including hook registration, execution and observation; every MCP doctor check passes, including old entries, hook round trip, double-fire, database and shell.
- Docker inspection confirms that the rebuilt container retains the existing `php-qa-scope_codex` volume at `/home/dev/.codex`. Validation performed no reset, configuration repair or data cleanup.
