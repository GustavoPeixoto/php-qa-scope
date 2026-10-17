"""Execute actual workflow-owned code against mocked GitHub responses.

Only Python's standard library is used. Syntax/security linters run separately.
"""

import base64
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from release.test_validate import FIXTURES, REPOSITORY


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
PR_WORKFLOW = (WORKFLOWS / "validate-release.yml").read_text()
MERGE_WORKFLOW = (WORKFLOWS / "create-release-tag.yml").read_text()
SHA = "a" * 40


def block(source, marker):
    """Extract a literal run block from the real workflow without a YAML dependency."""
    section = source.split(marker, 1)[1]
    lines = section.split("        run: |\n", 1)[1].splitlines()
    body = []
    for line in lines:
        if line and not line.startswith("          "):
            break
        body.append(line[10:] if line else "")
    return "\n".join(body)


AUTHORITY = block(MERGE_WORKFLOW, "- name: Recheck current publication authority")
CREATE = block(MERGE_WORKFLOW, "- name: Create immutable lightweight release ref")
ORIGIN = block(PR_WORKFLOW, "- name: Check release origin")


def merged_pr(fixture):
    return {
        "number": 7, "merged": True, "state": "closed", "merge_commit_sha": SHA,
        "base": {"ref": "main", "repo": {"full_name": REPOSITORY}},
        "head": {"ref": fixture["branch"], "repo": {"full_name": "fork/repo" if fixture.get("fork") else REPOSITORY}},
    }


def eligible(event, repository=REPOSITORY):
    """Evaluate the limited Actions condition used by both post-merge jobs."""
    source = MERGE_WORKFLOW.split("    if: >-\n", 1)[1].split("    runs-on:", 1)[0]
    pr = event["pull_request"]
    values = {
        "github.event.pull_request.merged": pr.get("merged"),
        "github.event.pull_request.base.ref": pr["base"]["ref"],
        "github.event.pull_request.head.repo.full_name": (pr["head"].get("repo") or {}).get("full_name"),
        "github.event.pull_request.head.ref": pr["head"]["ref"],
        "github.repository": repository,
    }
    for key in sorted(values, key=len, reverse=True):
        source = source.replace(key, repr(values[key]))
    source = source.replace("true", "True").replace("&&", " and ")
    return eval(" ".join(source.split()), {"__builtins__": {}, "startsWith": lambda value, prefix: value.startswith(prefix)})


class PublisherHarness:
    def __init__(self, fixture):
        self.fixture = fixture
        self.pr = merged_pr(fixture)
        self.event = {"action": "closed", "number": 7, "pull_request": copy.deepcopy(self.pr)}
        self.content = {
            "type": "file", "path": "composer.json", "encoding": "base64",
            "content": base64.encodebytes(json.dumps(fixture["manifest"]).encode()).decode(),
        }
        self.calls = []
        self.overrides = {}
        self.tokens = []

    def request(self, argv, **kwargs):
        self.calls.append(argv)
        endpoint = argv[4]
        if argv[:4] != ['gh', 'api', '--method', 'GET']:
            raise AssertionError('Authority attempted a write')
        if endpoint in self.overrides:
            value = self.overrides[endpoint]
        elif "/pulls/" in endpoint:
            value = self.pr
        elif "/contents/" in endpoint:
            value = self.content
        elif "/tags?" in endpoint:
            page = int(endpoint.rsplit("=", 1)[1])
            value = [{"name": name} for name in self.fixture["tags"][(page - 1) * 100:page * 100]]
        else:
            raise AssertionError(f"Unexpected endpoint {endpoint}")
        self.tokens.append(os.environ.get("GH_TOKEN"))
        if isinstance(value, Exception):
            raise value
        if isinstance(value, subprocess.CompletedProcess):
            return value
        return subprocess.CompletedProcess(argv, 0, json.dumps(value), "")

    def run(self):
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "event.json"
            output = Path(directory) / "output"
            event_path.write_text(json.dumps(self.event))
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_PATH": str(event_path),
                                         "GITHUB_OUTPUT": str(output), "GH_TOKEN": "read-only-fixture"}), patch("subprocess.run", self.request):
                try:
                    exec(compile(AUTHORITY, "workflow-authority", "exec"), {})
                except Exception:
                    if output.exists():
                        raise AssertionError("Failed validation published outputs")
                    raise
            return dict(line.split("=", 1) for line in output.read_text().splitlines())


class WorkflowTests(unittest.TestCase):
    def test_same_fixtures_execute_actual_inline_logic(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture):
                harness = PublisherHarness(fixture)
                if fixture["ok"] and fixture["branch"].startswith("release/"):
                    self.assertEqual({"tag": "v" + fixture["manifest"]["version"], "sha": SHA}, harness.run())
                else:
                    with self.assertRaises((ValueError, KeyError, TypeError)):
                        harness.run()
                self.assertTrue(all(token == "read-only-fixture" for token in harness.tokens))
                self.assertFalse(any(call[3] == "POST" for call in harness.calls))

    def test_event_gate_and_integrated_sha(self):
        fixture = FIXTURES[0]
        good = {"pull_request": merged_pr(fixture)}
        self.assertTrue(eligible(good))
        for target, value in [("merged", False), ("state", "open")]:
            h = PublisherHarness(fixture)
            h.pr[target] = value
            with self.assertRaises(ValueError):
                h.run()
        for location, value in [("base", "other"), ("head", "feature/example")]:
            event = copy.deepcopy(good)
            event["pull_request"][location]["ref"] = value
            self.assertFalse(eligible(event))
        event = copy.deepcopy(good)
        event["pull_request"]["merged"] = False
        self.assertFalse(eligible(event))
        event = copy.deepcopy(good)
        event["pull_request"]["head"]["repo"]["full_name"] = "fork/repo"
        self.assertFalse(eligible(event))
        for method in ["merge", "squash", "rebase"]:
            with self.subTest(method=method):
                h = PublisherHarness(fixture)
                h.pr["head"]["sha"] = "b" * 40
                h.pr["base"]["sha"] = "c" * 40
                self.assertEqual(SHA, h.run()["sha"])
                self.assertTrue(any(f"contents/composer.json?ref={SHA}" in call[4] for call in h.calls))

    def test_fresh_api_eligibility_and_malformed_responses(self):
        cases = [
            ("number", 8), ("merged", "true"), ("state", "open"),
            ("merge_commit_sha", "b" * 40), ("base", {"ref": "other", "repo": {"full_name": REPOSITORY}}),
            ("head", {"ref": "release/v0.1.0", "repo": {"full_name": "fork/repo"}}),
            ("head", {"ref": "release/v0.1.0", "repo": None}),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                h = PublisherHarness(FIXTURES[0])
                h.pr[key] = value
                with self.assertRaises((ValueError, TypeError)):
                    h.run()
        for value in [{}, [], {"encoding": "utf-8"}, {"type": "file", "path": "composer.json", "encoding": "base64", "content": "!!!"},
                      {"type": "file", "path": "composer.json", "encoding": "base64", "content": "e30="}]:
            h = PublisherHarness(FIXTURES[0])
            h.content = value
            with self.subTest(content=value), self.assertRaises((ValueError, AttributeError)):
                h.run()
        for value in [None, {}, [None], [{"name": 42}], [{"name": ""}], subprocess.CompletedProcess([], 1, "", "denied"),
                      subprocess.CompletedProcess([], 0, "{", "")]:
            h = PublisherHarness(FIXTURES[0])
            h.overrides[f"repos/{REPOSITORY}/tags?per_page=100&page=1"] = value
            with self.subTest(tags=value), self.assertRaises((ValueError, TypeError)):
                h.run()

    def test_all_tag_pages_and_incomplete_pagination(self):
        fixture = {"branch": "release/v1.10.1", "manifest": {"version": "1.10.1"},
                   "tags": [f"ignored-{i}" for i in range(98)] + ["v1.9.0", "1.8.0", "v1.10.0", "v2.0.0-rc.1"]}
        h = PublisherHarness(fixture)
        self.assertEqual("v1.10.1", h.run()["tag"])
        endpoint = f"repos/{REPOSITORY}/tags?per_page=100&page=2"
        self.assertIn(endpoint, [call[4] for call in h.calls])
        for value in [RuntimeError("network failed"), [{"name": name} for name in fixture["tags"][:100]]]:
            h = PublisherHarness(fixture)
            h.overrides[endpoint] = value
            with self.assertRaises((RuntimeError, ValueError)):
                h.run()

    def test_actual_create_step_shape_and_failure_propagation(self):
        for code in [0, 1, 22]:
            h = PublisherHarness(FIXTURES[0])
            output = h.run()
            with tempfile.TemporaryDirectory() as directory:
                executable = Path(directory) / "gh"
                # A fixture-only client captures the exact native shell argv.
                executable.write_text('#!/usr/bin/env python3\nimport json,os,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(int(os.environ["FIXTURE_CODE"]))\n')
                executable.chmod(0o755)
                result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", CREATE],
                                        env={**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"],
                                             "GITHUB_REPOSITORY": REPOSITORY, "TAG": output["tag"], "MERGE_SHA": output["sha"],
                                             "GH_TOKEN": "app-fixture", "FIXTURE_CODE": str(code)}, capture_output=True, text=True)
                self.assertEqual(code, result.returncode)
                argv = json.loads(result.stdout)
                self.assertEqual(["api", "--method", "POST", f"repos/{REPOSITORY}/git/refs", "-f", "ref=refs/tags/v0.1.0", "-f", f"sha={SHA}"], argv)

    def test_serialized_different_versions_recheck_fresh_state(self):
        # The fixture scheduler models the documented Actions concurrency contract.
        # Assert that the real workflow puts all authority/token/create steps inside it.
        publisher = MERGE_WORKFLOW.split('  publish:', 1)[1]
        self.assertIn('group: protected-release-publication\n      cancel-in-progress: false', publisher)
        self.assertLess(publisher.index('    concurrency:'), publisher.index('    steps:'))
        fixtures = [
            {'branch': 'release/v1.1.0', 'manifest': {'version': '1.1.0'}, 'tags': []},
            {'branch': 'release/v1.0.1', 'manifest': {'version': '1.0.1'}, 'tags': []},
        ]
        tags = ['v1.0.0']
        results = []
        lock = threading.Lock()
        entered = threading.Event()
        release_first = threading.Event()

        def run(fixture, first=False):
            with lock:
                if first:
                    entered.set()
                    self.assertTrue(release_first.wait(5))
                h = PublisherHarness({**fixture, 'tags': list(tags)})
                try:
                    output = h.run()
                    tags.append(output['tag'])
                    results.append(output['tag'])
                except ValueError:
                    results.append('stale')

        first = threading.Thread(target=run, args=(fixtures[0], True))
        second = threading.Thread(target=run, args=(fixtures[1],))
        first.start()
        self.assertTrue(entered.wait(5))
        second.start()
        self.assertEqual([], results)
        release_first.set()
        first.join(5)
        second.join(5)
        self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(['v1.1.0', 'stale'], results)
        self.assertEqual(['v1.0.0', 'v1.1.0'], tags)

    def test_integrated_event_authority_token_and_native_create(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state = directory / 'api.json'
            client = directory / 'gh'
            client.write_text(
                '#!/usr/bin/env python3\n'
                'import json,os,sys\n'
                'from pathlib import Path\n'
                'p=Path(os.environ["FIXTURE_STATE"])\n'
                'd=json.loads(p.read_text())\n'
                'assert os.environ["GH_TOKEN"]=="installation-token-fixture"\n'
                'args=sys.argv[1:]\n'
                'assert args[:4]==["api","--method","POST","repos/GustavoPeixoto/php-qa-scope/git/refs"]\n'
                'assert len(args)==8 and args[4]==args[6]=="-f"\n'
                'ref=args[5].removeprefix("ref=")\n'
                'sha=args[7].removeprefix("sha=")\n'
                'd["requests"].append({"ref":ref,"sha":sha})\n'
                'code=1 if ref in d["refs"] else d["failure"]\n'
                'if not code:d["refs"][ref]=sha\n'
                'p.write_text(json.dumps(d))\n'
                'sys.exit(code)\n'
            )
            client.chmod(0o755)
            minted = []

            def pipeline(harness):
                if not eligible(harness.event):
                    return 'skipped'
                authority = harness.run()
                # Substitute only the external App action; actual workflow config is
                # checked separately, and actual authority/create code runs unchanged.
                minted.append('repository-scoped:contents-write')
                result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', CREATE],
                                        env={**os.environ, 'PATH': str(directory) + os.pathsep + os.environ['PATH'],
                                             'FIXTURE_STATE': str(state), 'GITHUB_REPOSITORY': REPOSITORY,
                                             'TAG': authority['tag'], 'MERGE_SHA': authority['sha'],
                                             'GH_TOKEN': 'installation-token-fixture'}, capture_output=True, text=True)
                self.assertNotIn('installation-token-fixture', result.stdout + result.stderr)
                return result.returncode

            preserved = {'refs/tags/v0.0.9': 'd' * 40}
            for failure in [0, 1, 22]:
                with self.subTest(failure=failure):
                    state.write_text(json.dumps({'refs': preserved, 'requests': [], 'failure': failure}))
                    h = PublisherHarness(FIXTURES[0])
                    self.assertEqual(failure, pipeline(h))
                    data = json.loads(state.read_text())
                    self.assertEqual([{'ref': 'refs/tags/v0.1.0', 'sha': SHA}], data['requests'])
                    self.assertEqual(preserved if failure else {**preserved, 'refs/tags/v0.1.0': SHA}, data['refs'])
            for existing_sha in [SHA, 'e' * 40]:
                # Model a competing ref appearing between enumeration and create.
                refs = {**preserved, 'refs/tags/v0.1.0': existing_sha}
                state.write_text(json.dumps({'refs': refs, 'requests': [], 'failure': 0}))
                self.assertEqual(1, pipeline(PublisherHarness(FIXTURES[0])))
                self.assertEqual(refs, json.loads(state.read_text())['refs'])
            before = len(minted)
            for fixture in [FIXTURES[1], FIXTURES[2]]:
                self.assertEqual('skipped', pipeline(PublisherHarness(fixture)))
            for tags in [['v0.1.0'], ['v0.2.0']]:
                with self.assertRaises(ValueError):
                    pipeline(PublisherHarness({**FIXTURES[0], 'tags': tags}))
            self.assertEqual(before, len(minted), 'Skipped/failed validation minted write credentials')

    def test_pr_origin_and_event_update_coverage(self):
        for origin, ok in [(REPOSITORY, True), ("fork/repo", False)]:
            with patch.dict(os.environ, {"HEAD_REPOSITORY": origin, "GITHUB_REPOSITORY": REPOSITORY}):
                if ok:
                    exec(compile(ORIGIN, "origin", "exec"), {})
                else:
                    with self.assertRaisesRegex(SystemExit, "same repository"):
                        exec(compile(ORIGIN, "origin", "exec"), {})
        for event in ["opened", "reopened", "synchronize", "ready_for_review"]:
            self.assertIn(event, PR_WORKFLOW)
        self.assertNotIn("paths:", PR_WORKFLOW)
        self.assertNotIn("paths-ignore:", PR_WORKFLOW)
        self.assertNotIn("secrets.", PR_WORKFLOW)
        self.assertNotIn("app-token", PR_WORKFLOW)
        job_header = PR_WORKFLOW.split("jobs:", 1)[1].split("    steps:", 1)[0]
        self.assertNotIn("    if:", job_header)
        self.assertIn("name: Validate Release Branch", job_header)
        self.assertIn("Ordinary PR; no release version required.", PR_WORKFLOW)
        self.assertIn("github.event.pull_request.head.sha", PR_WORKFLOW)
        self.assertNotIn("${{", block(PR_WORKFLOW, "- name: Check release origin"))

    def test_workflow_security_invariants(self):
        publisher = MERGE_WORKFLOW.split("  publish:", 1)[1]
        validation = MERGE_WORKFLOW.split("  publish:", 1)[0]
        self.assertNotIn("checkout@", publisher)
        self.assertNotIn("tools/release", publisher)
        self.assertNotIn("secrets.", validation)
        self.assertIn("needs: validate", publisher)
        gates = re.findall(r'    if: >-\n((?:      .+\n)+)', MERGE_WORKFLOW)
        self.assertEqual(2, len(gates))
        self.assertEqual(gates[0], gates[1])
        self.assertIn("group: protected-release-publication\n      cancel-in-progress: false", publisher)
        self.assertNotIn("${{", AUTHORITY)
        self.assertLess(publisher.index("id: authority"), publisher.index("id: app-token"))
        self.assertIn("repositories: ${{ github.event.repository.name }}", publisher)
        self.assertIn("permission-contents: write", publisher)
        self.assertEqual(1, publisher.count("steps.app-token.outputs.token"))
        self.assertIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", publisher)
        self.assertIn("pull-requests: read", publisher)
        for source in [PR_WORKFLOW, MERGE_WORKFLOW]:
            self.assertIn("permissions:\n  contents: read", source)
            self.assertNotIn("pull_request_target:", source)
            for action in re.findall(r"uses: (.+)", source):
                self.assertRegex(action, r"^[\w/-]+@[0-9a-f]{40} # v?[0-9]")
            self.assertEqual(source.count("checkout@"), source.count("persist-credentials: false"))
            self.assertIn("tools: composer:2.10.3", source)
            self.assertIn("composer --no-plugins --no-scripts validate --strict --no-check-version", source)
        self.assertEqual({"validate-release.yml", "create-release-tag.yml"}, {p.name for p in WORKFLOWS.glob("*.yml")})


if __name__ == "__main__":
    unittest.main()
