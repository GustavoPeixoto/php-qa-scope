"""Adapter boundaries; real-package setup is exercised by test_runtime."""

import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "docker/dev/bin/setup-codex-context-mode"
LOADER = importlib.machinery.SourceFileLoader("context_mode_bootstrap", str(BOOTSTRAP))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
ADAPTER = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(ADAPTER)


class ReadinessTests(unittest.TestCase):
    def test_wait_retries_missing_executable_and_launcher_127(self):
        unavailable = subprocess.CompletedProcess([], 127, "", "extension not installed")
        ready = subprocess.CompletedProcess([], 0, "codex-cli fixture", "")
        with patch.object(ADAPTER.subprocess, "run", side_effect=[FileNotFoundError(), unavailable, ready]) as run, \
                patch.object(ADAPTER.time, "monotonic", return_value=0), \
                patch.object(ADAPTER.time, "sleep") as sleep, \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            ADAPTER.codex_ready(30)
        self.assertEqual(3, run.call_count)
        self.assertEqual([call(2), call(2)], sleep.call_args_list)
        self.assertTrue(all(c.kwargs["timeout"] == 5 for c in run.call_args_list))
        self.assertTrue(all(c.args[0] == ["codex", "--version"] for c in run.call_args_list))
        self.assertEqual(1, output.getvalue().count("Waiting up to"))

    def test_deadline_caps_attempt_and_sleep_then_reports_retry_instructions(self):
        with patch.object(ADAPTER.subprocess, "run", side_effect=FileNotFoundError()) as run, \
                patch.object(ADAPTER.time, "monotonic", side_effect=[0, 0, 2.5, 3]), \
                patch.object(ADAPTER.time, "sleep") as sleep, \
                patch("sys.stdout", new_callable=io.StringIO):
            with self.assertRaisesRegex(RuntimeError, "within 3s.*reconnect"):
                ADAPTER.codex_ready(3)
        self.assertEqual(1, run.call_count)
        self.assertEqual(3, run.call_args.kwargs["timeout"])
        sleep.assert_called_once_with(0.5)

    def test_real_errors_and_probe_timeouts_fail_without_retry(self):
        outcomes = [(subprocess.CompletedProcess([], 9, "", "codex broken"), "exited 9: codex broken"),
                    (subprocess.TimeoutExpired("codex", 5, stderr="probe stuck"), "timed out: probe stuck")]
        for outcome, message in outcomes:
            with self.subTest(message=message), \
                    patch.object(ADAPTER.subprocess, "run", side_effect=[outcome]) as run, \
                    patch.object(ADAPTER.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, message):
                    ADAPTER.codex_ready(30)
                run.assert_called_once()
                sleep.assert_not_called()

    def test_manual_readiness_is_fail_fast(self):
        for outcome in [FileNotFoundError(), subprocess.CompletedProcess([], 127, "", "missing extension")]:
            with self.subTest(outcome=outcome), \
                    patch.object(ADAPTER.subprocess, "run", side_effect=[outcome]) as run, \
                    patch.object(ADAPTER.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "Codex is unavailable"):
                    ADAPTER.codex_ready()
                run.assert_called_once()
                self.assertEqual(5, run.call_args.kwargs["timeout"])
                sleep.assert_not_called()


class ContextModeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "codex"
        self.home.mkdir()
        (self.home / "auth.json").write_bytes(b'{"fixture":"synthetic-account"}')
        (self.home / "auth.json").chmod(0o600)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "invocation.json"
        self.env = {**os.environ, "CODEX_HOME": str(self.home), "PATH": str(self.bin),
                    "ADAPTER_SENTINEL": "inherited", "ADAPTER_CALL_LOG": str(self.log)}
        codex = self.bin / "codex"
        codex.write_text(f'#!{sys.executable}\nprint("codex-cli fixture")\n')
        codex.chmod(0o755)
        backend = self.bin / "context-mode"
        backend.write_text(f'''#!{sys.executable}
import json, os, pathlib, signal, sys
pathlib.Path(os.environ["ADAPTER_CALL_LOG"]).write_text(json.dumps({{
    "args": sys.argv[1:], "CODEX_HOME": os.environ["CODEX_HOME"],
    "sentinel": os.environ.get("ADAPTER_SENTINEL")
}}))
if os.environ.get("ADAPTER_SETUP_SIGNAL"):
    os.kill(os.getpid(), signal.SIGTERM)
sys.exit(int(os.environ.get("ADAPTER_SETUP_EXIT", "0")))
''')
        backend.chmod(0o755)

    def run_setup(self, *args):
        return subprocess.run([sys.executable, str(BOOTSTRAP), *args], env=self.env,
                              cwd=self.base, text=True, capture_output=True, timeout=10)

    def test_delegates_exact_command_and_inherits_environment_without_rewriting_home(self):
        self.env["CODEX_HOME"] = "relative-codex-home"
        result = self.run_setup()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"args": ["setup", "--yes", "--agents", "codex"],
                          "CODEX_HOME": "relative-codex-home", "sentinel": "inherited"},
                         json.loads(self.log.read_text()))
        self.assertEqual(b'{"fixture":"synthetic-account"}', (self.home / "auth.json").read_bytes())

    def test_valid_wait_option_reaches_official_setup(self):
        result = self.run_setup("--wait-for-codex", "180")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.log.exists())

    def test_upstream_exit_status_and_signal_reach_caller(self):
        for extra, expected in [({"ADAPTER_SETUP_EXIT": "23"}, 23), ({"ADAPTER_SETUP_SIGNAL": "1"}, -signal.SIGTERM)]:
            with self.subTest(expected=expected):
                self.env.pop("ADAPTER_SETUP_EXIT", None)
                self.env.pop("ADAPTER_SETUP_SIGNAL", None)
                self.env.update(extra)
                self.assertEqual(expected, self.run_setup().returncode)

    def test_invalid_arguments_fail_before_readiness_or_setup(self):
        # Missing Codex distinguishes argument rejection from a readiness failure.
        (self.bin / "codex").unlink()
        for args in [("--reset",), ("--unknown",), ("--wait-for-codex",),
                     ("--wait-for-codex", "0"), ("--wait-for-codex", "-1"),
                     ("--wait-for-codex", "1.5"), ("--wait-for-codex", "invalid")]:
            with self.subTest(args=args):
                result = self.run_setup(*args)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertNotIn("Codex is unavailable", result.stderr)
                self.assertFalse(self.log.exists())

    def test_missing_codex_does_not_invoke_setup_or_change_account_state(self):
        (self.bin / "codex").unlink()
        before = (self.home / "auth.json").read_bytes()
        result = self.run_setup()
        self.assertEqual(1, result.returncode)
        self.assertIn("Codex is unavailable", result.stderr)
        self.assertFalse(self.log.exists())
        self.assertEqual(before, (self.home / "auth.json").read_bytes())

    def test_missing_setup_executable_reports_failure(self):
        (self.bin / "context-mode").unlink()
        result = self.run_setup()
        self.assertEqual(1, result.returncode)
        self.assertIn("context-mode", result.stderr)


if __name__ == "__main__":
    unittest.main()
