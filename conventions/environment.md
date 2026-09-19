---
id: environment
title: Environment Convention
when: Whenever you need to understand or change environments, local infrastructure, Docker, Compose, Dev Containers, the `dev` service, the `php` service, or AI-assisted development.
---

# Environment Convention

## General Rule

Use the `dev` service as the repository-wide environment for AI-assisted development, specification work, automation, documentation, and cross-cutting tasks.

Use the `php` service when the goal is to work directly with the Composer package tooling: Composer commands, PHP QA tools, package tests, Xdebug, and PHP-focused editor support.

## The `dev` Service

The `dev` service represents the cross-cutting development environment. It sees the whole repository and centralizes general development support tools such as OpenSpec, context tools, helper CLIs, automation, Git, Docker access, and useful libraries.

AI-assisted development should happen from the `dev` service by default. The agent needs a repository-wide view because a package change may affect package code, `docker-compose.yml`, Dev Containers, conventions, documentation, or OpenSpec artifacts.

Do not use the PHP-focused environment as the main context for AI-assisted development, except for an explicit and narrow task that only needs package-local tooling.

## The `php` Service

The `php` service is the focused workspace for Composer package tooling at the repository root.

Use it for:

- installing Composer dependencies;
- running package scripts;
- running PHP-CS-Fixer, PHPCS, PHPStan, PHPMD, and package tests;
- using PHP editor integrations and Xdebug.

The PHP service is a development and verification environment. This package does not define or maintain a PHP production runtime image.

## Environment Topology

The environment topology is intentionally small:

- PHP image, PHP ini files, and PHP service environment files live in `docker/php/`;
- repository-wide development tooling lives in `docker/dev/`;
- Dev Container entries live in `.devcontainer/dev/` and `.devcontainer/php/`;
- orchestration is declared in `docker-compose.yml`.

Both `dev` and `php` mount the repository root as the workspace. Operational services that support the whole workspace, such as `dev`, do not need a corresponding package directory.

## Environment Bootstrap

Use the Makefile helpers to create missing local environment files:

```sh
make env
make env-dev
make env-php
```

`make env` invokes `tools/env` for the `dev` and `php` services. The script creates missing `.env` files and leaves existing local files untouched.

After bootstrapping, open the repository in VS Code and choose one of the Dev Container entries under `.devcontainer/`.

From the repository root, Composer package commands may be run locally when PHP and Composer are installed:

```sh
composer install
composer validate --strict
```

With the PHP service running, run the same package commands through Compose:

```sh
docker compose exec php composer install
docker compose exec php composer validate --strict
```

## Local Package QA

The package's QA tools are development dependencies. Install them with `composer install`, without `--no-dev`, before running local checks.

| Tool | Responsibility | Configuration | Commands |
| --- | --- | --- | --- |
| PHPCS / PHPCBF | Check / fix coding standard | `phpcs.xml` | `composer sniffer-check`, `composer sniffer-fix` |
| PHP-CS-Fixer | Check / apply formatting | `php-cs-fixer.dist.php` | `composer fixer-check`, `composer fixer-fix` |
| PHPStan | Static analysis | `phpstan.neon` | `composer stan-check` |
| PHPMD | Detect design and complexity issues | `phpmd.xml` | Manual execution |

PHPMD remains outside `php-qa-scope`. Example manual execution, with an independent selection chosen by the developer:

```sh
vendor/bin/phpmd bin text phpmd.xml
```

The current PHP-CS-Fixer configuration enables `declare_strict_types`, but uses `setRiskyAllowed(false)`. Fixer rejects that combination. To explicitly allow that rule for one check, use:

```sh
composer fixer-check -- --allow-risky=yes
```

The permanent decision to enable risky rules or remove that rule belongs to the Fixer configuration. `php-qa-scope` does not modify that policy.

## Convention Scope

This convention describes environment topology and usage. It should not document internal details of package behavior.

Repository topology and package distribution boundaries belong in `conventions/repository.md`. Public package commands, supported QA tools, and user-facing configuration semantics belong in `README.md` or in durable OpenSpec artifacts when a change needs planning. Contributor-only setup and local QA commands belong in this convention. Implementation-specific test runners should be documented together with the implementation that introduces them.
