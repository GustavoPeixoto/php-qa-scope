"""Keep the PR workflow's scheduling, authority, and aggregate contracts explicit."""

import ast
from pathlib import Path
import re
import unittest

from git_hooks import reports


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / ".github/workflows/qa.yml").read_text()


class WorkflowTests(unittest.TestCase):
    def test_universal_pr_events_and_merge_revision(self):
        trigger = SOURCE.split("on:\n", 1)[1].split("permissions:", 1)[0]
        self.assertIn("pull_request:", trigger)
        self.assertIn("types: [opened, reopened, synchronize, ready_for_review, edited]", trigger)
        for prohibited in ("branches:", "paths:", "branches-ignore:", "paths-ignore:", "pull_request_target"):
            self.assertNotIn(prohibited, SOURCE)
        self.assertNotRegex(SOURCE, r"(?:head\.(?:ref|sha|repo)|\.draft)")
        checkouts = re.findall(r"ref: (.+)", SOURCE)
        self.assertEqual(["${{ github.sha }}"] * 2, checkouts)
        self.assertEqual(2, SOURCE.count("persist-credentials: false"))
        self.assertEqual(2, SOURCE.count("REVISION: ${{ github.sha }}"))
        self.assertNotIn("refs/pull/", SOURCE)

    def test_matrix_independence_and_cancellation(self):
        matrix = re.search(r"check: (\[.+\])", SOURCE)[1]
        values = ast.literal_eval(re.sub(r"([\w-]+)", r"'\1'", matrix))
        self.assertEqual(set(reports.CHECKS), set(values))
        self.assertEqual(len(reports.CHECKS), len(values))
        self.assertIn("fail-fast: false", SOURCE)
        self.assertIn("group: ${{ github.workflow }}-${{ github.event.pull_request.number }}", SOURCE)
        self.assertIn("cancel-in-progress: true", SOURCE)
        self.assertEqual(2, SOURCE.count("timeout-minutes: 30"))
        self.assertEqual(2, SOURCE.count("runs-on: ubuntu-24.04"))

    def test_shared_tooling_locked_dependencies_and_read_only_authority(self):
        self.assertIn("dockerfile=docker/dev/Dockerfile", SOURCE)
        self.assertIn("dockerfile=docker/php/Dockerfile", SOURCE)
        self.assertIn('--target tooling --tag pr-qa-tooling .', SOURCE)
        self.assertIn("composer install --no-interaction --no-ansi --prefer-dist --no-progress", SOURCE)
        self.assertIn('source=$GITHUB_WORKSPACE,target=$GITHUB_WORKSPACE', SOURCE)
        self.assertIn('--tmpfs /tmp:rw,mode=1777', SOURCE)
        self.assertIn('"$(id -u):$(id -g)"', SOURCE)
        self.assertIn("permissions:\n  contents: read", SOURCE)
        for prohibited in ("secrets.", "github.token", "GH_TOKEN", "GITHUB_TOKEN", "write", "docker compose", ".env", "setup-codex", "--no-dev", "--ignore-platform", "composer update", "setup-node", "openspec@", "php:", "composer:"):
            self.assertNotIn(prohibited, SOURCE)
        for action in re.findall(r"uses: (.+)", SOURCE):
            self.assertRegex(action, r"^actions/[a-z-]+@[a-f0-9]{40}(?: # .*)?$")

    def test_evidence_upload_and_gate_cannot_mask_failure(self):
        upload = SOURCE.split("- name: Retain available QA evidence", 1)[1].split("  required:", 1)[0]
        self.assertIn("if: ${{ always() }}", upload)
        self.assertIn("name: qa-${{ matrix.check }}", upload)
        self.assertIn("if-no-files-found: error", upload)
        self.assertIn("logs/pr-qa/results/${{ matrix.check }}/", upload)
        self.assertIn("logs/pr-qa/outcomes/${{ matrix.check }}.json", upload)
        self.assertNotIn("retention-days:", SOURCE)  # Repository-configured retention.
        gate = SOURCE.split("  required:\n", 1)[1]
        self.assertIn("name: QA Required\n", gate)
        self.assertIn("needs: checks", gate)
        self.assertIn("if: ${{ always() }}", gate)
        self.assertIn("UPSTREAM_RESULT: ${{ needs.checks.result }}", gate)
        self.assertIn('--upstream-result "$UPSTREAM_RESULT"', gate)
        self.assertIn("pattern: qa-*", gate)
        self.assertIn("path: logs/pr-qa/downloaded", gate)
        self.assertNotIn("run-id:", gate)
        self.assertNotIn("merge-multiple: true", gate)
        self.assertNotIn("continue-on-error", SOURCE)

    def test_release_check_keeps_existing_skip_rules(self):
        release = (ROOT / ".github/workflows/validate-release.yml").read_text()
        self.assertIn("name: Validate Release Branch", release)
        self.assertIn("if: startsWith(github.event.pull_request.head.ref, 'release/')", release)
        self.assertIn("branches: [main]", release)
        self.assertNotIn("QA Required", release)


if __name__ == "__main__":
    unittest.main()
