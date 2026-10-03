---
id: headroom
title: Headroom Convention
when: Whenever using, configuring, verifying, or troubleshooting Headroom, its local proxy, its MCP server, or Codex routing through Headroom.
---

# Headroom Convention

## Installation And Dev Container Lifecycle

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

## Codex Integration

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

## Runtime Configuration

The proxy listens on `127.0.0.1:8787` inside `dev`. Its runtime options are
documented in `docker/dev/.env.example` and loaded by Compose from
`docker/dev/.env`:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `HEADROOM_SAVINGS_PROFILE` | `coding` | Compression profile. |
| `HEADROOM_MODE` | `cache` | Proxy mode; use `token` to prioritize token removal. |
| `HEADROOM_BEACON` | `off` | Anonymous upstream upload beacon for the proxy and MCP. |
| `HEADROOM_STARTUP_TIMEOUT` | `120` | Maximum startup wait, in seconds. |

The helpers use these defaults when a variable is absent or empty. Compose loads
runtime overrides from `docker/dev/.env`. `HEADROOM_MODE` is
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

## Verifying The Installation

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

## Disabling And Re-enabling Routing

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
