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

### GitHub CLI And Persistent Tool State

The development stage installs the distribution's `gh` package through its
existing APT transaction. GitHub CLI is available to `dev` in a newly built
development image; it is not installed by the shared Node/OpenSpec tooling stage.
The exact package version follows the configured distribution repositories.

`GH_CONFIG_DIR` points to `/home/dev/.config/gh` for the default dev user.
Compose mounts the project-scoped `github-cli` named volume there, normally
`${PROJECT_NAME}_github-cli`. Compose also mounts `codex` at `/home/dev/.codex`,
normally using `${PROJECT_NAME}_codex`. The Dev Container inherits both mounts
from the dev service; do not duplicate them in its configuration. PHP receives
neither state volume.

The Codex declaration reuses the existing project-scoped volume. For this
project, the existing active mount and the resolved Compose name are both
`php-qa-scope_codex`. Keep that project/volume identity when recreating the
container; changing the project name selects a different volume. Moving the
declaration does not copy or replace existing state. Codex binary availability
still follows the existing VS Code extension setup.

Image setup creates both directories with dev ownership so new volumes are
writable without root. The GitHub CLI directory is created with mode `0700`;
its retained volume preserves that mode. Dev Container post-create initialization
repairs ownership of both directories while preserving existing files, their
modes, and the Codex setup commands. It does not repeat chmod.

Rebuild/recreate the active dev environment only in a coordinated, separately
authorized step. After recreation, run browser authentication only with the
required account-operation authorization:

```sh
gh auth login --hostname github.com --web --git-protocol ssh
gh auth status --hostname github.com
gh api user --jq .login
```

When prompted about generating or uploading an SSH key, decline generation and
select `Skip` for upload; do not provision keys as part of this login. The
distribution CLI does not provide the newer `--skip-ssh-key` option. This keeps
the repository's SSH transport without running `gh auth setup-git`.
Initial login remains interactive and is never part of image construction or
container startup. Check the account and
stored configuration location without printing the token or the contents of
`hosts.yml`. In this development image, credentials are stored as local files
in the private configuration volume; the volume is not an encryption service.
Do not put credentials in Dockerfiles, build arguments, versioned files, local
environment files, reports, or logs.

Retaining the volume preserves login state across container recreation and
image rebuilds while the credential remains valid. Expiration, revocation,
explicit logout, or deleting the volume can require a new login. Do not delete
credential volumes automatically or use `docker compose down --volumes` as a
routine rebuild operation. Rollback can remove the package/mount declaration
while leaving the existing volume for its owner.

The opt-in runtime suite exercises separate disposable GitHub CLI and Codex
volumes across two containers, with network disabled and synthetic account data.
It verifies ownership/non-root writing for both directories, private GH modes,
CLI configuration readback, and unchanged account-file digests for both tools,
then removes only its own test resources. It never mounts real state into a
probe. This proves persistence mechanics, not successful account authentication.

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
`tooling`, together with `unzip` for Composer distribution extraction. Release
validation and PR QA build `tooling` directly. The PHP Compose
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

## Shared Node And OpenSpec Tooling

`docker/dev/Dockerfile` defines `tooling -> development`. The official
`node:26.13.1-bookworm` base pins the complete Node.js version while retaining
Debian Bookworm. This pins the runtime version, not an immutable image digest.
Corepack 0.36.0, Yarn Classic 1.22.22, and OpenSpec 1.14.0 are installed in
`tooling`, with build-time version checks. Both stages use the same Node runtime;
runtime probes require an exact match with the version declared in `FROM`.
The development stage explicitly installs `sudo` and renames the base image's
`node` user to `dev`. NVM, Zsh, Oh My Zsh, and global ESLint from the former
Microsoft Dev Containers base are not provisioned.
`development` remains the final default target used by Compose and adds the
workspace/user setup, OS utilities, Lefthook, context-mode, helper
scripts, and root/user OpenSpec workflow configuration. CI does not run that
bootstrap or require workspace arguments, environment files, or Compose:

```sh
docker build --file docker/dev/Dockerfile --target tooling --tag php-qa-scope-pr-node-tooling .
docker run --rm php-qa-scope-pr-node-tooling openspec --version
docker build --file docker/dev/Dockerfile --build-arg WORKSPACE_DIR="$PWD" --tag php-qa-scope-pr-node-development .
docker build --file docker/php/Dockerfile --target tooling --tag php-qa-scope-pr-php-tooling .
docker build --file docker/php/Dockerfile --target development --build-arg WORKSPACE_DIR="$PWD" --tag php-qa-scope-pr-php-development .
PR_QA_RUNTIME_TESTS=1 PYTHONPATH=tools python3 -B -m unittest pr_qa.test_runtime -v
```

The focused runtime tests compare actual Node/OpenSpec and PHP/Composer versions
and verify development behavior. Runtime probes inspect the completed container
and collect its retained logs before removal, so a short command's lost attached
stdout cannot invalidate version evidence. PR QA installs locked development dependencies
with `composer install --no-interaction --no-ansi --prefer-dist --no-progress`.
It mounts the writable disposable checkout at the same absolute container path,
uses the runner UID/GID and a temporary writable home, and passes no Docker socket
or runner credentials to the tooling containers. Version declarations stay in
the Dockerfiles; mutable image tags and upstream registries still limit exact
reproducibility.

For native adapter acceptance, run from a host checkout with Docker available,
or from a runner exposing the checkout at its identical absolute host path:

```sh
PR_QA_NATIVE_TESTS=1 PYTHONPATH=tools python3 -B -m unittest pr_qa.test_native -v
```

This opt-in smoke exports committed HEAD blobs into a retained `tmp/` fixture,
references the original Git metadata read-only, installs locked dependencies,
runs all seven checks, validates their individual reports/outcomes, checks native
findings and catchable cancellation, and verifies tracked content and the lock
remain unchanged.
It neither creates commits/branches nor uses the contributor's index for writes.
The current working adapter is exercised against the exported package revision;
GitHub execution against the implementation's merge revision is verified during
rollout. Evidence is retained in the reported temporary fixture paths.

### Pull Request Preparation Caches

PR QA keeps its seven matrix entries independent. SHA-pinned official Buildx and
GitHub cache restore/save actions persist optional preparation caches in GitHub
Actions, using the platform's native branch/PR visibility and eviction policy.
Each runner restores its own copy; parallel checks do not share a live directory.
A first cold run may repeat the same setup in several jobs.

Docker uses BuildKit's local layer importer/exporter, with separate PHP and
Node/OpenSpec cache keys containing a format version, runner OS/architecture,
tooling family, and Dockerfile hash. Package-source edits do not invalidate these
keys. Each job still builds the tooling target and loads `pr-qa-tooling` into its
local Docker daemon. It exports layers into a fresh temporary directory and
replaces the previous export only after successful construction, retaining its
shell build log. No image is published to a registry. Mutable upstream references
retain their existing reproducibility limitation.

Only PHP entries restore Composer package downloads. Their keys include a format
version, runner OS/architecture, PHP Dockerfile hash, and both Composer manifest
and lock hashes, with fallback to earlier downloads for the same runtime. A
writable bind mount supplies `COMPOSER_CACHE_DIR`; `COMPOSER_HOME` remains
temporary. Every PHP job still runs its complete locked development install with
the current platform checks. Installed `vendor/`, credentials, reports, and QA
outcomes are never cached.

Restore/save failures are warning-only. Missing or expired caches follow the
normal build/download path; actual build, install, check, and required report
upload failures remain fatal. Successfully prepared caches are offered for
publication before native QA, skipping exact immutable-key hits. Concurrent
publishers use first-publication behavior. Record observed GitHub cold/warm
restoration and timings separately from local layer/download verification; local
success alone does not prove GitHub cache reuse or a speedup.

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
