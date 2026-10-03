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

## Headroom In The Dev Container

The `dev` image installs `headroom-ai[proxy]==0.39.1` in `/opt/headroom` and
exposes the CLI as `/usr/local/bin/headroom`. The proxy extra also includes the
MCP runtime. Python dependencies remain isolated from the system interpreter.

Rebuild the `dev` Dev Container after changing the image. Its lifecycle then:

1. Runs `setup-codex-context-mode` followed by `setup-codex-headroom` in
   `postCreateCommand`.
2. Runs `start-headroom-proxy` in `postStartCommand`, including on subsequent
   container starts.
3. Waits for proxy readiness before attaching the editor (`waitFor` is
   `postStartCommand`).

The setup helper merges the Headroom provider and MCP server into
`~/.codex/config.toml`, preserving other settings and the context-mode hooks.
It targets the Codex VS Code extension's ChatGPT login, using the Responses API
and WebSocket transport. Sign in through Codex normally on a fresh volume; the
helper does not create or copy credentials. The configuration applies to Codex
clients sharing this `CODEX_HOME`, including the terminal CLI.

The original configuration is saved once as `config.toml.before-headroom` in the
same directory. Setup also uses Headroom's provider reassociation routine for
existing conversation metadata so the history remains visible with the
`headroom` provider. This routine is best-effort; verify history and conversation
resumption after enabling or disabling routing.

The proxy listens on `127.0.0.1:8787` inside `dev`. Its runtime options are
documented in `docker/dev/.env.example` and loaded by Compose from
`docker/dev/.env`:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `HEADROOM_SAVINGS_PROFILE` | `coding` | Compression profile. |
| `HEADROOM_MODE` | `cache` | Proxy mode; use `token` to prioritize token removal. |
| `HEADROOM_BEACON` | `off` | Anonymous upstream upload beacon for the proxy and MCP. |
| `HEADROOM_STARTUP_TIMEOUT` | `120` | Maximum startup wait, in seconds. |

The helpers use these defaults when a variable is absent or empty. Image defaults
for the profile and beacon remain overridable by Compose. `HEADROOM_MODE` is
passed explicitly to the CLI and takes precedence over the selected profile's
mode. The setup helper copies the chosen beacon value into the MCP environment.
The loopback host and port remain fixed integration choices. `HEADROOM_PYTHON`
remains an internal interpreter override rather than an advertised runtime option.

The environment bootstrap leaves existing `.env` files untouched; add desired
overrides there manually. Recreate/rebuild the Dev Container to load changes and
refresh the persisted MCP configuration. An already running proxy keeps its
startup options; running `start-headroom-proxy` again reuses it.

Compression is automatic for eligible traffic routed
through it, while the MCP supports compression, retrieval, and statistics.
The context-mode MCP and hooks remain active. No host port forwarding is needed
for the extension running inside the Dev Container.

The anonymous upstream upload beacon is disabled by default (`HEADROOM_BEACON=off`).
Proxy logs, its PID, and startup lock live in `~/.codex/headroom/`, within the
persistent `codex` volume. Startup is serialized, checks `/readyz`, and avoids
duplicate listeners. `HEADROOM_STARTUP_TIMEOUT` can increase the default
120-second startup limit. A failed startup stops editor attachment; inspect
`~/.codex/headroom/proxy.log` before retrying.

Verify the installation and runtime inside `dev`:

```sh
headroom --version
codex mcp list
curl --fail http://127.0.0.1:8787/readyz
curl --fail http://127.0.0.1:8787/stats
```

For an end-to-end check, use the extension with your existing ChatGPT login,
verify a streamed response, resume an existing conversation, and exercise MCP
compression and retrieval. Compare equivalent tasks with direct routing for
token usage, latency, and answer quality; installation alone does not establish
those results.

Run the isolated setup, rollback, proxy compression, startup, and MCP integration
checks from the repository root in a disposable Compose container. This avoids
the proxy already running in the normal Dev Container:

```sh
docker compose run --rm --no-deps dev /opt/headroom/bin/python docker/dev/tests/test_headroom.py
```

To return to direct Codex routing:

```sh
setup-codex-headroom --disable
```

Reload the Codex extension afterwards. The helper restores only the previous
provider selection, base URL, and Headroom provider/MCP entries, preserving other
configuration changes made since setup. It reassociates conversation metadata
back to the previous provider and removes the saved configuration after a
successful restore. It leaves the local proxy running; stopping it does not
disable routing. Container shutdown stops the process. A subsequent
`postCreateCommand` enables the integration again; `postStartCommand` only starts
the proxy. To re-enable without rebuilding, run `setup-codex-headroom` followed
by `start-headroom-proxy`, then reload Codex.

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
