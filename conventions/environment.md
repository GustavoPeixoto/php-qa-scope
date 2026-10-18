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

### Shared PHP And Composer Tooling

`docker/php/Dockerfile` defines the shared runtime as `base -> tooling -> development`.
The PHP image version is declared in `base`; Composer is provisioned once in
`tooling`. Both release-validation jobs build `tooling` directly. The PHP Compose
service and Dev Container retain the `development` target, which adds Xdebug,
development ini files, utilities, the configured user and workspace.

Build the CI target from the repository root without development arguments:

```sh
docker build --file docker/php/Dockerfile --target tooling --tag php-qa-scope-release-tooling .
```

The tooling build does not execute the development-only PIE/Xdebug installation
or require local `.env` files or a running Compose service. Release workflows
mount their exact checkout read-only at `/workspace` and execute Composer there;
Python and GitHub CLI remain on the runner. No API/App credentials are passed to
the image build or Composer container.

For release runtime smoke tests, also build the development image with the
workspace path used by the test process:

```sh
docker build --file docker/php/Dockerfile --target development --build-arg WORKSPACE_DIR="$PWD" --tag php-qa-scope-release-development .
```

The release tests compare actual PHP/Composer versions against the single
Dockerfile declarations and each other, check Xdebug isolation and development
workspace behavior, and run strict Composer fixtures through tooling. When Docker
runs on the host while the tests run inside `dev`, set
`RELEASE_TEST_HOST_WORKSPACE` to the host path of this checkout so temporary fixture
paths remain visible through the bind mount. Optional `RELEASE_TEST_TOOLING_IMAGE`
and `RELEASE_TEST_DEVELOPMENT_IMAGE` select already built images;
`RELEASE_TEST_COMPOSER` overrides the fixture command prefix if needed.

Docker builds require the referenced registries; cached parent layers reduce
subsequent builds. Centralized version declarations prevent independently maintained
PHP/Composer pins in CI and tests. Mutable upstream image tags and package
repositories still limit byte-for-byte reproducibility.

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

## AI Development Tools

Headroom installation, Codex routing, runtime configuration, and verification
belong in [conventions/headroom.md](headroom.md).

Context-mode usage, context preservation, and Codex hooks belong in
[conventions/context-mode.md](context-mode.md).

## Local Package QA

The package's QA tools are development dependencies. Install them with `composer install`, without `--no-dev`, before running local checks.

| Tool | Responsibility | Configuration | Commands |
| --- | --- | --- | --- |
| PHPCS / PHPCBF | Check / fix coding standard | `phpcs.xml` | `composer sniffer-check`, `composer sniffer-fix` |
| PHP-CS-Fixer | Check / apply formatting | `php-cs-fixer.dist.php` | `composer fixer-check`, `composer fixer-fix` |
| PHPStan | Static analysis | `phpstan.neon` | `composer stan-check` |
| PHPMD | Detect design and complexity issues | `phpmd.xml` | `composer md-check` |

`composer md-check` analyzes `src`, `tests`, and `bin`. PHPMD is not managed by `php-qa-scope`; its path selection is defined independently in the Composer script. For a custom selection, run it manually:

```sh
vendor/bin/phpmd bin text phpmd.xml
```

The PHP-CS-Fixer configuration uses `setRiskyAllowed(false)` and does not enable `declare_strict_types`. Rule selection and risky-rule policy belong to the Fixer configuration. `php-qa-scope` does not modify that policy.

## Repository Git Hooks

Repository Git hook installation, runtime requirements, pre-push validation, and
hook automation verification belong in [conventions/git-hooks.md](git-hooks.md).

## Convention Scope

This convention describes environment topology and usage. It should not document internal details of package behavior.

Repository topology and package distribution boundaries belong in `conventions/repository.md`. Public package commands, supported QA tools, and user-facing configuration semantics belong in `README.md` or in durable OpenSpec artifacts when a change needs planning. Contributor environment setup and ordinary local QA commands belong in this convention. Git hook installation, runtime, and verification belong in [conventions/git-hooks.md](git-hooks.md).
