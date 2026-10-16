"""Native adapters retain scope, exit codes, and isolated report evidence."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from git_hooks import containers, execution, qa, reports
from test_reports import native_text, native_proof


class QATests(unittest.TestCase):
    def test_openspec_local_reports_and_real_codes(self):
        for mode in ("passed", "failed", "malformed", "launch"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run = reports.allocate(root)
                env = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
                def native(argv, **kwargs):
                    self.assertEqual(argv, ["openspec", "validate", "--all", "--strict", "--no-interactive", "--json"])
                    self.assertEqual(kwargs["cwd"], root)
                    if mode == "launch":
                        raise FileNotFoundError("openspec")
                    valid = mode == "passed"
                    data = {"version": "1.0", "root": {"path": str(root)},
                            "items": [{"id": "fixture", "type": "change", "valid": valid, "issues": []}],
                            "summary": {"totals": {"items": 1, "passed": int(valid), "failed": int(not valid)}}}
                    kwargs["stdout"].write(b"invalid" if mode == "malformed" else json.dumps(data).encode())
                    return subprocess.CompletedProcess(argv, 0 if valid or mode == "malformed" else 1)
                with patch.object(execution, "run", side_effect=native), patch.object(containers, "execute") as docker:
                    self.assertEqual(qa.check(root, "openspec", env), 0 if mode == "passed" else 1)
                    docker.assert_not_called()
                record = reports.collect(run, "openspec")
                self.assertEqual(record["exit_code"], None if mode == "launch" else 1 if mode == "failed" else 0)
                self.assertEqual(record["report_valid"], mode in ("passed", "failed"))
                self.assertEqual(record["container_cleanup"], "not_applicable")
                self.assertFalse((run / "containers").exists())

    def runtime(self, run, key):
        context = containers.configure(run, {"Id": "a" * 64, "Image": "sha256:" + "b" * 64,
            "Config": {"Labels": {"com.docker.compose.project": "unit"}}})
        (run / "containers").mkdir()
        containers.update(run, context, key)

    def removed(self, root, run, session, key):
        containers.update(run, containers.context(run), key, cleanup="removed", state="removed")
        return True

    def test_command_matrix_and_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            for key in reports.PHP_CHECKS:
                run = reports.allocate(directory)
                env = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
                self.runtime(run, key)
                def native(root, actual_run, actual_key, argv, stdout, stderr):
                    self.assertEqual(argv[:3], ["composer", "--no-interaction", "--no-ansi"])
                    self.assertEqual((actual_run, actual_key), (run, key))
                    self.assertNotIn("fixer-fix", argv)
                    self.assertNotIn("sniffer-fix", argv)
                    stderr.write(b"Composer diagnostic\n")
                    report = run / reports.CHECKS[key][1]
                    content = native_text(key).encode()
                    if key in ("qa-scope", "fixer", "stan"):
                        stdout.write(content)
                    else:
                        report.write_bytes(content)
                    native_proof(run, key)
                    return 0
                with patch.object(containers, "execute", side_effect=native), \
                        patch.object(containers, "cleanup", side_effect=self.removed):
                    self.assertEqual(qa.check(Path(directory), key, env), 0)
                record = reports.collect(run, key)
                self.assertEqual(record["status"], "passed")
                self.assertIn("Composer diagnostic", (run / record["diagnostics"]).read_text())
                self.assertEqual((run / f"results/{key}/stdout.log").exists(), key not in ("qa-scope", "fixer", "stan"))
                if key == "md":
                    self.assertIn("--reportfile-json", qa.command(key, run))

    def test_missing_malformed_and_launch_errors(self):
        for key in ("fixer", "sniffer", "test"):
            for mode in ("missing", "malformed", "launch", "nonzero"):
                with tempfile.TemporaryDirectory() as directory:
                    run = reports.allocate(directory)
                    env = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
                    self.runtime(run, key)
                    def native(root, actual_run, actual_key, argv, stdout, stderr):
                        if mode == "launch":
                            raise FileNotFoundError("docker missing")
                        content = b"invalid native report" if mode != "nonzero" else (
                            native_text(key).encode())
                        if key == "fixer":
                            stdout.write(content)
                        elif mode != "missing":
                            (run / reports.CHECKS[key][1]).write_bytes(content)
                        native_proof(run, key, 2 if mode == "nonzero" else 0)
                        return 2 if mode == "nonzero" else 0
                    with patch.object(containers, "execute", side_effect=native), \
                            patch.object(containers, "cleanup", side_effect=self.removed):
                        self.assertEqual(qa.check(Path(directory), key, env), 1)
                    record = reports.collect(run, key)
                    self.assertEqual(record["status"], "failed")
                    self.assertEqual(record["exit_code"], None if mode == "launch" else (2 if mode == "nonzero" else 0))
                    self.assertEqual(record["report_valid"], mode == "nonzero")
                    if key == "fixer" and mode == "malformed":
                        self.assertFalse((run / "results/fixer/result.json").exists())
                        self.assertIn("invalid native", (run / "results/fixer/execution.log").read_text())

    def test_direct_execution_requires_context(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                qa.check(Path(directory), "stan", {})
