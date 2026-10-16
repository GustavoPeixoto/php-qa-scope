"""Pinned dispatcher, installed launchers, and isolated seven-job execution."""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import tarfile
import time
import uuid
import unittest

from test_preflight import repository

PROJECT = Path(__file__).resolve().parents[2]
LEFTHOOK = os.environ.get("QA_HOOKS_TEST_LEFTHOOK") or shutil.which("lefthook")
if LEFTHOOK:
    LEFTHOOK = str(Path(LEFTHOOK).absolute())

FAKE_DOCKER = (PROJECT / "tools/git_hooks/fake_docker_fixture.py").read_text()


def assert_layout(case, run, summary, complete=True):
    """Check the agreed on-disk contract independently of production helpers."""
    case.assertEqual(summary["schema_version"], 4)
    case.assertFalse(list((run / "results").glob("*.json")))
    case.assertFalse(list((run / "containers").glob("*.json")))
    case.assertFalse((run / "runner.diagnostics.log").exists())
    for check in summary["validations"]:
        key = check["validation_id"]
        filename = "result.log" if key == "qa-scope" else ("result.junit.xml" if key == "test" else "result.json")
        report = f"results/{key}/{filename}"
        log = f"results/{key}/execution.log"
        case.assertEqual((check["report"], check["diagnostics"]), (report, log))
        case.assertFalse((run / f"{key}.diagnostics.log").exists())
        case.assertFalse((run / f"{key}.stdout.log").exists())
        job = run / "jobs" / f"{key}.json"
        if complete:
            for path in (run / report, run / log, job, run / "runner.log", run / "runtime.json",
                         run / "processes/coordinator.json", run / f"processes/local/{key}.json"):
                case.assertTrue(path.is_file(), str(path))
        if job.exists():
            record = json.loads(job.read_text())
            case.assertEqual((record["execution_id"], record["validation_id"]), (run.name, key))
            case.assertEqual((record["report"], record["diagnostics"]), (report, log))
        directory = run / "containers" / key
        if key == "openspec":
            case.assertEqual(check["execution_backend"], "dev-process")
            case.assertIsNone(check["container_id"])
            case.assertEqual(check["container_cleanup"], "not_applicable")
            case.assertFalse(directory.exists())
            continue
        case.assertEqual(check["execution_backend"], "php-container")
        if complete:
            for filename in ("metadata.json", "create.done.json", "create.stdout.log", "create.stderr.log"):
                case.assertTrue((directory / filename).is_file(), str(directory / filename))
            case.assertEqual(json.loads((directory / "metadata.json").read_text())["cleanup"], "removed")
        for filename in ("metadata.json", "create.done.json"):
            if (directory / filename).exists():
                case.assertIsInstance(json.loads((directory / filename).read_text()), dict)
        local = run / "processes/local" / f"{key}.json"
        if local.exists():
            for child in json.loads(local.read_text())["children"]:
                if child.get("receipt"):
                    case.assertEqual(child["receipt"], str(directory / "create.done.json"))


def old_flat_run(root):
    old = root / "logs/prepush/20000101-000000-000"
    (old / "results").mkdir(parents=True)
    (old / "results/stan.json").write_text('{"old": "job"}')
    (old / "stan.json").write_text('{"old": "native"}')
    (old / "stan.diagnostics.log").write_text("old diagnostics")
    (old / "summary.json").write_text('{"schema_version": 3, "status": "passed"}')
    return old, {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}


@contextmanager
def assembled():
    with repository() as (root, git):
        shutil.copytree(PROJECT / "tools/git_hooks", root / "tools/git_hooks")
        shutil.copy2(PROJECT / "tools/git-hooks", root / "tools/git-hooks")
        shutil.copy2(PROJECT / "lefthook.yml", root / "lefthook.yml")
        shutil.copytree(PROJECT / "openspec", root / "openspec")
        for name in ("docker-compose.yml", "composer.json", "php-qa-scope.yml", "phpcs.xml",
                     "php-cs-fixer.dist.php", "phpmd.xml", "phpstan.neon", "phpunit.xml.dist"):
            shutil.copy2(PROJECT / name, root / name)
        git("add", ".")
        git("commit", "-m", "automation")
        # Fixtures live outside the checkout so even untracked cleanliness is real.
        with tempfile.TemporaryDirectory() as bin_dir:
            bin_path = Path(bin_dir)
            # Node resolves the real entrypoint, preserving npm's relative imports.
            os.symlink(LEFTHOOK, bin_path / "lefthook")
            (bin_path / "docker").write_text(FAKE_DOCKER)
            (bin_path / "docker").chmod(0o755)
            shutil.copy2(PROJECT / "tools/git_hooks/fake_openspec_fixture.py", bin_path / "openspec")
            (bin_path / "openspec").chmod(0o755)
            env = dict(os.environ, PATH=str(bin_path) + os.pathsep + os.environ["PATH"],
                       QA_HOOKS_SERVICE="dev", LEFTHOOK_OUTPUT="meta,execution,summary",
                       FIXTURE_ENGINE=str(bin_path / "engine"))
            try:
                yield root, git, env
            finally:
                from git_hooks import execution
                for actor in (bin_path / "engine/actors").glob("*.json"):
                    execution.signal_owned(json.loads(actor.read_text()), signal.SIGKILL, True)


@unittest.skipUnless(LEFTHOOK, "Install pinned Lefthook or set QA_HOOKS_TEST_LEFTHOOK")
class HookIntegrationTests(unittest.TestCase):
    def test_real_openspec_cli_valid_specs_unchecked_tasks_and_invalid_delta(self):
        cli = shutil.which("openspec")
        if not cli:
            self.skipTest("OpenSpec 1.14.0 is required")
        self.assertEqual(subprocess.check_output([cli, "--version"]).decode().strip(), "1.14.0")
        with assembled() as (root, git, env):
            fake = Path(env["PATH"].split(os.pathsep)[0]) / "openspec"
            fake.unlink()
            fake.symlink_to(cli)
            for invalid in (False, True):
                if invalid:
                    change = root / "openspec/changes/invalid-fixture"
                    spec = change / "specs/fixture/spec.md"
                    spec.parent.mkdir(parents=True)
                    spec.write_text("## ADDED Requirements\n\n### Requirement: Invalid fixture\nThe system SHALL reject this missing-scenario fixture.\n")
                    (change / "proposal.md").write_text("## Why\nIntentional validation failure.\n")
                    (change / "tasks.md").write_text("- [ ] Keep this task unchecked.\n")
                    git("add", "openspec")
                    git("commit", "-m", "intentional invalid delta")
                result = subprocess.run([root / "tools/git-hooks", "pre-push", "manual"],
                    cwd=root, env=env, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, int(invalid), result.stdout + result.stderr)
                run = max(root.glob("logs/prepush/*"))
                summary = json.loads((run / "summary.json").read_text())
                local = summary["validations"][-1]
                self.assertEqual(local["status"], "failed" if invalid else "passed")
                self.assertTrue(local["report_valid"])
                self.assertEqual(local["exit_code"], int(invalid))
                bulk = json.loads((run / local["report"]).read_text())
                self.assertEqual(bulk["root"]["path"], str(root))
                self.assertTrue(any(i["type"] == "spec" for i in bulk["items"]))
                self.assertTrue(any(i["id"] == "configure-git-qa-hooks" for i in bulk["items"]))
                self.assertEqual(git("status", "--porcelain"), "")
                assert_layout(self, run, summary)

    def test_openspec_findings_and_bad_output_collect_all_seven(self):
        for mode in ("passed", "failed", "malformed"):
            with assembled() as (root, git, env):
                result = subprocess.run([root / "tools/git-hooks", "pre-push", "manual"],
                    cwd=root, env=dict(env, FIXTURE_OPENSPEC=mode), capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0 if mode == "passed" else 1, result.stdout + result.stderr)
                run = max(root.glob("logs/prepush/*"))
                summary = json.loads((run / "summary.json").read_text())
                self.assertEqual(len(summary["validations"]), 7)
                local = summary["validations"][-1]
                self.assertEqual(local["validation_id"], "openspec")
                self.assertEqual(local["report_valid"], mode != "malformed")
                self.assertTrue(all(c["status"] == "passed" for c in summary["validations"][:-1]))
                self.assertEqual(local["exit_code"], 1 if mode == "failed" else 0)
                self.assertFalse((run / "containers/openspec").exists())
                if mode == "malformed":
                    self.assertTrue((run / "results/openspec/stdout.log").is_file())

    def test_pin_install_only_prepush_repeat_and_conflicts(self):
        self.assertEqual(subprocess.check_output([LEFTHOOK, "version"]).decode().strip(), "2.1.16")
        with assembled() as (root, git, env):
            hooks = root / ".git/custom-hooks"
            hooks.mkdir()
            (hooks / "commit-msg").write_text("unrelated")
            git("config", "core.hooksPath", str(hooks))
            setup = PROJECT / "docker/dev/bin/setup-git-hooks"
            for _ in range(2):
                result = subprocess.run([setup], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git("config", "core.hooksPath"), str(hooks))
            self.assertEqual((hooks / "commit-msg").read_text(), "unrelated")
            self.assertFalse((hooks / "pre-commit").exists())
            self.assertFalse((hooks / "qa-checks").exists())
            self.assertTrue((hooks / "pre-push").is_file())
            (hooks / "pre-push").write_text("#!/bin/sh\n# unrelated\n")
            result = subprocess.run([setup], cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unmanaged", result.stderr)
            self.assertEqual((hooks / "pre-push").read_text(), "#!/bin/sh\n# unrelated\n")

    def test_installed_launcher_forwards_stdin_and_opaque_arguments(self):
        with assembled() as (root, git, env):
            probe = '''#!/usr/bin/env python3
import json, os, pathlib, sys
pathlib.Path('logs/probe.json').write_text(json.dumps({
 'stdin': sys.stdin.read(), 'args': sys.argv[1:],
 'remote': os.environ['QA_HOOKS_REMOTE_NAME'],
 'location': os.environ['QA_HOOKS_REMOTE_LOCATION'],
 'git_mode': os.environ['QA_HOOKS_GIT_PUSH']}))
'''
            (root / "tools/git-hooks").write_text(probe)
            (root / "logs").mkdir()
            setup = subprocess.run([PROJECT / "docker/dev/bin/setup-git-hooks"], cwd=root,
                                   env=env, capture_output=True)
            self.assertEqual(setup.returncode, 0, setup.stderr)
            hook = root / ".git/hooks/pre-push"
            location = "remote path 'quote' $(touch SHOULD_NOT_EXIST)"
            result = subprocess.run([hook, "origin", location], cwd=root, env=env,
                                    input="four field input record\n", capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads((root / "logs/probe.json").read_text())
            self.assertEqual(data["stdin"], "four field input record\n")
            self.assertEqual(data["remote"], "origin")
            self.assertEqual(data["location"], location)
            self.assertEqual(data["git_mode"], "1")
            self.assertNotIn("QA_HOOKS_GIT_PUSH", env)
            self.assertEqual(data["args"][:2], ["boundary", "git"])
            self.assertTrue(data["args"][2].isdecimal())
            self.assertFalse((root / "SHOULD_NOT_EXIST").exists())
            # An unavailable explicit dispatcher must fail, without native fallback.
            with tempfile.TemporaryDirectory() as directory:
                for executable in ("sh", "git", "uname", "sed", "grep", "dirname", "head", "tr", "awk", "node"):
                    found = shutil.which(executable)
                    if found:
                        os.symlink(found, Path(directory) / executable)
                missing = dict(env, PATH=directory, LEFTHOOK_BIN=str(Path(directory) / "lefthook"))
                result = subprocess.run([hook, "origin", "remote"], cwd=root, env=missing,
                                        input="", capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("lefthook", (result.stdout + result.stderr).lower())
            # Installed dispatcher finds the entrypoint but a missing Python fails it.
            with tempfile.TemporaryDirectory() as directory:
                for executable in ("sh", "git", "uname", "sed", "grep", "dirname", "head", "tr", "awk", "node"):
                    found = shutil.which(executable)
                    if found:
                        os.symlink(found, Path(directory) / executable)
                os.symlink(LEFTHOOK, Path(directory) / "lefthook")
                result = subprocess.run([hook, "origin", "remote"], cwd=root,
                                        env=dict(env, PATH=directory), input="", capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("python3", (result.stdout + result.stderr).lower())
            # The wrapper itself needs Node; the launcher can use its native fallback.
            with Path(LEFTHOOK).open("rb") as executable:
                npm_wrapper = executable.readline().strip() == b"#!/usr/bin/env node"
            if npm_wrapper:
                with tempfile.TemporaryDirectory() as directory:
                    for executable in ("sh", "git", "uname", "sed", "grep", "dirname", "head", "tr", "awk", "python3"):
                        found = shutil.which(executable)
                        if found:
                            os.symlink(found, Path(directory) / executable)
                    os.symlink(LEFTHOOK, Path(directory) / "lefthook")
                    result = subprocess.run([Path(directory) / "lefthook", "version"], cwd=root,
                                            env=dict(env, PATH=directory), input="", capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("node", (result.stdout + result.stderr).lower())

    def test_real_parallel_group_all_results_after_failure_and_overlap(self):
        with assembled() as (root, git, env):
            oid = git("rev-parse", "HEAD")
            row = f"refs/heads/main {oid} refs/heads/review {'0'*40}\n"
            before = git("status", "--porcelain"), git("write-tree"), git("stash", "list")
            processes = [subprocess.Popen([root / "tools/git-hooks", "pre-push"], cwd=root,
                                           env=dict(env, QA_TEST_FAIL=fail), stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                         for fail in ("", "stan")]
            for process in processes:
                process.stdin.write(row)
                process.stdin.close()
                process.stdin = None
            outputs = [process.communicate(timeout=45) for process in processes]
            self.assertEqual([p.returncode for p in processes], [0, 1], outputs)
            runs = list(root.glob("logs/prepush/*"))
            self.assertEqual(len(runs), 2)
            statuses = []
            for run in runs:
                summary = json.loads((run / "summary.json").read_text())
                statuses.append(summary["status"])
                self.assertEqual(len(summary["validations"]), 7)
                self.assertEqual(len(list(run.glob("*.started"))), 6)
                self.assertTrue(all(c["report_valid"] for c in summary["validations"]))
                self.assertTrue(all((run / c["report"]).exists() for c in summary["validations"]))
                assert_layout(self, run, summary)
                if summary["status"] == "failed":
                    self.assertNotEqual(summary["lefthook_exit_code"], 0)
            self.assertEqual(sorted(statuses), ["failed", "passed"])
            self.assertIn("PHPStan", outputs[1][0])
            self.assertLess(len(outputs[1][0].splitlines()), 10)
            self.assertEqual(before, (git("status", "--porcelain"), git("write-tree"), git("stash", "list")))

    def test_rejected_empty_deletion_and_direct_group_paths(self):
        with assembled() as (root, git, env):
            oid = git("rev-parse", "HEAD")
            row = f"refs/heads/main {oid} refs/heads/main {'0'*40}\n"
            for stream, service, code in ((row, "php", 1), (row + row, "dev", 1),
                                          ("", "dev", 0),
                                          (f"(delete) {'0'*40} refs/heads/old {oid}\n", "dev", 0)):
                result = subprocess.run([root / "tools/git-hooks", "pre-push"], cwd=root,
                                        env=dict(env, QA_HOOKS_SERVICE=service), input=stream,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertFalse((root / "logs/prepush").exists())
            direct = subprocess.run([LEFTHOOK, "run", "qa-checks"], cwd=root, env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(direct.returncode, 0)
            self.assertIn("allocated pre-push run context", direct.stdout + direct.stderr)

    def test_real_catchable_interrupt_consolidates_incomplete_jobs(self):
        with assembled() as (root, git, env):
            oid = git("rev-parse", "HEAD")
            process = subprocess.Popen([root / "tools/git-hooks", "pre-push"], cwd=root,
                                       env=dict(env, QA_TEST_HOLD="1"), stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                process.stdin.write(f"HEAD {oid} refs/heads/main {'0'*40}\n")
                process.stdin.close()
                process.stdin = None
                deadline = time.monotonic() + 15
                while len(list(root.glob("logs/prepush/*/*.started"))) != 6:
                    self.assertIsNone(process.poll())
                    if time.monotonic() >= deadline:
                        self.fail("Scheduler did not reach six-job synchronization point")
                    time.sleep(.01)
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=15)
                self.assertEqual(process.returncode, 1, stdout + stderr)
                summary = json.loads(next(root.glob("logs/prepush/*/summary.json")).read_text())
                self.assertEqual(summary["status"], "interrupted")
                self.assertTrue(all(c["status"] in ("interrupted", "not_run") or
                                    (c["validation_id"] == "openspec" and c["status"] == "passed")
                                    for c in summary["validations"]))
                self.assertIn("Interrupted", stdout)
                self.assertEqual(git("status", "--porcelain"), "")
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=15)

    def test_distribution_archive_excludes_contributor_tooling(self):
        with assembled() as (root, git, env):
            shutil.copy2(PROJECT / ".gitattributes", root / ".gitattributes")
            (root / "conventions").mkdir()
            (root / "conventions/fixture.md").write_text("internal")
            (root / "logs").mkdir()
            (root / "logs/fixture.log").write_text("ignored")
            git("add", ".gitattributes", "conventions")
            git("add", "-f", "logs/fixture.log")
            git("commit", "-m", "archive fixture")
            archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=root)
            with tarfile.open(fileobj=io.BytesIO(archive)) as handle:
                names = handle.getnames()
            self.assertIn("composer.json", names)
            self.assertNotIn("lefthook.yml", names)
            self.assertFalse(any(name.startswith(("tools/", "logs/", "conventions/")) for name in names))


@unittest.skipUnless(os.environ.get("QA_HOOKS_NATIVE_ACCEPTANCE") == "1",
                     "Set QA_HOOKS_NATIVE_ACCEPTANCE=1 for isolated Docker/native-tool acceptance")
class NativeAcceptanceTests(unittest.TestCase):
    def test_real_dev_php_push_pass_and_intentional_native_rejection(self):
        """Use separate Compose services and a local bare remote, never real remotes."""
        def host_command(*args):
            return subprocess.check_output(args, cwd=PROJECT, stderr=subprocess.PIPE).decode().strip()
        dev_id = host_command("docker", "compose", "ps", "-q", "dev")
        php_id = host_command("docker", "compose", "ps", "-q", "php")
        dev = json.loads(host_command("docker", "inspect", dev_id))[0]
        php = json.loads(host_command("docker", "inspect", php_id))[0]
        mount = next(m for m in dev["Mounts"] if m["Destination"] == str(PROJECT))
        host_workspace = Path(mount["Source"])
        project_name = "qa-hooks-native-" + uuid.uuid4().hex[:12]
        evidence = PROJECT / "tmp/git-hooks-verification/native-reports"
        with tempfile.TemporaryDirectory(dir=PROJECT / "tmp", prefix="native-hooks-") as directory:
            base = Path(directory)
            root = base / "repository"
            root.mkdir()
            # Copy package inputs; dependency trees are mounted read-only separately.
            names = ("src", "tests", "bin", "tools", "conventions", "composer.json", "composer.lock",
                     "php-qa-scope.yml", "phpcs.xml", "php-cs-fixer.dist.php", "phpmd.xml", "phpstan.neon",
                     "phpunit.xml.dist", "lefthook.yml", ".gitignore", ".gitattributes", "openspec")
            for name in names:
                source = PROJECT / name
                if source.is_dir():
                    shutil.copytree(source, root / name)
                else:
                    shutil.copy2(source, root / name)
            dev_env = root / "docker/dev"
            dev_env.mkdir(parents=True)
            shutil.copy2(PROJECT / "docker/dev/.env.example", dev_env / ".env.example")
            subprocess.run(["bash", "tools/env", "dev"], cwd=root, check=True, capture_output=True)
            host_root = host_workspace / root.relative_to(PROJECT)
            services = {}
            dev_image = os.environ.get("QA_HOOKS_NATIVE_DEV_IMAGE", dev["Image"])
            for service, image in (("dev", dev_image), ("php", php["Image"])):
                services[service] = {
                    "image": image, "entrypoint": ["sh", "-c", "sleep infinity"],
                    "working_dir": "/php-qa-scope",
                    "volumes": [f"{host_root}:/php-qa-scope",
                                f"{host_workspace / 'vendor'}:/php-qa-scope/vendor:ro"],
                }
            services["dev"]["env_file"] = ["./docker/dev/.env"]
            services["dev"]["volumes"].append("/var/run/docker.sock:/var/run/docker.sock")
            # A newly created fixture lacks the Dev Container feature's socket-group setup.
            socket_gid = host_command("docker", "run", "--rm", "-v",
                                      "/var/run/docker.sock:/var/run/docker.sock",
                                      "--entrypoint", "stat", dev_image, "-L", "-c", "%g", "/var/run/docker.sock")
            services["dev"]["group_add"] = [socket_gid]
            config = {"name": project_name, "services": services}
            (root / "docker-compose.yml").write_text(json.dumps(config))
            compose = ["docker", "compose", "-f", str(root / "docker-compose.yml")]
            def execute(service, *args):
                # A fixture receipt proves real remote completion independently
                # of an exec client's potentially premature zero/stream closure.
                directory = root / "logs/native-control"
                directory.mkdir(parents=True, exist_ok=True)
                local = directory / uuid.uuid4().hex
                remote = "/php-qa-scope/" + str(local.relative_to(root))
                if service == "dev":
                    wrapper = ["python3", "-c", """
import json, os, subprocess, sys
base=sys.argv[1]
with open(base+'.stdout','wb') as out, open(base+'.stderr','wb') as err:
    code=subprocess.run(sys.argv[2:],stdin=subprocess.DEVNULL,stdout=out,stderr=err).returncode
with open(base+'.tmp','w') as f: json.dump(code,f)
os.replace(base+'.tmp',base+'.done')
""", remote, *args]
                else:
                    wrapper = ["php", "-r", """
$base=$argv[1];
$p=proc_open(array_slice($argv,2),[0=>['file','/dev/null','r'],
1=>['file',$base.'.stdout','w'],2=>['file',$base.'.stderr','w']],$pipes);
$code=proc_close($p); file_put_contents($base.'.tmp',json_encode($code));
rename($base.'.tmp',$base.'.done');
""", "--", remote, *args]
                client = subprocess.run([*compose, "exec", "-T", service, *wrapper], cwd=root,
                                        capture_output=True, text=True, timeout=180)
                deadline = time.monotonic() + 180
                done = local.with_suffix(".done")
                while not done.exists():
                    self.assertLess(time.monotonic(), deadline,
                                    "Remote fixture completion unknown: " + client.stdout + client.stderr)
                    time.sleep(.02)
                return subprocess.CompletedProcess(args, json.loads(done.read_text()),
                    local.with_suffix(".stdout").read_text(), local.with_suffix(".stderr").read_text())
            def required(service, *args):
                result = execute(service, *args)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout.strip()
            try:
                result = subprocess.run([*compose, "up", "-d"], capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(required("dev", "printenv", "QA_HOOKS_SERVICE"), "dev")
                # Reject a broken exec transport before starting any hook work.
                completion = required("dev", "python3", "-c",
                    "import time; time.sleep(1); print('native-exec-complete')")
                self.assertEqual(completion, "native-exec-complete",
                    "Docker exec returned before its process completed; native acceptance is unavailable")
                # Prove this image uses the npm wrapper and its platform dependency.
                command = required("dev", "sh", "-c", "command -v lefthook")
                entrypoint = required("dev", "readlink", "-f", command)
                self.assertEqual(required("dev", "head", "-n", "1", entrypoint), "#!/usr/bin/env node")
                package_dir = str(Path(entrypoint).parent.parent)
                package = json.loads(required("dev", "cat", package_dir + "/package.json"))
                self.assertEqual((package["name"], package["version"]), ("lefthook", "2.1.16"))
                native = required("dev", "node", "-e",
                                  "console.log(require(process.argv[1] + '/get-exe').getExePath())", package_dir)
                self.assertIn("lefthook-linux-", native)
                self.assertEqual(required("dev", native, "version"), "2.1.16")
                self.assertEqual(required("dev", "lefthook", "version"), "2.1.16")
                required("dev", "git", "init", "-b", "main")
                required("dev", "git", "config", "user.name", "Native hook fixture")
                required("dev", "git", "config", "user.email", "fixture@example.invalid")
                required("dev", "git", "add", ".")
                required("dev", "git", "commit", "-m", "isolated native fixture")
                required("dev", "git", "init", "--bare", ".git/native-remote.git")
                required("dev", "git", "remote", "add", "fixture", "/php-qa-scope/.git/native-remote.git")
                # Installer is contributor tooling, copied explicitly for this fixture.
                installer = root / "tools/setup-native-hooks"
                shutil.copy2(PROJECT / "docker/dev/bin/setup-git-hooks", installer)
                required("dev", "git", "add", "tools/setup-native-hooks")
                required("dev", "git", "commit", "-m", "fixture installer")
                required("dev", "bash", "tools/setup-native-hooks")
                old, old_snapshot = old_flat_run(root)
                first = execute("dev", "git", "push", "fixture", "main")
                reports = sorted(p for p in root.glob("logs/prepush/*/summary.json") if p.parent != old)
                if reports:
                    evidence.mkdir(parents=True, exist_ok=True)
                    for path in reports:
                        shutil.copytree(path.parent, evidence / path.parent.name, dirs_exist_ok=True)
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr +
                                 "\nNative evidence retained at " + str(evidence))
                self.assertTrue(reports, "Docker exec returned before hook reports existed:\n" + first.stdout + first.stderr)
                summary = json.loads(reports[0].read_text())
                self.assertEqual(summary["status"], "passed")
                self.assertEqual(summary["invocation_mode"], "git")
                assert_layout(self, reports[0].parent, summary)
                self.assertTrue(all(c["report_valid"] for c in summary["validations"]))
                self.assertEqual(required("dev", "git", "status", "--porcelain"), "")
                remote_refs = required("dev", "git", "--git-dir=.git/native-remote.git", "for-each-ref")
                for detached in (False, True):
                    if detached:
                        required("dev", "git", "checkout", "--detach", "HEAD")
                    manual = execute("dev", "lefthook", "run", "pre-push")
                    self.assertEqual(manual.returncode, 0, manual.stdout + manual.stderr)
                    latest = max(root.glob("logs/prepush/*/summary.json"))
                    result = json.loads(latest.read_text())
                    self.assertEqual(result["invocation_mode"], "manual")
                    self.assertEqual(result["status"], "passed")
                    self.assertTrue(all(c["report_valid"] for c in result["validations"]))
                    assert_layout(self, latest.parent, result)
                    self.assertEqual(required("dev", "git", "--git-dir=.git/native-remote.git", "for-each-ref"), remote_refs)
                required("dev", "git", "checkout", "main")
                # Change one managed block to trigger QA Scope without correction/staging hooks.
                native = root / "phpcs.xml"
                contents = native.read_text()
                self.assertIn("<file>.</file>", contents)
                # Equivalent native path keeps all files eligible while managed text drifts.
                native.write_text(contents.replace("<file>.</file>", "<file>./</file>", 1))
                required("dev", "git", "add", "phpcs.xml")
                required("dev", "git", "commit", "-m", "intentional scope rejection")
                rejected = execute("dev", "git", "push", "fixture", "main")
                self.assertNotEqual(rejected.returncode, 0)
                reports = sorted(p for p in root.glob("logs/prepush/*/summary.json") if p.parent != old)
                self.assertEqual(len(reports), 4)
                for path in reports:
                    shutil.copytree(path.parent, evidence / path.parent.name, dirs_exist_ok=True)
                summary = json.loads(reports[-1].read_text())
                scope = next(c for c in summary["validations"] if c["validation_id"] == "qa-scope")
                assert_layout(self, reports[-1].parent, summary)
                self.assertEqual(scope["status"], "failed")
                self.assertTrue(all(c["report_valid"] for c in summary["validations"]))
                self.assertEqual(required("dev", "git", "status", "--porcelain"), "")
                self.assertEqual(required("dev", "git", "stash", "list"), "")
                manual = execute("dev", "lefthook", "run", "pre-push")
                self.assertNotEqual(manual.returncode, 0)
                latest = max(root.glob("logs/prepush/*/summary.json"))
                result = json.loads(latest.read_text())
                self.assertEqual(result["invocation_mode"], "manual")
                self.assertEqual(result["status"], "failed")
                self.assertTrue(all(c["report_valid"] for c in result["validations"]))
                assert_layout(self, latest.parent, result)
                self.assertEqual(required("dev", "git", "--git-dir=.git/native-remote.git", "for-each-ref"), remote_refs)
                # Exercise real OpenSpec findings with otherwise valid native PHP checks.
                native.write_text(contents)
                invalid = root / "openspec/changes/invalid-native-fixture"
                delta = invalid / "specs/fixture/spec.md"
                delta.parent.mkdir(parents=True)
                delta.write_text("## ADDED Requirements\n\n### Requirement: Invalid native fixture\nThe system SHALL reject this missing-scenario fixture.\n")
                (invalid / "proposal.md").write_text("## Why\nIntentional validation failure.\n")
                (invalid / "tasks.md").write_text("- [ ] Leave this active task unchecked.\n")
                required("dev", "git", "add", "phpcs.xml", "openspec")
                required("dev", "git", "commit", "-m", "intentional OpenSpec rejection")
                invalid_result = execute("dev", "lefthook", "run", "pre-push")
                self.assertNotEqual(invalid_result.returncode, 0)
                latest = max(root.glob("logs/prepush/*/summary.json"))
                result = json.loads(latest.read_text())
                local = result["validations"][-1]
                self.assertEqual((local["validation_id"], local["status"], local["exit_code"]),
                                 ("openspec", "failed", 1))
                self.assertTrue(all(c["report_valid"] for c in result["validations"]))
                self.assertTrue(all(c["status"] == "passed" for c in result["validations"][:-1]))
                assert_layout(self, latest.parent, result)
                shutil.rmtree(invalid)
                required("dev", "git", "add", "openspec")
                required("dev", "git", "commit", "-m", "restore valid OpenSpec fixture")

                # Controlled native work keeps a PHP descendant alive until cancellation.
                # Its script and Composer mutation exist only in this disposable fixture.
                hold = root / "tools/native-hold.php"
                hold.write_text("""<?php
$args = array_slice($argv, 1);
$run = dirname($args[array_search('--log-junit', $args, true) + 1], 3);
$pipes = [];
$child = proc_open(['sh', '-c', 'trap "" INT TERM; exec php -r "sleep(60);"'], [], $pipes);
file_put_contents($run . '/native-held.json', json_encode([
    'parent' => getmypid(), 'child' => proc_get_status($child)['pid']]));
while (true) { usleep(10000); }
""")
                composer = json.loads((root / "composer.json").read_text())
                composer["scripts"]["test"] = "php tools/native-hold.php"
                (root / "composer.json").write_text(json.dumps(composer, indent=2) + "\n")
                required("dev", "git", "add", "composer.json", "tools/native-hold.php")
                required("dev", "git", "commit", "-m", "native cancellation fixture")
                from test_hooks_terminal import Terminal, PHASE_FIXTURE
                def php_alive(pid):
                    return execute("php", "sh", "-c",
                        f"test -r /proc/{pid}/stat && test \"$(awk '{{print $3}}' /proc/{pid}/stat)\" != Z").returncode == 0
                def native_alive(container_id, pid):
                    result = subprocess.run(["docker", "exec", container_id, "sh", "-c",
                        f"test -r /proc/{pid}/stat && test \"$(awk '{{print $3}}' /proc/{pid}/stat)\" != Z"],
                        cwd=root, capture_output=True, timeout=5)
                    return result.returncode == 0
                def assert_removed(run):
                    owner = json.loads((run / "runtime.json").read_text())["owner"]
                    result = subprocess.run(["docker", "ps", "-aq", "--filter",
                        "label=php-qa-scope.execution=" + owner], cwd=root,
                        capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), "", "Owned running/stopped containers remain")
                # Real Docker creation/ID/start barriers live only in this committed fixture.
                with (root / "tools/git_hooks/execution.py").open("a") as handle:
                    handle.write(PHASE_FIXTURE)
                required("dev", "git", "add", "tools/git_hooks/execution.py")
                required("dev", "git", "commit", "-m", "native container phase fixture")
                controls = root / ".git/barriers"
                controls.mkdir()
                for phase in ("container-acknowledgement", "container-id-publication", "container-start"):
                    for number in (signal.SIGINT, signal.SIGTERM):
                        marker = controls / (phase + "-" + str(number))
                        previous = set(root.glob("logs/prepush/*"))
                        terminal = Terminal([*compose, "exec", "-e", "FIXTURE_PHASE=" + phase,
                            "-e", "FIXTURE_BARRIER=/php-qa-scope/.git/barriers/" + marker.name,
                            "dev", "lefthook", "run", "pre-push"], root, os.environ)
                        try:
                            deadline = time.monotonic() + 20
                            while not marker.exists():
                                terminal.drain()
                                self.assertIsNone(terminal.process.poll(), terminal.output.decode(errors="replace"))
                                self.assertLess(time.monotonic(), deadline)
                                time.sleep(.01)
                            began = time.monotonic()
                            if number == signal.SIGINT:
                                os.write(terminal.master, b"\x03")
                            else:
                                pid = int(marker.read_text())
                                required("dev", "kill", "-TERM", str(pid))
                                # A job-level signal must still produce nonzero collection;
                                # cancel the coordinator to exercise the common cleanup path.
                                run = next(iter(set(root.glob("logs/prepush/*")) - previous))
                                coordinator = json.loads((run / "processes/coordinator.json").read_text())
                                required("dev", "kill", "-TERM", str(coordinator["process"]["pid"]))
                            self.assertNotEqual(terminal.wait(10), 0)
                            run = next(iter(set(root.glob("logs/prepush/*")) - previous))
                            while json.loads((run / "summary.json").read_text())["status"] != "interrupted":
                                self.assertLess(time.monotonic() - began, 10)
                                time.sleep(.01)
                            assert_removed(run)
                            self.assertFalse((run / "native-held.json").exists())
                            self.assertLess(time.monotonic() - began, 10)
                            self.assertNotIn(b"Traceback", terminal.output)
                            self.assertEqual(required("dev", "git", "status", "--porcelain"), "")
                        finally:
                            terminal.close()
                required("php", "sh", "-c",
                    "setsid sh -c 'echo $$ >.git/unrelated.pid; sleep 60' >/dev/null 2>&1 </dev/null &")
                unrelated = int((root / ".git/unrelated.pid").read_text())
                for repeated in (False, True, "overlap"):
                    terminal = Terminal([*compose, "exec", "dev", "lefthook", "run", "pre-push"], root, os.environ)
                    second = None
                    previous = set(root.glob("logs/prepush/*"))
                    try:
                        deadline = time.monotonic() + 20
                        marker = None
                        while marker is None:
                            terminal.drain()
                            marker = next((p / "native-held.json" for p in set(root.glob("logs/prepush/*")) - previous
                                if (p / "native-held.json").exists()), None)
                            self.assertLess(time.monotonic(), deadline, terminal.output.decode(errors="replace"))
                            self.assertIsNone(terminal.process.poll(), terminal.output.decode(errors="replace"))
                            time.sleep(.01)
                        native_ids = json.loads(marker.read_text())
                        native_container = json.loads((marker.parent / "containers/test/metadata.json").read_text())["id"]
                        actual = json.loads(host_command("docker", "inspect", native_container))[0]
                        active_php = json.loads(host_command("docker", "inspect",
                            host_command(*compose, "ps", "-q", "php")))[0]
                        self.assertEqual(actual["Image"], active_php["Image"])
                        self.assertEqual(actual["Config"]["User"], active_php["Config"]["User"])
                        self.assertEqual(actual["Config"]["WorkingDir"], active_php["Config"]["WorkingDir"])
                        self.assertTrue(set(actual["Config"]["Env"]) == set(active_php["Config"]["Env"]), "Runtime environment differs")
                        # Docker Desktop can expose inherited bind sources through
                        # a VM-internal alias. Verify mount mode and file identity
                        # rather than rejecting equivalent host-path spellings.
                        mounts = lambda item: {(m["Type"], m["Destination"], m["RW"]) for m in item["Mounts"]}
                        self.assertEqual(mounts(actual), mounts(active_php))
                        destinations = [m["Destination"] for m in active_php["Mounts"]]
                        self.assertEqual(host_command("docker", "exec", native_container, "stat", "-c", "%d:%i", *destinations),
                            host_command("docker", "exec", active_php["Id"], "stat", "-c", "%d:%i", *destinations))
                        self.assertEqual({v["NetworkID"] for v in actual["NetworkSettings"]["Networks"].values()},
                            {v["NetworkID"] for v in active_php["NetworkSettings"]["Networks"].values()})
                        self.assertFalse(actual["HostConfig"]["AutoRemove"])
                        self.assertTrue(actual["HostConfig"]["Init"])
                        self.assertEqual(actual["HostConfig"]["RestartPolicy"]["Name"], "no")
                        self.assertFalse(actual["Config"]["Tty"])
                        self.assertFalse(actual["Config"]["OpenStdin"])
                        self.assertEqual(actual["Config"]["Entrypoint"], ["composer"])
                        self.assertEqual({m.get("Name") for m in actual["Mounts"] if m["Type"] == "volume"}
                            - {m.get("Name") for m in active_php["Mounts"] if m["Type"] == "volume"}, set())
                        self.assertTrue(all(native_alive(native_container, pid) for pid in native_ids.values()))
                        if repeated == "overlap":
                            second_previous = set(root.glob("logs/prepush/*"))
                            second = Terminal([*compose, "exec", "dev", "lefthook", "run", "pre-push"], root, os.environ)
                            second_marker = None
                            deadline = time.monotonic() + 20
                            while second_marker is None:
                                second.drain()
                                second_marker = next((p / "native-held.json" for p in set(root.glob("logs/prepush/*")) - second_previous
                                    if (p / "native-held.json").exists()), None)
                                self.assertLess(time.monotonic(), deadline)
                                time.sleep(.01)
                            second_ids = json.loads(second_marker.read_text())
                            second_container = json.loads((second_marker.parent / "containers/test/metadata.json").read_text())["id"]
                        began = time.monotonic()
                        os.write(terminal.master, b"\x03")
                        if repeated:
                            time.sleep(.03)
                            coordinator = json.loads((marker.parent / "processes/coordinator.json").read_text())
                            required("dev", "kill", "-TERM", str(coordinator["process"]["pid"]))
                        self.assertNotEqual(terminal.wait(10), 0)
                        summary_path = marker.parent / "summary.json"
                        while json.loads(summary_path.read_text())["status"] != "interrupted":
                            self.assertLess(time.monotonic() - began, 10)
                            time.sleep(.01)
                        assert_removed(marker.parent)
                        self.assertLess(time.monotonic() - began, 10)
                        if repeated:
                            self.assertLess(time.monotonic() - began, 5, "Repeated signal did not force native teardown")
                        self.assertTrue(php_alive(unrelated), "Cancellation signalled unrelated native work")
                        if repeated == "overlap":
                            self.assertIsNone(second.process.poll())
                            self.assertTrue(all(native_alive(second_container, pid) for pid in second_ids.values()))
                            second_began = time.monotonic()
                            os.write(second.master, b"\x03")
                            self.assertNotEqual(second.wait(10), 0)
                            while json.loads((second_marker.parent / "summary.json").read_text())["status"] != "interrupted":
                                self.assertLess(time.monotonic() - second_began, 10)
                                time.sleep(.01)
                            assert_removed(second_marker.parent)
                            self.assertTrue(php_alive(unrelated))
                        self.assertNotIn(b"Traceback", terminal.output)
                        result = json.loads(summary_path.read_text())
                        self.assertEqual(result["exit_code"], 1)
                        self.assertFalse(any("unconfirmed" in e for e in result["errors"]), result["errors"])
                        self.assertEqual(required("dev", "git", "--git-dir=.git/native-remote.git", "for-each-ref"), remote_refs)
                        self.assertEqual(required("dev", "git", "status", "--porcelain"), "")
                    finally:
                        terminal.close()
                        if second:
                            second.close()
                for path in root.glob("logs/prepush/*/summary.json"):
                    if path.parent == old:
                        continue
                    assert_removed(path.parent)
                    assert_layout(self, path.parent, json.loads(path.read_text()),
                                  complete=json.loads(path.read_text())["status"] != "interrupted")
                    shutil.copytree(path.parent, evidence / path.parent.name, dirs_exist_ok=True)
                self.assertEqual(old_snapshot, {p.relative_to(old): p.read_bytes()
                                               for p in old.rglob("*") if p.is_file()})
            finally:
                # Cleanup failed acceptance fixtures as well; never retain test QA containers.
                for path in root.glob("logs/prepush/*/summary.json"):
                    if path.parent.name != "20000101-000000-000":
                        shutil.copytree(path.parent, evidence / path.parent.name, dirs_exist_ok=True)
                for context in root.glob("logs/prepush/*/runtime.json"):
                    owner = json.loads(context.read_text())["owner"]
                    ids = subprocess.check_output(["docker", "ps", "-aq", "--filter",
                        "label=php-qa-scope.execution=" + owner], text=True).split()
                    if ids:
                        subprocess.run(["docker", "rm", "-f", "-v", *ids], capture_output=True, timeout=10)
                subprocess.run([*compose, "down"], capture_output=True, timeout=90)
