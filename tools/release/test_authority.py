"""Test authority failures and the workflow's native script invocation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from release.contract import ReleaseError
from release.test_validate import FIXTURES, REPOSITORY
from release.test_workflows import MERGE_WORKFLOW, PublisherHarness, ROOT, SHA, step_command


class AuthorityTests(unittest.TestCase):
    def test_rejects_invalid_events_and_api_identities_without_outputs(self):
        for key, value in [("action", "opened"), ("number", True), ("number", 0),
                           ("pull_request", None), ("pull_request", {"merge_commit_sha": "not-a-sha"})]:
            harness = PublisherHarness(FIXTURES[0])
            harness.event[key] = value
            with self.subTest(event_key=key, value=value), self.assertRaises(ReleaseError):
                harness.run()
        for value in [None, [], {}, {"number": True}, {"number": 7, "merged": 1}]:
            harness = PublisherHarness(FIXTURES[0])
            harness.overrides[f"repos/{REPOSITORY}/pulls/7"] = value
            with self.subTest(pr=value), self.assertRaises(ReleaseError):
                harness.run()

    def test_non_release_never_inherits_validation_skip(self):
        for branch in ["feature/example", "docs/readme", "release/invalid", "release/v0.1.0;echo bad"]:
            harness = PublisherHarness({**FIXTURES[0], "branch": branch})
            with self.subTest(branch=branch), self.assertRaises(ReleaseError):
                harness.run()

    def test_workflow_invokes_selected_sibling_modules_and_fails_without_fallback(self):
        command = step_command(MERGE_WORKFLOW, "Recheck current publication authority")
        modules = ["authority.py", "contract.py", "github_api.py"]
        for missing in [None, *modules]:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                selected = directory / "tools/release"
                selected.mkdir(parents=True)
                for name in modules:
                    if name != missing:
                        shutil.copyfile(ROOT / "tools/release" / name, selected / name)

                # This candidate tree must never supply executable automation or modules.
                candidate = directory / "candidate/tools/release"
                candidate.mkdir(parents=True)
                poison = 'from pathlib import Path\nPath("candidate-executed").touch()\nraise RuntimeError("wrong source")\n'
                for name in modules:
                    (candidate / name).write_text(poison)
                previous = directory / ".release-automation/tools/release"
                previous.mkdir(parents=True)
                for name in modules:
                    (previous / name).write_text(poison)
                (directory / "composer.json").write_text('{"version":"99.0.0"}')

                harness = PublisherHarness(FIXTURES[0])
                event_path, output = directory / "event.json", directory / "outputs"
                event_path.write_text(json.dumps(harness.event))
                responses = {
                    f"repos/{REPOSITORY}/pulls/7": harness.pr,
                    f"repos/{REPOSITORY}/contents/composer.json?ref={SHA}": harness.content,
                    f"repos/{REPOSITORY}/tags?per_page=100&page=1": [],
                }
                (directory / "responses.json").write_text(json.dumps(responses))
                client = directory / "gh"
                client.write_text(
                    '#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\n'
                    'assert sys.argv[1:4] == ["api","--method","GET"]\n'
                    'assert os.environ["GH_TOKEN"] == "read-only-fixture"\n'
                    'with open("calls.jsonl","a") as log: log.write(json.dumps(sys.argv[4])+"\\n")\n'
                    'print(json.dumps(json.loads(Path("responses.json").read_text())[sys.argv[4]]))\n'
                )
                client.chmod(0o755)
                # An unavailable script/module must stop the next, simulated credential step.
                pipeline = command + '\nprintf token-generated > "$TOKEN_MARKER"'
                result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", pipeline], cwd=directory,
                                        env={**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"],
                                             "PYTHONPATH": str(candidate), "GITHUB_WORKFLOW_SHA": "b" * 40,
                                             "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_PATH": str(event_path),
                                             "GITHUB_OUTPUT": str(output), "GH_TOKEN": "read-only-fixture",
                                             "TOKEN_MARKER": str(directory / "token-marker")},
                                        capture_output=True, text=True, check=False)
                self.assertEqual("", result.stdout)
                self.assertFalse((directory / "candidate-executed").exists())
                if missing:
                    self.assertNotEqual(0, result.returncode)
                    self.assertFalse(output.exists())
                    self.assertFalse((directory / "token-marker").exists())
                else:
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(f"tag=v0.1.0\nsha={SHA}\n", output.read_text())
                    self.assertTrue((directory / "token-marker").exists())
                    self.assertEqual(list(responses), [json.loads(line) for line in
                                                      (directory / "calls.jsonl").read_text().splitlines()])


if __name__ == "__main__":
    unittest.main()
