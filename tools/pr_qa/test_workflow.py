"""Keep PR scheduling, authority, uploads, and individual check identities explicit."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest

from git_hooks import reports


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / ".github/workflows/qa.yml").read_text()
STEPS = dict(block.split("\n", 1) for block in re.split(r"^      - name: ", SOURCE, flags=re.MULTILINE)[1:])


class WorkflowTests(unittest.TestCase):
    def test_universal_pr_events_and_merge_revision(self):
        trigger = SOURCE.split("on:\n", 1)[1].split("permissions:", 1)[0]
        self.assertIn("pull_request:", trigger)
        self.assertIn("types: [opened, reopened, synchronize, ready_for_review, edited]", trigger)
        for prohibited in ("branches:", "paths:", "branches-ignore:", "paths-ignore:", "pull_request_target"):
            self.assertNotIn(prohibited, SOURCE)
        self.assertNotRegex(SOURCE, r"(?:head\.(?:ref|sha|repo)|\.draft)")
        checkouts = re.findall(r"ref: (.+)", SOURCE)
        self.assertEqual(["${{ github.sha }}"], checkouts)
        self.assertEqual(1, SOURCE.count("persist-credentials: false"))
        self.assertEqual(1, SOURCE.count("REVISION: ${{ github.sha }}"))
        self.assertNotIn("refs/pull/", SOURCE)

    def test_matrix_independence_and_cancellation(self):
        matrix = re.search(r"check: (\[.+\])", SOURCE)[1]
        values = ast.literal_eval(re.sub(r"([\w-]+)", r"'\1'", matrix))
        self.assertEqual(set(reports.CHECKS), set(values))
        self.assertEqual(len(reports.CHECKS), len(values))
        self.assertIn("fail-fast: false", SOURCE)
        self.assertIn("group: ${{ github.workflow }}-${{ github.event.pull_request.number }}", SOURCE)
        self.assertIn("cancel-in-progress: true", SOURCE)
        self.assertEqual(1, SOURCE.count("timeout-minutes: 30"))
        self.assertEqual(1, SOURCE.count("runs-on: ubuntu-24.04"))
        jobs = re.findall(r"^  ([\w-]+):$", SOURCE.split("jobs:\n", 1)[1], re.MULTILINE)
        self.assertEqual(["checks"], jobs)
        self.assertIn("name: QA (${{ matrix.check }})", SOURCE)

    def test_shared_tooling_locked_dependencies_and_read_only_authority(self):
        self.assertIn("TOOLING_DOCKERFILE: ${{ matrix.check == 'openspec' && 'docker/dev/Dockerfile' || 'docker/php/Dockerfile' }}", SOURCE)
        self.assertIn('--target tooling --tag pr-qa-tooling .', SOURCE)
        self.assertIn("composer install --no-interaction --no-ansi --prefer-dist --no-progress", SOURCE)
        self.assertIn('source=$GITHUB_WORKSPACE,target=$GITHUB_WORKSPACE', SOURCE)
        self.assertIn('--tmpfs /tmp:rw,mode=1777', SOURCE)
        self.assertIn('"$(id -u):$(id -g)"', SOURCE)
        self.assertIn("permissions:\n  contents: read", SOURCE)
        for prohibited in ("secrets.", "github.token", "GH_TOKEN", "GITHUB_TOKEN", "write", "docker compose", ".env", "setup-codex", "--no-dev", "--ignore-platform", "composer update", "setup-node", "openspec@", "php:", "composer:"):
            self.assertNotIn(prohibited, SOURCE)
        for action in re.findall(r"uses: (.+)", SOURCE):
            self.assertRegex(action, r"^(?:actions/[a-z-]+(?:/(?:restore|save))?|docker/setup-buildx-action)@[a-f0-9]{40}(?: # .*)?$")

    def test_cache_identity_scope_and_publication_order(self):
        keys = STEPS["Prepare cache keys"]
        self.assertIn("pr-qa-tooling-v1-${{ runner.os }}-${{ runner.arch }}-${{ env.TOOLING_FAMILY }}-${{ hashFiles(env.TOOLING_DOCKERFILE) }}", keys)
        self.assertIn("TOOLING_FAMILY: ${{ matrix.check == 'openspec' && 'node' || 'php' }}", SOURCE)
        self.assertIn("pr-qa-composer-v1-${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('docker/php/Dockerfile') }}-", keys)
        self.assertIn("hashFiles('composer.json', 'composer.lock')", keys)
        self.assertNotIn("github.sha", keys)
        self.assertNotIn("github.run", keys)
        self.assertNotIn("**", keys)
        cache_steps = {name: body for name, body in STEPS.items() if "uses: actions/cache/" in body}
        self.assertEqual(4, len(cache_steps))
        for name, body in STEPS.items():
            self.assertEqual(name in cache_steps, "continue-on-error: true" in body, name)
            if name in cache_steps:
                self.assertNotIn("vendor", body)
                self.assertNotIn("logs/", body)
            if "Composer downloads" in name:
                self.assertIn("matrix.check != 'openspec'", body)
            if name.startswith("Save "):
                self.assertIn("outputs.cache-hit != 'true'", body)
        self.assertIn("restore-keys: ${{ steps.cache_keys.outputs.composer-prefix }}", STEPS["Restore Composer downloads"])
        names = list(STEPS)
        self.assertLess(names.index("Checkout proposed integration"), names.index("Prepare cache keys"))
        for prepare, save in (("Build shared tooling", "Save tooling layers"), ("Install locked PHP development dependencies", "Save Composer downloads")):
            self.assertLess(names.index(prepare), names.index(save))
            self.assertLess(names.index(save), names.index("Run native validation"))

    def test_per_check_upload_cannot_mask_failure(self):
        upload = SOURCE.split("- name: Retain available QA evidence", 1)[1]
        self.assertIn("if: ${{ always() }}", upload)
        self.assertIn("name: qa-${{ matrix.check }}", upload)
        self.assertIn("if-no-files-found: error", upload)
        self.assertIn("logs/pr-qa/results/${{ matrix.check }}/", upload)
        self.assertIn("logs/pr-qa/outcomes/${{ matrix.check }}.json", upload)
        self.assertNotIn("retention-days:", SOURCE)  # Repository-configured retention.
        self.assertNotIn("success()", upload)
        for removed in ("QA Required", "download-artifact", "--aggregate", "--upstream-result"):
            self.assertNotIn(removed, SOURCE)
        self.assertNotIn("continue-on-error", upload)
        for name in ("Build shared tooling", "Install locked PHP development dependencies", "Run native validation"):
            self.assertNotIn("continue-on-error", STEPS[name])

    def test_release_check_keeps_existing_skip_rules(self):
        release = (ROOT / ".github/workflows/validate-release.yml").read_text()
        self.assertIn("name: Validate Release Branch", release)
        self.assertIn("if: startsWith(github.event.pull_request.head.ref, 'release/')", release)
        self.assertIn("branches: [main]", release)
        self.assertNotIn("QA Required", release)


class PreparationShellTests(unittest.TestCase):
    """Execute workflow shell blocks with controlled Docker success and failure."""

    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name)
        self.cache = self.root / "cache"
        self.cache.mkdir()
        self.logs = self.root / "logs/pr-qa/results/test"
        self.logs.mkdir(parents=True)
        binaries = self.root / "bin"
        binaries.mkdir()
        docker = binaries / "docker"
        docker.write_text(textwrap.dedent("""\
            #!/usr/bin/env python3
            import json
            import os
            from pathlib import Path
            import sys
            args = sys.argv[1:]
            Path(os.environ['ARGV_LOG']).write_text(json.dumps(args))
            print('controlled Docker diagnostic')
            if args[:2] == ['buildx', 'build']:
                spec = args[args.index('--cache-to') + 1]
                dest = next(part[5:] for part in spec.split(',') if part.startswith('dest='))
                target = Path(dest)
                target.mkdir()
                (target / 'index.json').write_text('{}')
                (target / 'new-layer').touch()
            sys.exit(int(os.environ.get('DOCKER_TEST_EXIT', '0')))
            """))
        docker.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
            "CACHE_ROOT": str(self.cache),
            "CHECK_ID": "test",
            "TOOLING_DOCKERFILE": "docker/php/Dockerfile",
            "GITHUB_WORKSPACE": str(self.root),
            "ARGV_LOG": str(self.root / "argv.json"),
        }

    def run_step(self, name, code=0):
        script = textwrap.dedent(STEPS[name].split("        run: |\n", 1)[1])
        result = subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", script],
            cwd=self.root, env={**self.env, "DOCKER_TEST_EXIT": str(code)},
            text=True, capture_output=True, check=False,
        )
        args = json.loads((self.root / "argv.json").read_text())
        return result, args

    def test_cold_build_loads_image_and_exports_cache(self):
        result, args = self.run_step("Build shared tooling")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("--cache-from", args)
        self.assertIn("--load", args)
        self.assertEqual("pr-qa-tooling", args[args.index("--tag") + 1])
        self.assertTrue((self.cache / "tooling/new-layer").exists())
        self.assertFalse((self.cache / "tooling-next").exists())
        self.assertIn("controlled Docker diagnostic", (self.logs / "build.log").read_text())

    def test_warm_build_imports_layers_and_replaces_old_export(self):
        old = self.cache / "tooling"
        old.mkdir()
        (old / "index.json").write_text('{}')
        (old / "obsolete-layer").touch()
        result, args = self.run_step("Build shared tooling")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(f"type=local,src={old}", args[args.index("--cache-from") + 1])
        self.assertFalse((old / "obsolete-layer").exists())
        self.assertTrue((old / "new-layer").exists())

    def test_failed_build_is_fatal_and_keeps_restored_cache_and_log(self):
        old = self.cache / "tooling"
        old.mkdir()
        (old / "index.json").write_text('{}')
        (old / "old-layer").touch()
        result, _ = self.run_step("Build shared tooling", code=23)
        self.assertEqual(23, result.returncode)
        self.assertTrue((old / "old-layer").exists())
        self.assertFalse((old / "new-layer").exists())
        self.assertTrue((self.logs / "build.log").exists())

    def test_install_mounts_downloads_and_propagates_failure(self):
        for code in (0, 19):
            with self.subTest(code=code):
                result, args = self.run_step("Install locked PHP development dependencies", code=code)
                self.assertEqual(code, result.returncode, result.stderr)
                self.assertIn("COMPOSER_CACHE_DIR=/composer-cache", args)
                self.assertIn("COMPOSER_HOME=/tmp/composer", args)
                self.assertIn(f"type=bind,source={self.cache}/composer,target=/composer-cache", args)
                self.assertIn(f"type=bind,source={self.root},target={self.root}", args)
                self.assertIn("--user", args)
                self.assertTrue((self.cache / "composer").is_dir())
                self.assertIn("controlled Docker diagnostic", (self.logs / "install.log").read_text())


if __name__ == "__main__":
    unittest.main()
