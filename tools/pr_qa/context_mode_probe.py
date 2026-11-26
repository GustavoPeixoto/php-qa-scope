"""Run inside a disposable development container with the real package and Codex."""

import json
import os
from pathlib import Path
import select
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tomllib


def run(*args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, timeout=90, **kwargs)
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result.stdout


def state(home):
    names = ["config.toml", "hooks.json", "auth.json"] + [
        f"skills/{skill}/SKILL.md" for skill in ("ctx-doctor", "ctx-stats", "ctx-upgrade")]
    return {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
            for name in names if (home / name).exists()}


def check_cold_lifecycle(base):
    """Use the image launcher and deliver the real binary like an extension."""
    metadata = json.loads(Path("/tmp/context-mode-devcontainer.json").read_text())
    assert metadata["waitFor"] == "postCreateCommand"
    assert "setup-codex-context-mode" not in metadata["postCreateCommand"]
    assert metadata["postAttachCommand"] == "setup-codex-context-mode --wait-for-codex 180"
    home = base / "codex"
    extensions = base / "extensions"
    home.mkdir()
    extensions.mkdir()
    env = {**os.environ, "HOME": str(base), "CODEX_HOME": str(home),
           "CODEX_VSCODE_EXTENSIONS_DIR": str(extensions)}
    (base / "lefthook.yml").write_text(Path("/tmp/context-mode-lefthook.yml").read_text())
    assert subprocess.run(["codex", "--version"], env=env, capture_output=True).returncode == 127
    run("sh", "-c", metadata["postCreateCommand"], env=env, cwd=base)
    hook = base / ".git/hooks/pre-push"
    assert "# php-qa-scope managed pre-push launcher" in hook.read_text()
    assert not (home / "config.toml").exists(), "post-create ran Codex setup"
    auth = home / "auth.json"
    auth.write_text('{"fixture":"cold-lifecycle"}')
    auth.chmod(0o600)
    data = base / ".context-mode/cold-history-sentinel"
    data.parent.mkdir()
    data.write_bytes(b"keep cold history")
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(shlex.split(metadata["postAttachCommand"]), env=env, cwd=base,
                                   stdout=subprocess.PIPE, stderr=errors)
        try:
            assert select.select([process.stdout], [], [], 10)[0], "no readiness diagnostic"
            line = process.stdout.readline()
            assert b"Waiting up to 180s" in line, line
            assert process.poll() is None and not (home / "config.toml").exists()
            binary = extensions / "openai.chatgpt-fixture/bin/linux-x86_64/codex"
            binary.parent.mkdir(parents=True)
            shutil.copy2("/tmp/context-mode-real-codex", binary)
            output, _ = process.communicate(timeout=60)
            errors.seek(0)
            assert process.returncode == 0, (output, errors.read())
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
    before = state(home)
    run("sh", "-c", metadata["postAttachCommand"], env=env, cwd=base)
    assert state(home) == before, "reconnect changed managed files"
    assert data.read_bytes() == b"keep cold history"
    assert auth.read_text() == '{"fixture":"cold-lifecycle"}'
    doctor = run("context-mode", "doctor", "--agents", "codex", env=env, cwd=base)
    assert "PASS" in doctor and "FAIL" not in doctor, doctor
    assert "enabled" in run("codex", "mcp", "list", env=env, cwd=base)
    # Remaining probes still use the production launcher, never a second CLI.
    os.environ["CODEX_VSCODE_EXTENSIONS_DIR"] = str(extensions)


def bootstrap(base, existing):
    home = base / "codex"
    home.mkdir()
    auth = home / "auth.json"
    auth.write_text('{"OPENAI_API_KEY":"synthetic-validation-only"}')
    auth.chmod(0o600)
    env = {**os.environ, "HOME": str(base), "CODEX_HOME": str(home)}
    user_hook = {"matcher": "fixture-only", "hooks": [
        {"type": "command", "command": "printf third-party-hook"}]}
    trust_key = str(home / "hooks.json") + ":pre_tool_use:1:0"
    user_skill = home / "skills/user-skill/SKILL.md"
    if existing:
        # Seed a working v2 installation, then add independent user state.
        run("setup-codex-context-mode", env=env, cwd=base)
        config_file = home / "config.toml"
        text = 'model = "runtime-fixture"\n' + config_file.read_text()
        text += ('\n[mcp_servers.other]\ncommand = "python3"\n'
                 '[hooks.state."third-party-hook"]\ntrusted_hash = "sha256:' + 'f' * 64 + '"\n')
        text += f'\n[hooks.state.{json.dumps(trust_key)}]\ntrusted_hash = "sha256:' + 'e' * 64 + '"\n'
        config_file.write_text(text)
        hooks_file = home / "hooks.json"
        hooks = json.loads(hooks_file.read_text())
        hooks["fixture"] = "keep"
        for event in ("PreToolUse", "Stop"):
            hooks["hooks"].setdefault(event, []).append(user_hook)
        hooks_file.write_text(json.dumps(hooks))
        user_skill.parent.mkdir(parents=True)
        user_skill.write_text("user-owned skill")
    sentinel = base / ".context-mode/history-sentinel"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_bytes(b"preserved history")
    before = state(home)
    run("setup-codex-context-mode", env=env, cwd=base)
    first = state(home)
    run("setup-codex-context-mode", env=env, cwd=base)
    assert first == state(home), "setup is not idempotent"
    assert first["auth.json"] == before["auth.json"]
    assert sentinel.read_bytes() == b"preserved history"
    config = tomllib.loads((home / "config.toml").read_text())
    server = config["mcp_servers"]["context-mode"]
    assert Path(server["command"]).name == "node"
    assert Path(server["args"][0]).name == "server.mjs"
    package = Path(server["args"][0]).parent / "package.json"
    assert json.loads(package.read_text())["version"] == sys.argv[1]
    assert server["args"][1:] == ["--agent", "codex"]
    assert server["env"]["CODEX_HOME"] == str(home)
    hooks = json.loads((home / "hooks.json").read_text())
    own = [(event, group, handler) for event, groups in hooks["hooks"].items()
           for group in groups for handler in group["hooks"] if "hook.mjs" in handler["command"]]
    assert {event for event, _, _ in own} == {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"}
    assert len(own) == 4
    trust = config["hooks"]["state"]
    assert len(trust) == 4 + 2 * int(existing), trust
    assert all(v["trusted_hash"].startswith("sha256:") for v in trust.values())
    if existing:
        assert config["model"] == "runtime-fixture"
        assert config["mcp_servers"]["other"] == {"command": "python3"}
        assert trust["third-party-hook"]["trusted_hash"] == "sha256:" + "f" * 64
        assert trust[trust_key]["trusted_hash"] == "sha256:" + "e" * 64
        assert user_skill.read_text() == "user-owned skill"
        assert hooks["fixture"] == "keep"
        for event in ("PreToolUse", "Stop"):
            assert [g for g in hooks["hooks"][event] if g.get("matcher") == "fixture-only"] == [user_hook]
    listing = run("codex", "mcp", "list", env=env, cwd=base)
    assert "context-mode" in listing and "enabled" in listing
    doctor = run("context-mode", "doctor", "--agents", "codex", env=env, cwd=base)
    assert "PASS" in doctor and "FAIL" not in doctor, doctor
    return home, server, own, env


def check_mcp(base, server, env):
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen([server["command"], *server["args"]], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors, env=env, cwd=base)
        pending = b""

        def request(method, params, identity):
            nonlocal pending
            message = {"jsonrpc": "2.0", "method": method, "params": params}
            if identity is not None:
                message["id"] = identity
            process.stdin.write((json.dumps(message) + "\n").encode())
            process.stdin.flush()
            if identity is None:
                return
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    reply = json.loads(line)
                    if reply.get("id") == identity:
                        assert "error" not in reply, reply
                        return reply["result"]
                if select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))[0]:
                    chunk = os.read(process.stdout.fileno(), 65536)
                    assert chunk, "MCP exited before replying"
                    pending += chunk
            raise AssertionError(f"MCP timeout: {method}")

        try:
            init = request("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                          "clientInfo": {"name": "codex", "version": "runtime-probe"}}, 1)
            # The published v2.1.8 bundle reports "dev" in serverInfo.version.
            # Verify its package manifest above and its MCP identity here.
            assert init["serverInfo"]["name"] == "context-mode", init
            request("notifications/initialized", {}, None)
            names = {t["name"] for t in request("tools/list", {}, 2)["tools"]}
            assert names == {"ctx_execute", "ctx_batch", "ctx_index", "ctx_search", "ctx_resume",
                             "ctx_stats", "ctx_doctor", "ctx_upgrade", "ctx_purge"}, names
            sample = base / "sample.txt"
            sample.write_text("runtime-file-sentinel")
            calls = [
                ("ctx_execute", {"language": "python", "file": str(sample), "code":
                                 "import os; from pathlib import Path; print(Path(os.environ['CTX_FILE']).read_text())"},
                 "runtime-file-sentinel"),
                ("ctx_batch", {"commands": ["printf runtime-batch-sentinel"],
                               "queries": ["runtime-batch-sentinel"]}, "runtime-batch-sentinel"),
                ("ctx_index", {"content": "# Runtime\nDistinctive mars migration sentinel for the runtime probe.",
                               "source": "runtime-probe"}, None),
                ("ctx_search", {"queries": ["distinctive mars migration"], "source": "runtime-probe"}, "Distinctive"),
                ("ctx_resume", {}, None),
            ]
            for identity, (name, arguments, expected) in enumerate(calls, 3):
                result = request("tools/call", {"name": name, "arguments": arguments}, identity)
                assert not result.get("isError"), result
                if expected:
                    assert expected in json.dumps(result), (name, result)
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()


def check_hooks(base, own, env):
    large = base / "large.log"
    large.write_text("runtime large output line\n" * 10000)
    for event, _, handler in own:
        payload = {"hook_event_name": event, "session_id": "runtime-probe", "cwd": str(base),
                   "source": "startup", "prompt": "runtime probe", "tool_name": "Bash",
                   "tool_input": {"command": f"cat {shlex.quote(str(large))}"},
                   "tool_response": {"stdout": "small probe output", "stderr": ""}}
        result = subprocess.run(shlex.split(handler["command"]), input=json.dumps(payload),
                                text=True, capture_output=True, env=env, cwd=base, timeout=15)
        if event == "PreToolUse":
            assert "ctx_execute" in result.stdout, result
            assert result.returncode == 2 or "deny" in result.stdout, result
        else:
            assert result.returncode == 0, result


assert run("context-mode", "--version").strip() == sys.argv[1]
run("node", "--input-type=module", "-e",
    "import {DatabaseSync} from 'node:sqlite'; const db=new DatabaseSync(':memory:');"
    "db.exec('CREATE VIRTUAL TABLE probe USING fts5(content)'); db.close();")
with tempfile.TemporaryDirectory(prefix="context-mode-cold-") as directory:
    cold = Path(directory)
    run("git", "init", "--quiet", str(cold))
    check_cold_lifecycle(cold)
    for existing in (False, True):
        with tempfile.TemporaryDirectory(prefix="context-mode-runtime-") as directory:
            base = Path(directory)
            run("git", "init", "--quiet", str(base))
            home, server, own, env = bootstrap(base, existing)
            check_mcp(base, server, env)
            check_hooks(base, own, env)
print(json.dumps({"version": sys.argv[1], "cold_lifecycle": "passed", "fresh": "passed",
                  "existing": "passed", "mcp": "passed", "hooks": "passed"}))
