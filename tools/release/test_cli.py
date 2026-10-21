"""Exercise the validation CLI through direct-script and module invocation."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from release.test_validate import REPOSITORY


ROOT = Path(__file__).resolve().parents[2]


class ValidationCliTests(unittest.TestCase):
    def invoke(self, manifest, tags, branch="release/v0.1.0", arguments=(), module=False):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "composer.json").write_text(json.dumps(manifest))
            (directory / "tags.json").write_text(json.dumps(tags))
            command = [sys.executable, "-B"]
            command += ["-m", "release.validate"] if module else [str(ROOT / "tools/release/validate.py")]
            return subprocess.run(command + ["--tags", "tags.json", *arguments], cwd=directory,
                                  env={**os.environ, "PYTHONPATH": str(ROOT / "tools"),
                                       "RELEASE_BRANCH": branch, "GITHUB_REPOSITORY": REPOSITORY,
                                       "HEAD_REPOSITORY": REPOSITORY, "BASE_BRANCH": "main"},
                                  capture_output=True, text=True, check=False)

    def test_script_and_module_environment_defaults(self):
        for module in [False, True]:
            with self.subTest(module=module):
                result = self.invoke({"version": "0.1.0"}, [], module=module)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual({"release": True, "tag": "v0.1.0", "version": "0.1.0", "baseline": None},
                                 json.loads(result.stdout))
                self.assertEqual("", result.stderr)

    def test_explicit_arguments_override_environment(self):
        result = self.invoke({"version": "1.2.4"}, ["v1.2.3"], branch="release/invalid",
                             arguments=("--manifest", "composer.json", "--branch", "release/v1.2.4",
                                        "--repository", REPOSITORY, "--head-repository", REPOSITORY,
                                        "--base", "main"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"release": True, "tag": "v1.2.4", "version": "1.2.4", "baseline": "1.2.3"},
                         json.loads(result.stdout))

    def test_ordinary_branch_keeps_skip_result(self):
        result = self.invoke({}, [], branch="feature/example")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"release": False}, json.loads(result.stdout))

    def test_error_json_and_exit_status(self):
        for manifest, tags, branch, message in [
            ({}, [], "release/v0.1.0", "Manifest version must equal 0.1.0 exactly"),
            ({"version": "0.1.0"}, ["v0.1.0"], "release/v0.1.0", "Target ref already exists: v0.1.0"),
            ({"version": "0.1.0"}, [], "release/v01.0.0", "Expected canonical release/vX.Y.Z branch"),
        ]:
            with self.subTest(branch=branch, tags=tags):
                result = self.invoke(manifest, tags, branch)
                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual({"error": message}, json.loads(result.stderr))


if __name__ == "__main__":
    unittest.main()
