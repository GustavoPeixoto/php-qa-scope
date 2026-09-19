---
id: repository
title: Repository Convention
when: Whenever you need to understand or change repository topology, entrypoints, package root layout, public package distribution, or root-level documentation.
---

# Repository Convention

## General Rule

The repository root is also the Composer package root for `gustavo-peixoto/php-qa-scope`.

Treat `README.md` as the public package entrypoint. It should primarily serve Packagist users and package consumers.

Treat `AGENTS.md` as the operational entrypoint for agents and collaborators. It should index canonical conventions rather than duplicate them.

## Repository Topology

The root contains both package files and repository support files:

- package metadata and public package documentation live at the root;
- Composer public executables live in `bin/` when implemented and declared in `composer.json`;
- package source and tests live in `src/` and `tests/`;
- package QA configuration lives at the root;
- `php-qa-scope.yml` is the source of truth for this package repository's own QA scope;
- `phpcs.xml`, `phpstan.neon`, and `php-cs-fixer.dist.php` contain native tool configuration plus managed scope blocks;
- `phpmd.xml` is a PHPMD ruleset; PHPMD is not managed by `php-qa-scope` yet;
- internal repository helper scripts live in `tools/`;
- PHP image, PHP ini files, and PHP service environment files live in `docker/php/`;
- repository-wide development tooling lives in `docker/dev/`;
- Dev Container entries live in `.devcontainer/dev/` and `.devcontainer/php/`;
- OpenSpec configuration and artifacts live in `openspec/`;
- durable cross-cutting conventions live in `conventions/`;
- ignored transient artifacts live in `tmp/`.

Do not recreate an `apps/` package workspace unless the repository intentionally becomes multi-package again.

## Distribution Boundary

Because the repository root is the package root, root-level versioned files may be visible in source installs.

Use `.gitattributes` `export-ignore` to keep Composer dist archives focused on package-relevant files. Do not rely on `export-ignore` to hide secrets or private material; such material must not be versioned.

Keep Composer public executables in `bin/`. Put internal repository automation in `tools/`.

## Documentation Boundaries

Package motivation, package behavior, user-facing installation, consumer commands, supported QA tools, configuration semantics, and public usage examples belong in `README.md` or durable OpenSpec artifacts when a change needs planning.

Contributor-only setup, local QA commands, internal implementation layout, and repository operation rules belong in conventions rather than in `README.md`.

Repository operation rules belong in conventions:

- environment and Dev Container usage belong in `conventions/environment.md`;
- OpenSpec workflow belongs in `conventions/workflow.md`;
- artifact durability and `tmp/` usage belong in `conventions/artifacts.md`;
- context-mode and Codex hook usage belong in `conventions/context-mode.md`.
