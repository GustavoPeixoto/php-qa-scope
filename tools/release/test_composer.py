"""Exercise shared PHP images and strict Composer fixtures without package dependencies."""

import copy
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOST_ROOT = os.environ.get("RELEASE_TEST_HOST_WORKSPACE", str(ROOT))
TOOLING_IMAGE = os.environ.get("RELEASE_TEST_TOOLING_IMAGE", "php-qa-scope-release-tooling")
DEVELOPMENT_IMAGE = os.environ.get("RELEASE_TEST_DEVELOPMENT_IMAGE", "php-qa-scope-release-development")
RUNTIME = ["docker", "run", "--rm", "--mount", f"type=bind,source={HOST_ROOT},target={ROOT}",
           "--workdir", str(ROOT), TOOLING_IMAGE]
COMMAND = shlex.split(os.environ["RELEASE_TEST_COMPOSER"]) if "RELEASE_TEST_COMPOSER" in os.environ else RUNTIME + ["composer"]
VALIDATE = ["--no-plugins", "--no-scripts", "validate", "--strict", "--no-check-version"]


class ComposerTests(unittest.TestCase):
    def test_shared_runtime_and_development_contract(self):
        dockerfile = (ROOT / "docker/php/Dockerfile").read_text()
        php = re.findall(r"^FROM php:([0-9.]+)-", dockerfile, re.MULTILINE)
        composer = re.findall(r"^COPY --from=composer:([0-9.]+) ", dockerfile, re.MULTILINE)
        self.assertEqual(1, len(php), "Expected one shared PHP version declaration")
        self.assertEqual(1, len(composer), "Expected one shared Composer version declaration")
        versions = []
        for image, xdebug in [(TOOLING_IMAGE, False), (DEVELOPMENT_IMAGE, True)]:
            runtime = ["docker", "run", "--rm", "--env", "XDEBUG_MODE=off", image]
            result = subprocess.run(runtime + ["php", "-r", 'echo json_encode([PHP_VERSION, extension_loaded("xdebug")]);'],
                                    capture_output=True, text=True, check=True)
            version, loaded = json.loads(result.stdout)
            self.assertEqual(php[0], version)
            self.assertEqual(xdebug, loaded)
            output = subprocess.run(runtime + ["composer", "--version"], capture_output=True, text=True, check=True).stdout
            self.assertIn(f"Composer version {composer[0]} ", output)
            versions.append((version, output.splitlines()[0]))
        self.assertEqual(versions[0], versions[1])
        username = re.search(r"^ARG USERNAME=(.+)$", dockerfile, re.MULTILINE).group(1)
        result = subprocess.run(["docker", "run", "--rm", DEVELOPMENT_IMAGE, "sh", "-ec",
                                 'test -w "$PWD"; test "$PWD" = "$WORKSPACE_DIR"; id -un; pwd'],
                                capture_output=True, text=True, check=True)
        self.assertEqual([username, str(ROOT)], result.stdout.splitlines())

    def test_strict_manifest_and_lock_fixtures(self):
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
