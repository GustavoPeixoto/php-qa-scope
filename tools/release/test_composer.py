"""Exercise the documented commands in the running PHP service, without dependencies."""

import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
COMMAND = shlex.split(os.environ.get("RELEASE_TEST_COMPOSER", "docker compose exec -T php composer"))
VALIDATE = ["--no-plugins", "--no-scripts", "validate", "--strict", "--no-check-version"]


class ComposerTests(unittest.TestCase):
    def test_strict_manifest_and_lock_fixtures(self):
        version = subprocess.run(COMMAND + ["--version"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn("Composer version 2.10.3", version.stdout)
        (ROOT / "tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="release-composer-", dir=ROOT / "tmp") as directory:
            directory = Path(directory)
            manifest_path = directory / "composer.json"
            marker = directory / "script-ran"
            manifest = {
                "name": "fixture/release", "description": "Release validation fixture", "license": "MIT",
                "version": "0.1.0", "require": {"php": ">=8.1"},
                "repositories": {"packagist.org": False},
                "scripts": {"pre-update-cmd": f"touch {marker}", "post-update-cmd": f"touch {marker}"},
            }

            def run(arguments):
                return subprocess.run(COMMAND + [f"--working-dir={directory}"] + arguments,
                                      cwd=ROOT, capture_output=True, text=True)

            def check(data, passed):
                manifest_path.write_text(json.dumps(data))
                result = run(VALIDATE)
                self.assertEqual(passed, result.returncode == 0, result.stdout + result.stderr)
                self.assertFalse(marker.exists(), "Composer executed package scripts")
                self.assertFalse((directory / "vendor").exists(), "Validation installed dependencies")

            check(manifest, True)
            without_suppression = run(["--no-plugins", "--no-scripts", "validate", "--strict"])
            self.assertNotEqual(0, without_suppression.returncode)
            self.assertIn("version", without_suppression.stdout + without_suppression.stderr)
            for mutate in [lambda d: d.update(name="invalid name"), lambda d: d.pop("description"),
                           lambda d: d.pop("license"), lambda d: d.update(unknown_property=True)]:
                invalid = copy.deepcopy(manifest)
                mutate(invalid)
                check(invalid, False)
            manifest_path.write_text("{")
            self.assertNotEqual(0, run(VALIDATE).returncode)
            manifest_path.write_text(json.dumps(manifest))
            # Build a dependency-free fixture lock; production validation never updates it.
            seed = run(["--no-plugins", "--no-scripts", "update", "--no-install", "--no-audit"])
            self.assertEqual(0, seed.returncode, seed.stdout + seed.stderr)
            check(manifest, True)
            before = json.loads((directory / "composer.lock").read_text())
            changed = {**manifest, "version": "0.2.0"}
            check(changed, False)
            repair = run(["--no-plugins", "--no-scripts", "update", "--lock", "--no-install"])
            self.assertEqual(0, repair.returncode, repair.stdout + repair.stderr)
            check(changed, True)
            after = json.loads((directory / "composer.lock").read_text())
            for key in ["packages", "packages-dev"]:
                self.assertEqual(before[key], after[key], "Lock repair changed dependencies")


if __name__ == "__main__":
    unittest.main()
