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

This convention is based on the context-mode routing rules for Codex at <https://github.com/mksglu/context-mode/blob/main/configs/codex/AGENTS.md>, but it is not a literal copy of upstream. When updating context-mode, compare against that file and incorporate only rules compatible with this repository.

## Context Resumption

When resuming a session, continuing after compaction, or needing to remember previous decisions, search the context-mode knowledge base before asking the user again.

Use `ctx_search` with `sort: "timeline"` to retrieve captured decisions, plans, blockers, errors, rejected approaches, and compaction guides.

After `/clear` or `/compact`, treat the context-mode knowledge base as preserved. Use `ctx purge` only when the user explicitly asks to clear the base.

## Collection And Analysis

Use `ctx_batch_execute` when you need to run multiple related investigation commands. Give commands descriptive labels and include the necessary queries in the same round trip when possible.

Use `ctx_execute` or `ctx_execute_file` when the task is to process data or files and the raw content does not need to enter the conversation. The code should print only the necessary answer.

Use regular text search, such as `rg`, when the expected output is small and directly observable. If the output grows or requires summarization, route it through context-mode.

## Network And External Content

Avoid `curl`, `wget`, and inline fetches that bring large responses directly into context. For external pages, APIs, or documents, prefer search, indexing, or processing tools that return only relevant excerpts or verifiable summaries.

When the answer depends on a recent or unstable external source, verify the information with an appropriate source and record the links used in the response.

## Maintenance Commands

When the user asks for:

- `ctx stats`: call the context-mode statistics tool and show the output;
- `ctx doctor`: call the context-mode diagnostic and present the checklist;
- `ctx upgrade`: call the upgrade tool, run the returned command, and advise restarting the session;
- `ctx purge`: confirm the scope before clearing because the action is destructive.

## Operational Configuration

The operational context-mode configuration for Codex in this project lives in the `dev` environment:

- `docker/dev/.codex/config.toml` declares hooks and the MCP server;
- `docker/dev/.codex/hooks.json` declares Codex hooks;
- `docker/dev/bin/setup-codex-context-mode` merges the configuration into `~/.codex`;
- `.devcontainer/dev/devcontainer.json` runs setup in `postCreateCommand`;
- the `codex` Docker volume stores Codex configuration and trust state across container rebuilds.

## Manual Hook Review

The first time a new `codex` volume is created, Codex still requires a manual hook review before running configured hooks.

To review hooks from inside the `dev` container:

```sh
codex -C "$PWD" --no-alt-screen
```

Open the Hooks screen, review the hooks loaded from `~/.codex/hooks.json`, and trust them. Repeat this only when the `codex` volume is recreated or when `docker/dev/.codex/hooks.json` changes.

Do not duplicate this configuration in `AGENTS.md`. Use `AGENTS.md` as the operational index and this convention as the durable source for usage rules.

### Verifying The Installation

In the `dev` container terminal, the installed command is `context-mode`:

```sh
command -v context-mode
context-mode doctor
```

The diagnostic should report success for the server, FTS5/SQLite, MCP configuration, and Codex hooks. Performance warnings, such as the recommendation to install Bun, do not block usage.

Inside a Codex conversation, ask for the diagnostic or statistics by text:

```text
ctx doctor
ctx stats
```

In that case, `ctx doctor` and `ctx stats` are conversational commands that make Codex call the context-mode MCP tools. They do not need to exist as shell commands.

If `ctx doctor` in the terminal returns `ctx: command not found`, use `context-mode doctor`. If `context-mode` does not exist in the terminal, rebuild the Dev Container or run the `postCreateCommand` again. If the hooks appear inactive, review them with:

```sh
codex -C "$PWD" --no-alt-screen
```
