"""Opt-in probes against the actual shared tooling and development images."""

import json
import os
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get("PR_QA_RUNTIME_TESTS") == "1", "Requires four built QA images")
class RuntimeTests(unittest.TestCase):
    def run_image(self, image, *argv, user=None):
        command = ["docker", "create"]
        if user:
            command += ["--user", user]
        container = subprocess.run(command + [image, *argv], check=True,
                                   capture_output=True, text=True).stdout.strip()
        if not re.fullmatch(r"[a-f0-9]{64}", container):
            raise ValueError("Missing runtime probe container identity")
        try:
            subprocess.run(["docker", "start", container], check=True, capture_output=True)
            subprocess.run(["docker", "wait", container], check=True, capture_output=True)
            state = json.loads(subprocess.run(
                ["docker", "inspect", "--format", "{{json .State}}", container],
                check=True, capture_output=True, text=True).stdout)
            # Attached clients can lose a short process's output. Read retained
            # logs after termination instead of treating empty stdout as evidence.
            output = subprocess.run(["docker", "logs", container], check=True,
                                    capture_output=True, text=True)
            self.assertEqual("exited", state["Status"])
            self.assertEqual(0, state["ExitCode"], output.stdout + output.stderr)
            self.assertFalse(state["Error"] or state["OOMKilled"])
            return output.stdout.strip()
        finally:
            subprocess.run(["docker", "rm", "--force", container], check=True, capture_output=True)

    def test_node_development_inherits_tooling_and_configuration(self):
        source = (ROOT / "docker/dev/Dockerfile").read_text()
        major = re.search(r"javascript-node:(\d+)-", source)[1]
        openspec = re.search(r"@fission-ai/openspec@([\d.]+)", source)[1]
        versions = []
        for stage in ("tooling", "development"):
            image = f"php-qa-scope-pr-node-{stage}"
            node = self.run_image(image, "node", "--version")
            self.assertTrue(node.startswith(f"v{major}."))
            self.assertEqual(openspec, self.run_image(image, "openspec", "--version"))
            self.run_image(image, "corepack", "--version")
            versions.append(node)
        self.assertEqual(*versions)
        image = "php-qa-scope-pr-node-development"
        username = re.search(r"^ARG USERNAME=(.+)$", source, re.MULTILINE)[1]
        self.assertEqual(username, self.run_image(image, "id", "-un"))
        self.assertEqual(re.search(r"lefthook@([\d.]+)", source)[1], self.run_image(image, "lefthook", "version"))
        for user in (username, "root"):
            self.assertEqual("custom", self.run_image(image, "openspec", "config", "get", "profile", user=user))
            workflows = json.loads(self.run_image(image, "openspec", "config", "get", "workflows", user=user))
            self.assertEqual(["propose", "explore", "apply", "update", "sync", "archive", "verify"], workflows)
        self.run_image(image, "bash", "-ec", 'for tool in codex context-mode headroom setup-codex-context-mode setup-codex-headroom setup-git-hooks start-headroom-proxy; do command -v "$tool"; done')
        self.run_image(image, "sudo", "-n", "true")
        self.assertEqual(str(ROOT), self.run_image(image, "git", "config", "--system", "--get", "safe.directory"))

    def test_php_shared_versions_and_development_isolation(self):
        source = (ROOT / "docker/php/Dockerfile").read_text()
        php = re.search(r"FROM php:([\d.]+)-", source)[1]
        composer = re.search(r"COPY --from=composer:([\d.]+)", source)[1]
        versions = []
        for stage in ("tooling", "development"):
            image = f"php-qa-scope-pr-php-{stage}"
            version = json.loads(self.run_image(image, "php", "-r", 'echo json_encode([PHP_VERSION, extension_loaded("xdebug")]);'))
            self.assertEqual([php, stage == "development"], version)
            self.assertTrue(self.run_image(image, "composer", "--version").startswith(f"Composer version {composer} ") or
                            self.run_image(image, "composer", "--version").startswith(f"Composer {composer} "))
            self.run_image(image, "unzip", "-v")
            versions.append(version[0])
        self.assertEqual(*versions)
        self.assertEqual("dev", self.run_image("php-qa-scope-pr-php-development", "id", "-un"))
        self.assertEqual(str(ROOT), self.run_image("php-qa-scope-pr-php-development", "sh", "-ec", 'test -w "$PWD"; test "$PWD" = "$WORKSPACE_DIR"; pwd'))


if __name__ == "__main__":
    unittest.main()
