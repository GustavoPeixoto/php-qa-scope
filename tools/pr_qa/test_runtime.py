"""Opt-in probes against the actual shared tooling and development images."""

import json
import os
from pathlib import Path
import re
import subprocess
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get("PR_QA_RUNTIME_TESTS") == "1", "Requires four built QA images")
class RuntimeTests(unittest.TestCase):
    def run_image(self, image, *argv, user=None, mounts=(), network=None):
        command = ["docker", "create"]
        if user:
            command += ["--user", user]
        for mount in mounts:
            command += ["--mount", mount]
        if network:
            command += ["--network", network]
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
        version = re.search(r"^FROM node:(\d+\.\d+\.\d+)-bookworm AS tooling$", source, re.MULTILINE)[1]
        openspec = re.search(r"@fission-ai/openspec@([\d.]+)", source)[1]
        versions = []
        for stage in ("tooling", "development"):
            image = f"php-qa-scope-pr-node-{stage}"
            node = self.run_image(image, "node", "--version")
            self.assertEqual(f"v{version}", node)
            self.assertEqual(openspec, self.run_image(image, "openspec", "--version"))
            self.assertEqual(re.search(r"corepack@([\d.]+)", source)[1],
                             self.run_image(image, "corepack", "--version"))
            self.assertEqual(re.search(r"yarn@([\d.]+)", source)[1],
                             self.run_image(image, "yarn", "--version"))
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
        self.run_image(image, "bash", "-ec", '''
            for tool in gh codex context-mode setup-codex-context-mode setup-git-hooks python3; do
                command -v "$tool"
            done
        ''')
        self.assertTrue(self.run_image(image, "gh", "--version").startswith("gh version "))
        self.run_image(image, "sudo", "-n", "true")
        self.assertEqual(str(ROOT), self.run_image(image, "git", "config", "--system", "--get", "safe.directory"))

    def test_context_mode_bootstrap_is_idempotent(self):
        self.run_image("php-qa-scope-pr-node-development", "bash", "-ec", '''
            export CODEX_HOME="$(mktemp -d)"
            trap 'rm -rf "$CODEX_HOME"' EXIT
            printf '%s\\n' '{"fixture":"codex-runtime"}' > "$CODEX_HOME/auth.json"
            chmod 0600 "$CODEX_HOME/auth.json"
            sha256sum "$CODEX_HOME/auth.json" > "$CODEX_HOME/auth.sha256"
            setup-codex-context-mode
            sha256sum "$CODEX_HOME/config.toml" "$CODEX_HOME/hooks.json" > "$CODEX_HOME/setup.sha256"
            setup-codex-context-mode
            sha256sum --check "$CODEX_HOME/auth.sha256" "$CODEX_HOME/setup.sha256"
            python3 - <<'PY'
import json
import os
from pathlib import Path
import tomllib

home = Path(os.environ["CODEX_HOME"])
config = tomllib.loads((home / "config.toml").read_text())
assert config["mcp_servers"]["context-mode"]["command"] == "context-mode"
assert json.loads((home / "hooks.json").read_text())["hooks"]
PY
        ''', network="none")

    def test_shared_cli_state_survives_container_recreation(self):
        image = "php-qa-scope-pr-node-development"
        volumes = []
        mounts = []
        try:
            for kind, target in (("gh", "/home/dev/.config/gh"), ("codex", "/home/dev/.codex")):
                volume = f"php-qa-scope-{kind}-runtime-" + uuid.uuid4().hex
                created = subprocess.run(
                    ["docker", "volume", "create", "--label", "php-qa-scope.test=cli-state", volume],
                    check=True, capture_output=True, text=True).stdout.strip()
                self.assertEqual(volume, created)
                volumes.append(volume)
                mounts.append(f"type=volume,source={volume},target={target}")
            digest = self.run_image(image, "bash", "-ec", '''
                test "$(id -u)" != 0
                test "$GH_CONFIG_DIR" = "/home/$(id -un)/.config/gh"
                test "$(stat -c '%u:%g' "$GH_CONFIG_DIR")" = "$(id -u):$(id -g)"
                test "$(stat -c '%u:%g' "$HOME/.codex")" = "$(id -u):$(id -g)"
                test "$(stat -c '%a' "$GH_CONFIG_DIR")" = 700
                test ! -e "$GH_CONFIG_DIR/hosts.yml"
                test ! -e "$GH_CONFIG_DIR/config.yml"
                test ! -e "$HOME/.codex/auth.json"
                gh config set editor github-cli-runtime-fixture
                printf '%s\\n' 'github.com:' '    user: runtime-fixture' \\
                    '    oauth_token: synthetic-validation-only' \\
                    '    git_protocol: ssh' > "$GH_CONFIG_DIR/hosts.yml"
                printf '%s\\n' '{"fixture":"codex-runtime"}' > "$HOME/.codex/auth.json"
                chmod 0600 "$GH_CONFIG_DIR/hosts.yml" "$HOME/.codex/auth.json"
                sha256sum "$GH_CONFIG_DIR/hosts.yml" "$HOME/.codex/auth.json" | cut -d ' ' -f 1
            ''', mounts=mounts, network="none")
            self.assertRegex(digest, r"^[a-f0-9]{64}\n[a-f0-9]{64}$")
            restored = self.run_image(image, "bash", "-ec", '''
                test "$(stat -c '%u:%g' "$GH_CONFIG_DIR")" = "$(id -u):$(id -g)"
                test "$(stat -c '%u:%g' "$HOME/.codex")" = "$(id -u):$(id -g)"
                test "$(stat -c '%a' "$GH_CONFIG_DIR")" = 700
                test "$(stat -c '%a' "$GH_CONFIG_DIR/hosts.yml")" = 600
                test "$(stat -c '%a' "$HOME/.codex/auth.json")" = 600
                gh config get editor
                sha256sum "$GH_CONFIG_DIR/hosts.yml" "$HOME/.codex/auth.json" | cut -d ' ' -f 1
            ''', mounts=mounts, network="none")
            self.assertEqual(f"github-cli-runtime-fixture\n{digest}", restored)
        finally:
            for volume in reversed(volumes):
                subprocess.run(["docker", "volume", "rm", volume], check=True, capture_output=True)

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
