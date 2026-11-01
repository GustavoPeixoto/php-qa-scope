"""Opt-in native smoke on a retained, clean export of HEAD; no Git mutations."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import tempfile
import unittest
from unittest.mock import patch

from git_hooks import reports
from pr_qa import cli


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get("PR_QA_NATIVE_TESTS") == "1", "Requires Docker and shared tooling images at matching host paths")
class NativeTests(unittest.TestCase):
    def test_real_startup_failure_and_catchable_cancellation(self):
        fixture = Path(tempfile.mkdtemp(prefix="pr-qa-cancel-", dir=ROOT / "tmp"))
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        environment = dict(os.environ, GIT_DIR=str(ROOT / ".git"), GIT_WORK_TREE=str(fixture))
        (fixture / "composer.json").write_text(json.dumps({"name": "fixture/qa", "scripts": {
            "qa-scope": "php -r 'echo \"native-started\\n\"; sleep(60);'"}}))
        with patch.dict(os.environ, environment):
            # The Node image has no Composer; Docker startup must not become a native success.
            self.assertEqual(1, cli.check(fixture, "qa-scope", "php-qa-scope-pr-node-tooling", revision))
            outcome = json.loads((fixture / "logs/pr-qa/outcomes/qa-scope.json").read_text())
            self.assertIsNone(outcome["native_exit_code"])
        snapshot = ["docker", "ps", "--all", "--filter", "name=pr-qa-qa-scope-", "--format", "{{.Names}}"]
        before = subprocess.check_output(snapshot)
        argv = ["python3", "-B", str(ROOT / "tools/pr-qa"), "--check", "qa-scope",
                "--image", "php-qa-scope-pr-php-tooling", "--revision", revision]
        with (fixture / "adapter.stdout.log").open("wb") as stdout, (fixture / "adapter.stderr.log").open("wb") as stderr:
            child = subprocess.Popen(argv, cwd=fixture, env=environment, stdout=stdout, stderr=stderr)
            try:
                captured = fixture / "logs/pr-qa/results/qa-scope/stdout.log"
                deadline = time.monotonic() + 15
                while not captured.exists() or "native-started" not in captured.read_text():
                    self.assertIsNone(child.poll(), f"Adapter exited early; see {fixture}")
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.05)
                child.send_signal(signal.SIGTERM)
                self.assertNotEqual(0, child.wait(timeout=20))
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
        outcome = json.loads((fixture / "logs/pr-qa/outcomes/qa-scope.json").read_text())
        self.assertEqual("cancelled", outcome["status"])
        self.assertIsNone(outcome["native_exit_code"])
        self.assertIn("native-started", captured.read_text())
        self.assertEqual(before, subprocess.check_output(snapshot))
        print(f"Native startup/cancellation evidence: {fixture}")

    def test_clean_revision_all_checks_aggregate_and_native_findings(self):
        fixture = Path(tempfile.mkdtemp(prefix="pr-qa-native-", dir=ROOT / "tmp"))
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        # Export committed blobs without export-ignore, an index, refs, or commits.
        entries = subprocess.check_output(["git", "ls-tree", "-rz", "HEAD"], cwd=ROOT).split(b"\0")
        for entry in filter(None, entries):
            metadata, filename = entry.split(b"\t", 1)
            mode, kind, oid = metadata.split()
            self.assertEqual(b"blob", kind)
            path = fixture / os.fsdecode(filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            # Global negations allow env examples/markers even inside tmp; remove
            # these fixture-only copies after the unchanged-tree assertions.
            if path.name in (".env.example", ".gitkeep"):
                self.addCleanup(path.unlink, missing_ok=True)
            data = subprocess.check_output(["git", "cat-file", "blob", oid.decode()], cwd=ROOT)
            if mode == b"120000":
                path.symlink_to(os.fsdecode(data))
            else:
                path.write_bytes(data)
                path.chmod(int(mode, 8) & 0o777)
        environment = dict(os.environ, GIT_DIR=str(ROOT / ".git"), GIT_WORK_TREE=str(fixture))
        php = "php-qa-scope-pr-php-tooling"
        node = "php-qa-scope-pr-node-tooling"
        install = subprocess.run(["docker", "run", "--rm", "--init", "--user", f"{os.getuid()}:{os.getgid()}",
                                  "--tmpfs", "/tmp:rw,mode=1777", "--env", "HOME=/tmp", "--env", "COMPOSER_HOME=/tmp/composer",
                                  "--mount", f"type=bind,source={fixture},target={fixture}", "--workdir", str(fixture), php,
                                  "composer", "install", "--no-interaction", "--no-ansi", "--prefer-dist", "--no-progress"], capture_output=True)
        (fixture / "install.stdout.log").write_bytes(install.stdout)
        (fixture / "install.stderr.log").write_bytes(install.stderr)
        self.assertEqual(0, install.returncode, install.stderr.decode())
        previous = {key: os.environ.get(key) for key in ("GIT_DIR", "GIT_WORK_TREE")}
        os.environ.update({key: environment[key] for key in previous})
        try:
            def clean():
                self.assertEqual(0, subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=fixture, env=environment, capture_output=True).returncode)

            clean()
            downloaded = fixture / "logs/pr-qa/downloaded"
            for key in reports.CHECKS:
                with redirect_stdout(io.StringIO()):
                    result = cli.check(fixture, key, node if key == "openspec" else php, revision)
                self.assertEqual(0, result, f"{key}: see {fixture}/logs/pr-qa")
                artifact = downloaded / f"qa-{key}"
                (artifact / "outcomes").mkdir(parents=True)
                shutil.copyfile(fixture / f"logs/pr-qa/outcomes/{key}.json", artifact / f"outcomes/{key}.json")
                shutil.copytree(fixture / f"logs/pr-qa/results/{key}", artifact / f"results/{key}")
            self.assertEqual(0, cli.aggregate(fixture, downloaded, revision, "success"))
            clean()
            phpcs = fixture / "phpcs.xml"
            original = phpcs.read_bytes()
            try:
                phpcs.write_bytes(original.replace(b"<file>.</file>", b"<file>src</file>"))
                self.assertEqual(1, cli.check(fixture, "qa-scope", php, revision))
                outcome = json.loads((fixture / "logs/pr-qa/outcomes/qa-scope.json").read_text())
                self.assertNotEqual(0, outcome["native_exit_code"])
                self.assertTrue(outcome["report_valid"])
                self.assertTrue((fixture / "logs/pr-qa/results/qa-scope/stdout.log").read_text())
            finally:
                phpcs.write_bytes(original)
            clean()
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            print(f"Native QA revision {revision}; retained evidence: {fixture}")


if __name__ == "__main__":
    unittest.main()
