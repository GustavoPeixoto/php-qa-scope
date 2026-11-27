"""Execute GitHub Release publication with synthetic credentials and remote state."""

import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from release.test_workflows import (
    CREATE, FIXTURES, MERGE_WORKFLOW, MERGED_VALIDATION, PR_WORKFLOW, PUBLISHER,
    REPOSITORY, ROOT, SHA, PublisherHarness, checkout_step, eligible, job_section, step_command,
)


RELEASE_JOB = job_section(MERGE_WORKFLOW, "github-release")
RELEASE_COMMAND = step_command(RELEASE_JOB, "Verify tag and publish GitHub Release")
TAG = "v0.1.0"

# This executable never delegates to an installed gh or contacts GitHub.
FAKE_GH = r'''#!/usr/bin/env -S python3 -I -B
import json
import os
from pathlib import Path
import sys

path = Path(os.environ["FIXTURE_STATE"])
state = json.loads(path.read_text())
args = sys.argv[1:]
tag_write = args[:4] == ["api", "--method", "POST", "repos/GustavoPeixoto/php-qa-scope/git/refs"]
credential = "installation-token-fixture" if tag_write else "release-token-fixture"
assert os.environ["GH_TOKEN"] == credential
state["calls"].append({"args": args, "credential": "app" if tag_write else "normal"})
path.write_text(json.dumps(state))

def finish(payload=None, code=0, raw=None):
    path.write_text(json.dumps(state))
    if raw is not None:
        print(raw)
    elif payload is not None:
        print(json.dumps(payload))
    if code:
        print("synthetic GitHub failure", file=sys.stderr)
    sys.exit(code)

if args[:3] == ["api", "--method", "GET"] and len(args) == 4:
    endpoint = args[3]
    if endpoint in state["overrides"]:
        response = state["overrides"][endpoint]
        finish(response.get("json"), response.get("code", 0), response.get("raw"))
    if endpoint.startswith("repos/GustavoPeixoto/php-qa-scope/git/ref/tags/"):
        tag = endpoint.split("/git/ref/tags/", 1)[1]
        ref = "refs/tags/" + tag
        if ref not in state["refs"]:
            finish({"message": "Not Found"}, 1)
        finish({"ref": ref, "object": {"type": "commit", "sha": state["refs"][ref]}})
    if endpoint.startswith("repos/GustavoPeixoto/php-qa-scope/releases?per_page=100&page="):
        page = int(endpoint.rsplit("=", 1)[1])
        finish(state["releases"][(page - 1) * 100:page * 100])
elif tag_write:
    assert len(args) == 8 and args[4] == args[6] == "-f"
    ref = args[5].removeprefix("ref=")
    sha = args[7].removeprefix("sha=")
    if ref in state["refs"]:
        finish(code=22)
    if state["tag_failure"]:
        finish(code=state["tag_failure"])
    state["refs"][ref] = sha
    finish()
elif args[:2] == ["release", "create"]:
    tag = args[2]
    if "refs/tags/" + tag not in state["refs"] or any(r["tag_name"] == tag for r in state["releases"]):
        finish(code=22)
    if not state["create_failure"] or state["create_before_failure"]:
        state["releases"].append({
            "id": max([r["id"] for r in state["releases"]] + [0]) + 1,
            "tag_name": tag, "name": args[args.index("--title") + 1],
            "draft": False, "prerelease": False,
            "published_at": "2026-11-27T00:00:00Z", "body": "generated notes", "assets": [],
        })
    finish(code=state["create_failure"])
raise AssertionError("Unexpected GitHub operation: " + repr(args))
'''


def published_release(tag=TAG, identity=1, **changes):
    """Return API state with deliberately preserved user-edited presentation."""
    return {"id": identity, "tag_name": tag, "name": "Maintainer title", "draft": False,
            "prerelease": False, "published_at": "2026-11-27T00:00:00Z",
            "body": "Existing notes", "assets": [{"id": 42, "name": "existing.txt"}], **changes}


def publisher_outputs(authority):
    """Resolve the actual publisher job's output mapping rather than assume names."""
    header = PUBLISHER.split("    steps:", 1)[0]
    mapping = re.findall(r"^      (\w+): \$\{\{ steps\.authority\.outputs\.(\w+) \}\}$", header, re.MULTILINE)
    return {name: authority[source] for name, source in mapping}


class ReleaseHarness:
    """Persist fake remote state across publication and partial-job reruns."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "api.json"
        selected = self.directory / "tools/release"
        selected.mkdir(parents=True)
        shutil.copyfile(ROOT / "tools/release/github_release.py", selected / "github_release.py")
        client = self.directory / "gh"
        client.write_text(FAKE_GH)
        client.chmod(0o755)
        self.save({"refs": {"refs/tags/" + TAG: SHA}, "releases": [], "calls": [],
                   "overrides": {}, "tag_failure": 0, "create_failure": 0, "create_before_failure": False})
        self.authority_calls = 0
        self.app_tokens = 0
        self.outputs = {}

    def state(self):
        return json.loads(self.path.read_text())

    def save(self, state):
        self.path.write_text(json.dumps(state))

    def execute(self, command, token, environment):
        return subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", command], cwd=self.directory,
            env={**os.environ, "PATH": str(self.directory) + os.pathsep + os.environ["PATH"],
                 "GH_CONFIG_DIR": str(self.directory / "gh-config"), "GH_TOKEN": token,
                 "GITHUB_REPOSITORY": REPOSITORY, "FIXTURE_STATE": str(self.path), **environment},
            capture_output=True, text=True,
        )

    def release(self, publish_result="success", outputs=None, **environment):
        # Model Actions' default needs/success scheduling, not the hosted scheduler.
        header = RELEASE_JOB.split("    steps:", 1)[0]
        if re.search(r"^    needs: (\S+)$", header, re.MULTILINE).group(1) != "publish":
            raise AssertionError("Release job must depend on publish")
        if re.search(r"^    if:", header, re.MULTILINE):
            raise AssertionError("Expected default success-dependent job scheduling")
        if publish_result != "success":
            return "skipped"
        outputs = self.outputs if outputs is None else outputs
        mapping = re.findall(r"^          (\w+): \$\{\{ needs\.publish\.outputs\.(\w+) \}\}$", RELEASE_JOB, re.MULTILINE)
        values = {name: outputs.get(source, "") for name, source in mapping}
        return self.execute(RELEASE_COMMAND, "release-token-fixture", {**values, **environment})

    def publish(self, validation_result="success", fixture=None):
        fixture = copy.deepcopy(FIXTURES[0] if fixture is None else fixture)
        harness = PublisherHarness(fixture)
        if validation_result != "success" or not eligible(harness.event):
            return "skipped"
        fixture["tags"] = [ref.removeprefix("refs/tags/") for ref in self.state()["refs"]]
        harness.fixture = fixture
        self.authority_calls += 1
        authority = harness.run()
        self.app_tokens += 1
        result = self.execute(CREATE, "installation-token-fixture",
                              {"TAG": authority["tag"], "MERGE_SHA": authority["sha"]})
        if result.returncode == 0:
            self.outputs = publisher_outputs(authority)
        return result


class GitHubReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="github release fixture ")
        self.addCleanup(directory.cleanup)
        self.harness = ReleaseHarness(directory.name)
        self.outputs = {"tag": TAG, "sha": SHA}

    def assert_success(self, result):
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("release-token-fixture", result.stdout + result.stderr)

    def assert_failure_without_writes(self, message, outputs=None, **environment):
        before = self.harness.state()
        result = self.harness.release(outputs=self.outputs if outputs is None else outputs, **environment)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(message.casefold(), result.stderr.casefold())
        after = self.harness.state()
        self.assertEqual(before["refs"], after["refs"])
        self.assertEqual(before["releases"], after["releases"])
        self.assertTrue(all(call["args"][:3] == ["api", "--method", "GET"] for call in after["calls"]))

    def test_job_authority_handoff_and_scoped_credentials(self):
        self.assertEqual(self.outputs, publisher_outputs(self.outputs))
        header = RELEASE_JOB.split("    steps:", 1)[0]
        self.assertIn("name: Publish GitHub Release\n", header)
        self.assertIn("permissions:\n      contents: write\n", header)
        self.assertIn("runs-on: ubuntu-24.04\n", header)
        self.assertIn("GH_TOKEN: ${{ github.token }}", RELEASE_JOB)
        self.assertIn("TAG: ${{ needs.publish.outputs.tag }}", RELEASE_JOB)
        self.assertIn("MERGE_SHA: ${{ needs.publish.outputs.sha }}", RELEASE_JOB)
        self.assertIn("contents: read\n      pull-requests: read", PUBLISHER)
        self.assertNotIn("permissions:", MERGED_VALIDATION)
        self.assertNotIn("contents: write", PR_WORKFLOW)
        self.assertNotIn("${{", RELEASE_COMMAND)
        self.assertEqual("python3 -I -B tools/release/github_release.py", RELEASE_COMMAND)
        self.assertNotIn("        run: |", RELEASE_JOB)
        for forbidden in ["secrets.", "app-token", "RELEASE_APP", "pull-requests:", "always()"]:
            self.assertNotIn(forbidden, RELEASE_JOB)

    def test_job_skips_failed_canceled_and_skipped_publish(self):
        for outcome in ["failure", "cancelled", "skipped"]:
            with self.subTest(outcome=outcome):
                self.assertEqual("skipped", self.harness.release(outcome, self.outputs))
                self.assertEqual([], self.harness.state()["calls"])
        self.assert_success(self.harness.release(outputs=self.outputs))
        self.assertTrue(self.harness.state()["calls"])

    def test_checkout_uses_publisher_pin_and_exact_workflow_revision(self):
        checkout = checkout_step(RELEASE_JOB)
        publisher_checkout = checkout_step(PUBLISHER)
        pin = re.search(r"uses: (actions/checkout@[^\n]+)", publisher_checkout).group(1)
        self.assertIn("- name: Checkout repository\n", checkout)
        self.assertIn("uses: " + pin, checkout)
        self.assertIn("repository: ${{ github.repository }}", checkout)
        self.assertIn("ref: ${{ github.workflow_sha }}", checkout)
        self.assertIn("persist-credentials: false", checkout)
        self.assertLess(RELEASE_JOB.index("uses: actions/checkout@"),
                        RELEASE_JOB.index("- name: Verify tag and publish GitHub Release"))
        for forbidden in ["          path:", "sparse-checkout", "merge_commit_sha", "needs.publish.outputs",
                          "secrets.", "app-token"]:
            self.assertNotIn(forbidden, checkout)
        self.assertNotIn("continue-on-error:", RELEASE_JOB)
        self.assertEqual(4, (PR_WORKFLOW + MERGE_WORKFLOW).count("uses: actions/checkout@"))
        self.assertEqual(4, (PR_WORKFLOW + MERGE_WORKFLOW).count("      - name: Checkout repository\n"))

    def test_selected_script_is_required_without_candidate_or_module_fallback(self):
        initial = self.harness.state()
        selected = self.harness.directory / "tools/release/github_release.py"
        poison = 'from pathlib import Path\nPath("candidate-executed").touch()\nraise RuntimeError("wrong source")\n'
        for path in ["candidate/tools/release/github_release.py",
                     ".release-automation/tools/release/github_release.py", "github_release.py",
                     "candidate/json.py", "tools/release/json.py"]:
            path = self.harness.directory / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(poison)
        for missing in [False, True]:
            with self.subTest(missing=missing):
                self.harness.save(initial)
                if missing:
                    selected.unlink()
                result = self.harness.release(
                    outputs=self.outputs, GITHUB_WORKFLOW_SHA="b" * 40, GITHUB_SHA="c" * 40,
                    PYTHONPATH=str(self.harness.directory / "candidate"),
                )
                self.assertFalse((self.harness.directory / "candidate-executed").exists())
                state = self.harness.state()
                self.assertEqual(initial["refs"], state["refs"])
                if missing:
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("github_release.py", result.stderr)
                    self.assertEqual([], state["calls"])
                    self.assertEqual([], state["releases"])
                else:
                    self.assert_success(result)
                    self.assertEqual(1, len(state["releases"]))
                    self.assertIn(SHA, state["calls"][-1]["args"])

    def test_actual_creation_command_uses_outputs_for_first_and_later_versions(self):
        for tag in ["v0.1.0", "v1.2.3"]:
            with self.subTest(tag=tag):
                state = self.harness.state()
                state.update(refs={"refs/tags/" + tag: SHA}, releases=[], calls=[])
                self.harness.save(state)
                self.assert_success(self.harness.release(outputs={"tag": tag, "sha": SHA},
                                                        GITHUB_SHA="b" * 40, RELEASE_BRANCH="release/v9.0.0"))
                state = self.harness.state()
                self.assertEqual(["api", "--method", "GET", f"repos/{REPOSITORY}/git/ref/tags/{tag}"],
                                 state["calls"][0]["args"])
                self.assertEqual(["release", "create", tag, "--repo", REPOSITORY, "--verify-tag", "--target", SHA,
                                  "--title", tag, "--generate-notes", "--draft=false", "--prerelease=false"],
                                 state["calls"][-1]["args"])
                self.assertEqual({"refs/tags/" + tag: SHA}, state["refs"])
                release = state["releases"][0]
                self.assertEqual(tag, release["name"])
                self.assertFalse(release["draft"] or release["prerelease"])
                self.assertEqual([], release["assets"])

    def test_invalid_inputs_fail_before_any_github_request(self):
        for changes in [{"TAG": ""}, {"TAG": "v01.2.3"}, {"TAG": "v1.2.3-rc.1"},
                        {"TAG": "v1.2.3\n"}, {"MERGE_SHA": ""}, {"MERGE_SHA": "main"},
                        {"MERGE_SHA": "a" * 39}, {"GITHUB_REPOSITORY": "../bad/repo"}]:
            with self.subTest(changes=changes):
                self.assert_failure_without_writes("invalid", **changes)
                self.assertEqual([], self.harness.state()["calls"])
        self.assert_failure_without_writes("Missing", outputs={})
        self.assertEqual([], self.harness.state()["calls"])

    def test_missing_and_mismatched_remote_tags_prevent_even_existing_release_acceptance(self):
        initial = self.harness.state()
        initial["releases"] = [published_release()]
        for refs in [{}, {"refs/tags/" + TAG: "b" * 40}]:
            with self.subTest(refs=refs):
                self.harness.save({**initial, "refs": refs, "calls": []})
                self.assert_failure_without_writes("API lookup failed" if not refs else "expected SHA")
                self.assertEqual(1, len(self.harness.state()["calls"]))

    def test_remote_reference_shape_and_type_are_checked(self):
        endpoint = f"repos/{REPOSITORY}/git/ref/tags/{TAG}"
        for response in [None, [], {}, {"ref": "refs/tags/another", "object": {"type": "commit", "sha": SHA}},
                         {"ref": "refs/tags/" + TAG, "object": []},
                         {"ref": "refs/tags/" + TAG, "object": {"type": "tag", "sha": SHA}},
                         {"ref": "refs/tags/" + TAG, "object": {"type": "commit", "sha": "b" * 40}}]:
            with self.subTest(response=response):
                state = self.harness.state()
                state.update(calls=[], overrides={endpoint: {"raw": json.dumps(response)}})
                self.harness.save(state)
                self.assert_failure_without_writes("lightweight reference")
                self.assertEqual(1, len(self.harness.state()["calls"]))

    def test_published_release_is_unchanged_on_repetition(self):
        state = self.harness.state()
        state["releases"] = [published_release()]
        self.harness.save(state)
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                result = self.harness.release(outputs=self.outputs)
                self.assert_success(result)
                self.assertIn("leaving it unchanged", result.stdout)
                after = self.harness.state()
                self.assertEqual(state["refs"], after["refs"])
                self.assertEqual(state["releases"], after["releases"])
                self.assertTrue(all(call["args"][:3] == ["api", "--method", "GET"] for call in after["calls"]))

    def test_conflicting_draft_or_prerelease_is_not_changed(self):
        for draft, prerelease in [(True, False), (False, True), (True, True)]:
            with self.subTest(draft=draft, prerelease=prerelease):
                state = self.harness.state()
                state.update(calls=[], releases=[published_release(draft=draft, prerelease=prerelease)])
                self.harness.save(state)
                self.assert_failure_without_writes("Conflicting draft or prerelease")

    def test_complete_pagination_finds_published_and_conflicting_releases(self):
        unrelated = [published_release(tag=f"other-{i}", identity=i + 1) for i in range(100)]
        for match in [published_release(identity=101), published_release(identity=101, draft=True),
                      published_release(identity=101, prerelease=True), None]:
            with self.subTest(match=match):
                state = self.harness.state()
                state.update(calls=[], releases=unrelated + ([match] if match else []))
                self.harness.save(state)
                if match and (match["draft"] or match["prerelease"]):
                    self.assert_failure_without_writes("Conflicting")
                else:
                    self.assert_success(self.harness.release(outputs=self.outputs))
                state = self.harness.state()
                self.assertIn(["api", "--method", "GET", f"repos/{REPOSITORY}/releases?per_page=100&page=2"],
                              [call["args"] for call in state["calls"]])
                self.assertEqual(0 if match else 1, sum(call["args"][:2] == ["release", "create"]
                                                      for call in state["calls"]))

    def test_api_and_network_errors_never_establish_absence(self):
        tag_endpoint = f"repos/{REPOSITORY}/git/ref/tags/{TAG}"
        page_endpoint = f"repos/{REPOSITORY}/releases?per_page=100&page=1"
        for endpoint in [tag_endpoint, page_endpoint]:
            for response in [{"code": 1, "json": {"message": "Bad credentials", "status": "401"}},
                             {"code": 1, "json": {"message": "Forbidden", "status": "403"}},
                             {"code": 1, "json": {"message": "Not Found", "status": "404"}},
                             {"code": 22, "json": {"message": "Server error", "status": "500"}},
                             {"code": 1, "raw": "network unavailable"}, {"raw": "{"}]:
                with self.subTest(endpoint=endpoint, response=response):
                    state = self.harness.state()
                    state.update(calls=[], overrides={endpoint: response})
                    self.harness.save(state)
                    self.assert_failure_without_writes("API lookup failed" if response.get("code") else "Malformed")

    def test_invalid_records_and_published_state_are_fatal(self):
        endpoint = f"repos/{REPOSITORY}/releases?per_page=100&page=1"
        malformed = [None, {}, [None], [published_release(identity=i + 1) for i in range(101)],
                     [published_release(identity=True)], [published_release(identity=0)],
                     [published_release(tag=None)], [published_release(draft="false")],
                     [published_release(prerelease=0)]]
        inconsistent = [[published_release(published_at=None)], [published_release(published_at="")],
                        [published_release(), published_release(identity=2)]]
        for message, pages in [("Malformed", malformed), ("Inconsistent", inconsistent)]:
            for page in pages:
                with self.subTest(page=page):
                    state = self.harness.state()
                    state.update(calls=[], overrides={endpoint: {"raw": json.dumps(page)}})
                    self.harness.save(state)
                    self.assert_failure_without_writes(message)

    def test_incomplete_or_repeated_later_pages_are_fatal_even_after_match(self):
        page = [published_release(identity=i + 1, tag=TAG if i == 0 else f"other-{i}") for i in range(100)]
        for response, message in [({"code": 1}, "API lookup failed"), ({"raw": "{"}, "Malformed"),
                                  ({"json": page}, "Repeated/inconsistent")]:
            with self.subTest(response=response):
                state = self.harness.state()
                state.update(calls=[], releases=page,
                             overrides={f"repos/{REPOSITORY}/releases?per_page=100&page=2": response})
                self.harness.save(state)
                self.assert_failure_without_writes(message)

    def test_release_creation_failure_does_not_modify_tag(self):
        for code in [1, 22]:
            with self.subTest(code=code):
                state = self.harness.state()
                state.update(calls=[], create_failure=code)
                self.harness.save(state)
                result = self.harness.release(outputs=self.outputs)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("GitHub Release creation failed", result.stderr)
                after = self.harness.state()
                self.assertEqual(state["refs"], after["refs"])
                self.assertEqual([], after["releases"])
                self.assertEqual("create", after["calls"][-1]["args"][1])

    def test_native_tag_publication_then_release_uses_original_authority(self):
        state = self.harness.state()
        state["refs"] = {"refs/tags/notes": "d" * 40}
        self.harness.save(state)
        self.assert_success(self.harness.publish())
        self.assertEqual(self.outputs, self.harness.outputs)
        refs = self.harness.state()["refs"]
        self.assert_success(self.harness.release(GITHUB_SHA="c" * 40))
        state = self.harness.state()
        self.assertEqual(refs, state["refs"])
        self.assertEqual(1, self.harness.authority_calls)
        self.assertEqual(1, self.harness.app_tokens)
        self.assertEqual("app", state["calls"][0]["credential"])
        self.assertTrue(all(call["credential"] == "normal" for call in state["calls"][1:]))
        self.assertEqual(TAG, state["releases"][0]["tag_name"])

    def test_failed_or_ineligible_validation_never_reaches_release(self):
        initial = self.harness.state()
        initial["refs"] = {}
        ordinary = {**FIXTURES[0], "branch": "feature/example"}
        fork = {**FIXTURES[0], "fork": True}
        for outcome, fixture in [("failure", None), ("cancelled", None), ("skipped", None),
                                 ("success", ordinary), ("success", fork)]:
            with self.subTest(outcome=outcome, fixture=fixture):
                self.harness.save(initial)
                self.assertEqual("skipped", self.harness.publish(outcome, fixture))
                self.assertEqual("skipped", self.harness.release("skipped"))
                self.assertEqual([], self.harness.state()["calls"])
        self.assertEqual(0, self.harness.authority_calls)
        self.assertEqual(0, self.harness.app_tokens)

    def test_native_tag_failure_blocks_release_and_preserves_refs(self):
        state = self.harness.state()
        state.update(refs={"refs/tags/notes": "d" * 40}, tag_failure=22)
        self.harness.save(state)
        result = self.harness.publish()
        self.assertEqual(22, result.returncode)
        self.assertEqual("skipped", self.harness.release("failure"))
        after = self.harness.state()
        self.assertEqual(state["refs"], after["refs"])
        self.assertEqual([], after["releases"])
        self.assertEqual(1, len(after["calls"]))
        self.assertEqual("POST", after["calls"][0]["args"][2])

    def test_partial_rerun_recovers_without_authority_app_token_or_tag_creation(self):
        initial = self.harness.state()
        for remote_success in [False, True]:
            with self.subTest(remote_success=remote_success):
                state = copy.deepcopy(initial)
                state.update(refs={"refs/tags/notes": "d" * 40}, create_failure=1,
                             create_before_failure=remote_success)
                self.harness.save(state)
                self.assert_success(self.harness.publish())
                published_refs = self.harness.state()["refs"]
                result = self.harness.release()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("GitHub Release creation failed", result.stderr)
                state = self.harness.state()
                self.assertEqual(published_refs, state["refs"])
                self.assertEqual(1 if remote_success else 0, len(state["releases"]))
                boundary = len(state["calls"])
                authority_calls, app_tokens = self.harness.authority_calls, self.harness.app_tokens
                state.update(create_failure=0, create_before_failure=False)
                # A later stable tag must not trigger progression checks on recovery.
                state["refs"]["refs/tags/v0.2.0"] = "b" * 40
                expected_refs = copy.deepcopy(state["refs"])
                existing_releases = copy.deepcopy(state["releases"])
                self.harness.save(state)
                self.assert_success(self.harness.release())
                after = self.harness.state()
                self.assertEqual(expected_refs, after["refs"])
                self.assertEqual(1, len(after["releases"]))
                self.assertEqual(TAG, after["releases"][0]["tag_name"])
                if remote_success:
                    self.assertEqual(existing_releases, after["releases"])
                self.assertEqual(authority_calls, self.harness.authority_calls)
                self.assertEqual(app_tokens, self.harness.app_tokens)
                self.assertEqual(["api", "--method", "GET", f"repos/{REPOSITORY}/git/ref/tags/{TAG}"],
                                 after["calls"][boundary]["args"])
                self.assertTrue(all(call["credential"] == "normal" for call in after["calls"][boundary:]))
                self.assertFalse(any(call["args"][:3] == ["api", "--method", "POST"]
                                     for call in after["calls"][boundary:]))
                creates = [call for call in after["calls"][boundary:] if call["args"][:2] == ["release", "create"]]
                self.assertEqual(0 if remote_success else 1, len(creates))
                self.assert_success(self.harness.release())
                self.assertEqual(after["refs"], self.harness.state()["refs"])
                self.assertEqual(after["releases"], self.harness.state()["releases"])

    def test_rerunning_tag_authority_still_rejects_existing_tag_at_same_sha(self):
        state = self.harness.state()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.harness.publish()
        self.assertEqual(1, self.harness.authority_calls)
        self.assertEqual(0, self.harness.app_tokens)
        self.assertEqual([], self.harness.state()["calls"])
        self.assertEqual(state["refs"], self.harness.state()["refs"])
        self.assertEqual("skipped", self.harness.release("failure"))


if __name__ == "__main__":
    unittest.main()
