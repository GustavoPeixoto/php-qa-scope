"""Container integration checks for Headroom setup, rollback, and startup.

Run with /opt/headroom/bin/python docker/dev/tests/test_headroom.py in dev.
The tests use temporary Codex homes and never contact a model provider.
"""

import asyncio
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import tempfile
import unittest

import httpx
import tomlkit
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.home = Path(self.workspace.name)
        self.env = {**os.environ, "CODEX_HOME": str(self.home)}
        self.config = self.home / "config.toml"

    def tearDown(self):
        self.workspace.cleanup()

    def setup_headroom(self, *args, check=True):
        return subprocess.run(
            ["setup-codex-headroom", *args], env=self.env,
            capture_output=True, text=True, check=check,
        )

    def test_fresh_setup_is_idempotent_and_restores_absent_settings(self):
        self.setup_headroom()
        first = self.config.read_text()
        self.setup_headroom()
        self.assertEqual(first, self.config.read_text())
        config = tomlkit.parse(first)
        self.assertTrue(config["model_providers"]["headroom"]["requires_openai_auth"])
        self.assertEqual(config["mcp_servers"]["headroom"]["command"], "/usr/local/bin/headroom")
        self.setup_headroom("--disable")
        restored = tomlkit.parse(self.config.read_text())
        self.assertNotIn("model_provider", restored)
        self.assertNotIn("headroom", restored.get("mcp_servers", {}))
        self.assertFalse((self.home / "config.toml.before-headroom").exists())

    def test_existing_configuration_hooks_auth_and_history_survive(self):
        original = '''# User settings
model = "gpt-5.4"
model_provider = "openai"
openai_base_url = "https://api.openai.com/v1"

[features]
hooks = true

[mcp_servers.context-mode]
command = "context-mode"

[mcp_servers.headroom]
command = "previous-headroom"

[profiles.review]
model_provider = "another-provider"
'''
        self.config.write_text(original)
        hooks = self.home / "hooks.json"
        hooks.write_text('{"hooks":{"SessionStart":[{"custom":"keep"}]}}')
        auth = self.home / "auth.json"
        auth.write_text('{"auth_mode":"chatgpt"}')
        before_hooks, before_auth = hooks.read_bytes(), auth.read_bytes()
        db = sqlite3.connect(self.home / "state_5.sqlite")
        db.execute("CREATE TABLE threads (id TEXT, model_provider TEXT)")
        db.execute("INSERT INTO threads VALUES ('existing', 'openai')")
        db.execute("INSERT INTO threads VALUES ('other', 'another-provider')")
        db.commit()
        self.setup_headroom()
        first = self.config.read_text()
        self.setup_headroom()
        self.assertEqual(first, self.config.read_text())
        self.assertEqual((self.home / "config.toml.before-headroom").read_text(), original)
        configured = tomlkit.parse(first)
        self.assertEqual(configured["mcp_servers"]["context-mode"]["command"], "context-mode")
        self.assertEqual(configured["profiles"]["review"]["model_provider"], "another-provider")
        self.assertIn("# User settings", first)
        self.assertEqual(db.execute("SELECT model_provider FROM threads WHERE id='existing'").fetchone()[0], "headroom")
        # Simulate a setting added after enable: rollback must retain it.
        configured["features"]["new_setting"] = True
        self.config.write_text(tomlkit.dumps(configured))
        self.setup_headroom("--disable")
        restored = tomlkit.parse(self.config.read_text())
        self.assertEqual(restored["model_provider"], "openai")
        self.assertEqual(restored["mcp_servers"]["headroom"]["command"], "previous-headroom")
        self.assertTrue(restored["features"]["new_setting"])
        self.assertEqual(db.execute("SELECT model_provider FROM threads WHERE id='existing'").fetchone()[0], "openai")
        self.assertEqual(db.execute("SELECT model_provider FROM threads WHERE id='other'").fetchone()[0], "another-provider")
        db.close()
        self.assertEqual(hooks.read_bytes(), before_hooks)
        self.assertEqual(auth.read_bytes(), before_auth)

    def test_invalid_configuration_is_not_overwritten(self):
        self.config.write_text('[invalid\n')
        result = self.setup_headroom(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_text(), '[invalid\n')
        self.assertFalse((self.home / "config.toml.before-headroom").exists())

    def test_mcp_beacon_respects_environment_and_defaults_when_unset(self):
        self.env["HEADROOM_BEACON"] = "on"
        self.setup_headroom()
        configured = tomlkit.parse(self.config.read_text())
        self.assertEqual(configured["mcp_servers"]["headroom"]["env"]["HEADROOM_BEACON"], "on")
        first = self.config.read_text()
        self.setup_headroom()
        self.assertEqual(first, self.config.read_text())
        self.env.pop("HEADROOM_BEACON")
        self.setup_headroom()
        configured = tomlkit.parse(self.config.read_text())
        self.assertEqual(configured["mcp_servers"]["headroom"]["env"]["HEADROOM_BEACON"], "off")

    def test_context_mode_setup_can_run_before_and_after_headroom(self):
        subprocess.run(["setup-codex-context-mode"], env=self.env, capture_output=True, check=True)
        hooks = (self.home / "hooks.json").read_bytes()
        self.setup_headroom()
        configured = self.config.read_text()
        subprocess.run(["setup-codex-context-mode"], env=self.env, capture_output=True, check=True)
        self.assertEqual(self.config.read_text(), configured)
        self.assertEqual((self.home / "hooks.json").read_bytes(), hooks)


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.home = Path(self.workspace.name)
        self.env = {**os.environ, "CODEX_HOME": str(self.home)}

    def tearDown(self):
        pid_file = self.home / "headroom/proxy.pid"
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text()), signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.workspace.cleanup()

    def start(self, **env):
        return subprocess.run(
            ["start-headroom-proxy"], env={**self.env, **env},
            capture_output=True, text=True, timeout=150,
        )

    def test_occupied_port_fails_without_starting_a_second_listener(self):
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 8787))
            listener.listen()
            result = self.start(HEADROOM_STARTUP_TIMEOUT="2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("port 8787 is occupied", result.stderr)
        self.assertFalse((self.home / "headroom/proxy.pid").exists())

    def test_real_proxy_starts_reuses_process_and_mcp_retrieves_original(self):
        options = {
            "HEADROOM_SAVINGS_PROFILE": "balanced",
            "HEADROOM_MODE": "token",
            "HEADROOM_BEACON": "off",
        }
        first = self.start(**options)
        self.assertEqual(first.returncode, 0, first.stderr)
        pid = (self.home / "headroom/proxy.pid").read_text()
        second = self.start(**options)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(pid, (self.home / "headroom/proxy.pid").read_text())
        self.assertIn("already ready", second.stdout)
        response = httpx.get("http://127.0.0.1:8787/readyz")
        response.raise_for_status()
        self.assertTrue(response.json()["ready"])
        runtime = httpx.get("http://127.0.0.1:8787/stats").json()
        self.assertEqual(runtime["summary"]["mode"], "token")
        self.assertEqual(runtime["config"]["savings_profile"], "balanced")
        process_env = Path(f"/proc/{pid.strip()}/environ").read_bytes().split(b"\0")
        self.assertIn(b"HEADROOM_SAVINGS_PROFILE=balanced", process_env)
        self.assertIn(b"HEADROOM_BEACON=off", process_env)
        content = json.dumps([{"id": i, "status": "ok", "message": "repeated log entry"} for i in range(500)])
        compressed = httpx.post(
            "http://127.0.0.1:8787/v1/compress",
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "user", "content": "Find errors in these log entries."},
                    {"role": "assistant", "content": None, "tool_calls": [
                        {"id": "logs", "type": "function", "function": {"name": "read_logs", "arguments": "{}"}}
                    ]},
                    {"role": "tool", "tool_call_id": "logs", "content": content},
                ],
            },
            timeout=30,
        )
        compressed.raise_for_status()
        self.assertLess(compressed.json()["tokens_after"], compressed.json()["tokens_before"])
        asyncio.run(self.check_mcp())

    async def check_mcp(self):
        params = StdioServerParameters(
            command="headroom", args=["mcp", "serve", "--proxy-url", "http://127.0.0.1:8787"],
            env={**self.env, "HEADROOM_BEACON": "off"},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = {tool.name for tool in (await session.list_tools()).tools}
                self.assertTrue({"headroom_compress", "headroom_retrieve", "headroom_stats"} <= names)
                content = json.dumps([{"id": i, "status": "ok", "message": "repeated log entry"} for i in range(100)])
                compressed = await session.call_tool("headroom_compress", {"content": content})
                self.assertFalse(compressed.isError)
                result = json.loads(compressed.content[0].text)
                self.assertIn("hash", result)
                retrieved = await session.call_tool("headroom_retrieve", {"hash": result["hash"]})
                self.assertFalse(retrieved.isError)
                self.assertIn("repeated log entry", retrieved.content[0].text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
