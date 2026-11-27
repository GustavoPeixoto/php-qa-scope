---
id: context-mode
title: Context-Mode Convention
when: Whenever using context-mode, `ctx_*` tools, Codex hooks, resuming after compaction, or investigating potentially large outputs.
---

# Context-Mode Convention

## General Rule

Use context-mode to preserve the context window during AI-assisted development.

When the intent is to analyze, filter, count, compare, summarize, search, transform, or aggregate data, prefer running the analysis in a `ctx_*` tool and returning only the derived result. Avoid dumping long outputs, raw HTML, long logs, dumps, or large files directly into the conversation.

The regular shell remains appropriate for short commands, state mutations, local validations, servers, installations, Git, and reads made specifically to edit a file section.

## Relationship With Upstream

The development image pins context-mode 2.1.8. Its [updating guide](https://github.com/mksglu/context-mode/blob/v2.1.8/docs/install/README.md#updating), [Codex setup guide](https://github.com/mksglu/context-mode/blob/v2.1.8/docs/install/codex.md), and [tool prompts](https://github.com/mksglu/context-mode/tree/v2.1.8/src/prompt/tools) describe the upstream behavior. When updating the package, compare against the target release and incorporate rules compatible with this repository. The old `configs/codex/AGENTS.md` routing file is absent from v2.

The target is a stable release, not an upstream LTS designation. Package versions belong in the development Dockerfile; updates must keep its exact version pin and build-time CLI assertion coherent.

## Context Resumption

When resuming a session or continuing after compaction, call `ctx_resume({})` before repeating work. It returns the current task, changed files, open errors, and search terms. Follow a returned pointer with `ctx_resume({seq: N})` when needed.

Use `ctx_search` with `queries` and `sort: "timeline"` to retrieve captured decisions and other session history before asking the user again. The default search scope is the current worktree; `scope: "session"` and `scope: "project"` narrow or expand it. Timeline pagination uses `after`.

After `/clear` or `/compact`, treat the context-mode knowledge base as preserved. Use `ctx purge` only when the user explicitly asks to clear the base.

## Collection And Analysis

Use `ctx_batch` when you need to run multiple related investigation commands. Supply command strings and the necessary queries in the same round trip:

```text
ctx_batch({commands: ["git status --short", "git log --oneline -5"], queries: ["working tree changes", "recent commits"]})
```

Use `ctx_execute` when processing data or files. For a local file, pass `file`; the code receives its path through the `CTX_FILE` environment variable. Print only the necessary answer:

```text
ctx_execute({language: "python", file: "tmp/check.log", code: "import os; from pathlib import Path; print(sum('ERROR' in line for line in Path(os.environ['CTX_FILE']).read_text().splitlines()))"})
```

Use `intent` when output may be large so the full output can be indexed and relevant sections returned. v2 replaces the separate file-execution tool with this interface.

Use regular text search, such as `rg`, when the expected output is small and directly observable. If the output grows or requires summarization, route it through context-mode.

## Network And External Content

Avoid `curl`, `wget`, and inline fetches that bring large responses directly into context. Index an external page with `ctx_index({url: "https://example.com/docs", source: "upstream-docs"})`, then retrieve relevant passages with `ctx_search`. v2 handles URLs through `ctx_index`.

When the answer depends on a recent or unstable external source, verify the information with an appropriate source and record the links used in the response.

## Maintenance Commands

When the user asks for:

- `ctx stats`: call `ctx_stats` and show the output;
- `ctx doctor`: call `ctx_doctor` and present the diagnostic;
- `ctx upgrade`: explain the image version pin before changing the environment. The v2 `ctx_upgrade` tool performs the operation and returns a table; it does not return a shell command to execute. When an in-session upgrade is explicitly requested, show its table, run `ctx_doctor`, and report any required restart. A transient upgrade does not replace updating and validating the Dockerfile pin;
- `ctx purge`: confirm the scope before clearing because the action is destructive.

## Operational Configuration

The operational context-mode configuration for Codex in this project lives in the `dev` environment:

- `docker/dev/Dockerfile` installs the pinned global package;
- `docker/dev/bin/setup-codex-context-mode` waits for Codex and delegates to `context-mode setup --yes --agents codex`;
- the official setup generates MCP configuration, current hooks, skills, and own-hook trust in `~/.codex` or the selected `CODEX_HOME`;
- `.devcontainer/dev/devcontainer.json` prepares permissions/Git hooks in post-create and runs waiting setup in `postAttachCommand`;
- the `codex` Docker volume stores Codex configuration and trust state across container rebuilds.

## Official Setup, Readiness, And Hook Trust

`setup-codex-context-mode` is a small adapter. It checks for the extension's Codex
executable, then replaces its process with `context-mode setup --yes --agents codex`.
The official process inherits the environment, including `CODEX_HOME`, and its
exit status, signals and diagnostics reach the caller.

The package owns MCP configuration, hooks, skills, trust, backups, rollback and
setup locking. The adapter performs no configuration edits or data deletion and
keeps no local snapshots or locks. If another setup holds the upstream lock,
the official process can reject the competing run; wait for that setup to finish
and reconnect or retry. The readiness budget does not cover official setup.

The project provides no reset command. `--reset` and unknown arguments are rejected.
Future destructive cleanup must be a separately scoped maintenance operation.
Normal setup and reconnection preserve history and unrelated state according to
the pinned package's behavior; additional local file-mode or recovery guarantees
are not imposed on upstream.

Official setup registers trust only for its own hooks. Inspect hooks in the Codex
Hooks screen when troubleshooting:

```sh
codex -C "$PWD" --no-alt-screen
```

Setup needs the real Codex executable supplied by the VS Code extension; the image
keeps only its launcher, not a second CLI installation. Post-create prepares
permissions and Git hooks without Codex. `waitFor` remains `postCreateCommand`,
allowing the editor to connect while extensions are being installed. Post-attach
runs `setup-codex-context-mode --wait-for-codex 180` automatically on each connection.

Waiting accepts a positive integer duration. It retries only a missing executable
or launcher exit 127, every two seconds, with a monotonic deadline and each probe
limited to five seconds or the remaining budget. Actual errors and probe timeouts
fail immediately with diagnostics. On expiry, check extension installation and
reconnect or rerun the waiting command. Readiness itself never changes configuration
or history. Ordinary manual setup without the option remains fail-fast.

Disposable runtime probes use the real package, the image's extension launcher,
a copied Codex binary and synthetic account state with network disabled. Outside
dev, set `CONTEXT_MODE_TEST_CODEX_BINARY` for probes. Coverage includes fresh and
existing v2 installations and delayed extension delivery.

Validate rebuilt images in disposable containers before activation. Retain the
`php-qa-scope_codex` volume when recreating dev, following [environment.md](environment.md).
Restart Codex afterward: an existing session's MCP process retains its old tools.
A clean installation must pass doctor without isolating or ignoring legacy data.

Do not duplicate this configuration in `AGENTS.md`; this convention owns usage rules.

### Verifying The Installation

In the `dev` container terminal, the installed command is `context-mode`:

```sh
command -v context-mode
context-mode --version
context-mode doctor --agents codex
codex mcp list
```

The CLI must report 2.1.8. The diagnostic must confirm the server, SQLite, MCP configuration, and Codex hooks; the MCP listing must show context-mode enabled. An Auth value of `Unsupported` is expected for a server that needs no login. Investigate any failed configuration, trust, execution, or legacy-data check. In a fresh Codex session, verify the v2 tool inventory and actual hook behavior.

Inside a Codex conversation, ask for the diagnostic or statistics by text:

```text
ctx doctor
ctx stats
```

In that case, `ctx doctor` and `ctx stats` are conversational commands that make Codex call the context-mode MCP tools. They do not need to exist as shell commands.

If `ctx doctor` in the terminal returns `ctx: command not found`, use `context-mode doctor --agents codex`. If the package is missing or its version is old, build and activate the pinned image through the coordinated environment workflow; re-running setup alone does not install the package. To repair v2 configuration after the package is installed, run:

```sh
setup-codex-context-mode
context-mode doctor --agents codex
```
