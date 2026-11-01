"""Exercise native validators, Docker boundaries, and per-check execution."""

from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from git_hooks import qa, reports
from git_hooks.test_reports import native_text
from pr_qa import cli


SHA = "a" * 40


def native(key, root, failed=False):
    if key == "openspec":
        return json.dumps({"version": "1.0", "root": {"path": str(root)},
                           "items": [{"id": "fixture", "type": "spec", "valid": not failed, "issues": []}],
                           "summary": {"totals": {"items": 1, "passed": int(not failed), "failed": int(failed)}}})
    value = native_text(key)
    if failed:
        if key == "qa-scope":
            value = value.replace("OK phpstan", "OUT-OF-SYNC phpstan")
        elif key == "test":
            value = value.replace('failures="0"', 'failures="1"').replace('/></testsuite>', '><failure/></testcase></testsuite>')
        else:
            data = json.loads(value)
            if key in ("sniffer", "stan"):
                data["totals"]["errors"] = 1
            else:
                data["files"] = [{"name": "fixture.php"}]
            value = json.dumps(data)
    return value


class AdapterFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.quiet = io.StringIO()
        self.stdout = redirect_stdout(self.quiet)
        self.stderr = redirect_stderr(self.quiet)
        self.stdout.__enter__()
        self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def execute(self, key, *, content=None, code=0, failure=None, state_error=False):
        commands = []

        def run(argv, **kwargs):
            commands.append(argv)
            if argv[1] == "create":
                self.assertIn("--init", argv)
                self.assertIn(f"type=bind,source={self.root},target={self.root}", argv)
                native_argv = qa.command(key, self.root / "logs/pr-qa")
                self.assertEqual(argv[argv.index("--entrypoint") + 1], native_argv[0])
                self.assertEqual(argv[-len(native_argv[1:]):], native_argv[1:])
                self.assertNotIn("--tty", argv)
                self.assertNotIn("--interactive", argv)
                self.assertFalse(any("sock" in value or "TOKEN" in value for value in argv))
                if failure == "missing":
                    raise FileNotFoundError("docker")
                if failure == "create":
                    kwargs["stderr"].write(b"creation diagnostic")
                    return 125
                return 0
            kwargs["stderr"].write(b"native stderr\n")
            kwargs["stdout"].write(b"available stdout\n" if failure else b"")
            if failure == "cancel":
                raise cli.Cancelled("fixture interruption")
            text = native(key, self.root, code != 0) if content is None else content
            if key in cli.STDOUT_REPORTS:
                kwargs["stdout"].write(text.encode())
            else:
                (self.root / "logs/pr-qa" / reports.CHECKS[key][1]).write_text(text)
            return code

        def docker(argv, **kwargs):
            commands.append(argv)
            if argv[1] == "inspect":
                state = {"Status": "exited", "Error": "exec missing" if state_error else "",
                         "StartedAt": "2026-10-20T00:00:00Z", "ExitCode": code, "OOMKilled": False}
                return subprocess.CompletedProcess(argv, 0, json.dumps(state), "")
            return subprocess.CompletedProcess(argv, 0, b"removed", b"")

        with patch.object(cli, "validate_revision"), patch.object(cli, "process", side_effect=run), patch.object(cli.subprocess, "run", side_effect=docker):
            result = cli.check(self.root, key, "fixture:tooling", SHA)
        outcome = json.loads((self.root / f"logs/pr-qa/outcomes/{key}.json").read_text())
        self.assertEqual(commands[-1][1:3], ["rm", "--force"])
        return result, outcome

class AdapterTests(AdapterFixture):
    def test_all_formats_accept_real_validator_contract_and_keep_native_findings(self):
        for key in reports.CHECKS:
            for code in (0, 1):
                with self.subTest(key=key, code=code):
                    result, outcome = self.execute(key, code=code)
                    self.assertEqual(int(code != 0), result)
                    self.assertEqual(code, outcome["native_exit_code"])
                    self.assertTrue(outcome["report_valid"])
                    self.assertEqual("passed" if code == 0 else "failed", outcome["status"])
                    self.assertIn("native stderr", (self.root / f"logs/pr-qa/results/{key}/stderr.log").read_text())

    def test_invalid_empty_semantic_and_foreign_root_reports_fail(self):
        for key in reports.CHECKS:
            invalid = ["", "malformed", "{}", native(key, self.root, True)]
            if key == "openspec":
                invalid.append(native(key, "/foreign"))
            for text in invalid:
                with self.subTest(key=key, report=text):
                    result, outcome = self.execute(key, content=text)
                    self.assertEqual(1, result)
                    self.assertEqual(0, outcome["native_exit_code"])
                    self.assertFalse(outcome["report_valid"])
                    if key in cli.STDOUT_REPORTS:
                        self.assertEqual(text, (self.root / f"logs/pr-qa/results/{key}/stdout.log").read_text())

    def test_preparation_startup_and_cancellation_preserve_available_evidence(self):
        for failure in ("missing", "create", "cancel"):
            result, outcome = self.execute("fixer", failure=failure)
            self.assertEqual(1, result)
            self.assertIsNone(outcome["native_exit_code"])
            self.assertIsNotNone(outcome["error"])
            if failure == "cancel":
                self.assertEqual("cancelled", outcome["status"])
                self.assertIn("available stdout", (self.root / "logs/pr-qa/results/fixer/stdout.log").read_text())
        result, outcome = self.execute("fixer", state_error=True)
        self.assertEqual(1, result)
        self.assertIsNone(outcome["native_exit_code"])

    def test_revision_and_cli_inputs(self):
        with patch.object(cli.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, SHA, "")):
            cli.validate_revision(self.root, SHA)
            for value in ("HEAD", "b" * 40, "a" * 41):
                with self.assertRaises(ValueError):
                    cli.validate_revision(self.root, value)
        with self.assertRaises(ValueError):
            cli.check(self.root, "unknown", "image", SHA)
        with self.assertRaises(SystemExit):
            cli.main(["--check", "fixer", "--revision", SHA])

    def test_check_dispatch_and_removed_cli_modes(self):
        argv = ["--check", "fixer", "--image", "fixture:tooling", "--revision", SHA]
        with patch.object(cli, "check", return_value=0) as execute:
            self.assertEqual(0, cli.main(argv))
        execute.assert_called_once_with(Path.cwd().resolve(), "fixer", "fixture:tooling", SHA)
        for invalid in (["--aggregate", str(self.root), "--revision", SHA],
                        argv + ["--upstream-result", "success"],
                        ["--check", "unknown", "--image", "fixture:tooling", "--revision", SHA],
                        ["--image", "fixture:tooling", "--revision", SHA],
                        ["--check", "fixer", "--image", "fixture:tooling"]):
            with self.subTest(argv=invalid), self.assertRaises(SystemExit) as rejected:
                cli.main(invalid)
            self.assertEqual(2, rejected.exception.code)

    def test_interrupted_client_is_reaped(self):
        from unittest.mock import Mock
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [cli.Cancelled("cancelled"), subprocess.TimeoutExpired("docker", 5), 0]
        with patch.object(cli.subprocess, "Popen", return_value=child):
            with self.assertRaises(cli.Cancelled):
                cli.process(["docker", "start"])
        child.terminate.assert_called_once()
        child.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
