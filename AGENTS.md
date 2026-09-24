# Project Operating Guide

This repository develops `php-qa-scope`, a Composer package for synchronizing managed PHP QA scope blocks across native tool configuration files.

## Repository Entrypoints

[README.md](README.md) is the human entrypoint at the repository root.

This [AGENTS.md](AGENTS.md) file is the operational entrypoint for agents and collaborators. It indexes project conventions and points to the canonical sources to consult.

The repository root is also the Composer package root for `gustavo-peixoto/php-qa-scope`.

## Conventions

Conventions are durable documents in `conventions/` that define cross-cutting project rules. Each convention declares in its `when` front matter when it should be read.

| Convention | Scope |
| --- | --- |
| [conventions/language.md](conventions/language.md) | Default language for conversation, project context, and artifacts. |
| [conventions/repository.md](conventions/repository.md) | Repository topology, entrypoints, package root layout, public package distribution, and documentation boundaries. |
| [conventions/phpdoc.md](conventions/phpdoc.md) | PHPDoc requirements for class-like declarations, methods, functions, parameters, returns, templates, and closure signatures. |
| [conventions/workflow.md](conventions/workflow.md) | Exploration, planning, proposals, and applying changes. |
| [conventions/git.md](conventions/git.md) | Versioned state, diffs, branches, commits, pushes, and change review. |
| [conventions/environment.md](conventions/environment.md) | Environments, local infrastructure, Docker, Compose, Dev Containers, `dev`, and PHP package tooling. |
| [conventions/artifacts.md](conventions/artifacts.md) | Durable and transient artifacts, inputs, handoffs, drafts, `tmp/`, and sources of truth. |
| [conventions/context-mode.md](conventions/context-mode.md) | Using context-mode, `ctx_*` tools, Codex hooks, and preserving the context window. |
