"""Real terminal/frontend cancellation with fixture-only deterministic barriers."""
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import tempfile
import termios
import time
import unittest

from git_hooks import execution
from test_hooks_integration import assembled, assert_layout, LEFTHOOK, PROJECT


PHASE_FIXTURE = '''
# Instrument only this disposable committed fixture, never production hook paths.
_ordinary_phase = Session.phase
def _fixture_phase(self, name):
    _ordinary_phase(self, name)
    target = os.environ.get("FIXTURE_PHASE")
    if name != target or self.finishing:
        return
    if name in ("native-report", "result-publication") and self.job_id != "stan":
        return
    if name.startswith(("results-tool-directory", "containers-tool-directory")) and self.job_id != "stan":
        return
    marker = Path(os.environ["FIXTURE_BARRIER"])
    marker.write_text(str(os.getpid()))
    while not marker.with_suffix(".release").exists():
        if name.endswith("-atomic") and self.number is not None:
            break
        self.check()
        time.sleep(.005)
Session.phase = _fixture_phase
'''

ATOMIC_FIXTURE = '''
_ordinary_atomic_json = atomic_json
def atomic_json(path, data):
    session = execution.CURRENT
    target = os.environ.get("FIXTURE_PHASE")
    selected = (
        target == "initial-atomic" and Path(path).name == "summary.json" and data.get("status") == "incomplete"
        or target == "final-atomic" and Path(path).name == "summary.json" and data.get("status") == "passed"
        or target == "result-atomic" and Path(path).name == "stan.json" and Path(path).parent.name == "jobs"
            and data.get("status") == "passed"
        or target == "container-id-atomic" and Path(path).name == "metadata.json"
            and Path(path).parent.name == "stan" and data.get("state") == "created"
        or target == "native-proof-atomic" and Path(path).name == "metadata.json"
            and Path(path).parent.name == "stan" and data.get("state") == "exited"
            and data.get("native_completion") == "confirmed")
    if not session or session.finishing or not selected:
        return _ordinary_atomic_json(path, data)
    with session.atomic():
        marker = Path(os.environ["FIXTURE_BARRIER"])
        marker.write_text(str(os.getpid()))
        while session.number is None and not marker.with_suffix(".release").exists():
            time.sleep(.005)
        _ordinary_atomic_json(path, data)
'''


def live_fixture(token):
    """Select this fixture's actual exec processes, excluding dead zombies."""
    found = []
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal():
            continue
        try:
            env = (path / "environ").read_bytes().split(b"\0")
            record = execution.identity(int(path.name))
            if f"FIXTURE_TOKEN={token}".encode() in env and record and record["state"] != "Z":
                found.append(record)
        except (OSError, PermissionError):
            pass
    return found


class Terminal:
    def __init__(self, command, root, env):
        self.env = env
        self.master, slave = pty.openpty()
        def own_terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        self.process = subprocess.Popen(command, cwd=root, env=env, stdin=slave,
            stdout=slave, stderr=slave, preexec_fn=own_terminal)
        os.close(slave)
        os.set_blocking(self.master, False)
        self.output = b""

    def drain(self):
        while select.select([self.master], [], [], 0)[0]:
            try:
                data = os.read(self.master, 65536)
                if not data:
                    return
                self.output += data
            except (BlockingIOError, OSError):
                return

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while self.process.poll() is None:
            self.drain()
            if time.monotonic() > deadline:
                raise AssertionError("Terminal did not recover: " + self.output.decode(errors="replace"))
            time.sleep(.01)
        self.drain()
        return self.process.returncode

    def close(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=2)
        os.close(self.master)


@unittest.skipUnless(LEFTHOOK, "Pinned npm Lefthook required")
class TerminalTests(unittest.TestCase):
    def instrument(self, root, git):
        with (root / "tools/git_hooks/execution.py").open("a") as handle:
            handle.write(PHASE_FIXTURE)
        with (root / "tools/git_hooks/reports.py").open("a") as handle:
            handle.write(ATOMIC_FIXTURE)
        git("add", "tools/git_hooks/execution.py", "tools/git_hooks/reports.py")
        git("commit", "-m", "terminal phase fixture")

    def await_barrier(self, terminal, marker):
        # Readiness is ordinary QA work, not the shared cancellation deadline.
        deadline = time.monotonic() + 20
        while not marker.exists():
            terminal.drain()
            self.assertIsNone(terminal.process.poll(), terminal.output.decode(errors="replace"))
            self.assertLess(time.monotonic(), deadline, terminal.output.decode(errors="replace"))
            time.sleep(.01)

    def assert_stopped(self, terminal, token, began, native=True):
        self.assertNotEqual(terminal.wait(10), 0)
        deadline = began + 10
        while live_fixture(token) and time.monotonic() < deadline:
            terminal.drain()
            time.sleep(.02)
        self.assertEqual(live_fixture(token), [], terminal.output.decode(errors="replace"))
        self.assertLess(time.monotonic() - began, 10)
        self.assertNotIn(b"Traceback", terminal.output)
        if native and terminal.env.get("FIXTURE_ENGINE"):
            engine = Path(terminal.env["FIXTURE_ENGINE"])
            for file in (engine / "actors").glob("*.json"):
                record = json.loads(file.read_text())
                if record.get("token") == token:
                    self.assertFalse(execution.alive(record), "Fake Docker native work survived cleanup")
            remaining = [json.loads(file.read_text())["Name"] for file in engine.glob("*.json")
                if json.loads(file.read_text()).get("fixture_token") == token]
            self.assertEqual(remaining, [], "Owned created/running/stopped container objects remain")

    def test_openspec_version_probe_node_descendants_cancel_before_allocation(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
                token = f"openspec-probe-{time.monotonic_ns()}"
                marker = Path(controls) / "probe.started"
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root,
                    dict(env, FIXTURE_TOKEN=token, FIXTURE_OPENSPEC_PROBE_MARKER=str(marker)))
                try:
                    self.await_barrier(terminal, marker)
                    began = time.monotonic()
                    terminal.process.send_signal(number)
                    self.assert_stopped(terminal, token, began)
                    self.assertFalse(list(root.glob("logs/prepush/*")))
                finally:
                    terminal.close()

    def test_openspec_local_descendants_cancel_with_php_jobs(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with assembled() as (root, git, env):
                token = f"openspec-{time.monotonic_ns()}"
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root,
                    dict(env, FIXTURE_TOKEN=token, FIXTURE_OPENSPEC="node-hold", QA_TEST_HOLD="1"))
                try:
                    deadline = time.monotonic() + 15
                    while not list(root.glob("logs/prepush/*/openspec.started")):
                        terminal.drain()
                        self.assertIsNone(terminal.process.poll())
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(.01)
                    began = time.monotonic()
                    terminal.process.send_signal(number)
                    self.assert_stopped(terminal, token, began)
                    run = max(root.glob("logs/prepush/*"))
                    summary = json.loads((run / "summary.json").read_text())
                    self.assertEqual(summary["status"], "interrupted")
                    assert_layout(self, run, summary, complete=False)
                    self.assertFalse((run / "containers/openspec").exists())
                finally:
                    terminal.close()

    def test_manual_attached_detached_stdin_open_and_no_remote_change(self):
        with assembled() as (root, git, env):
            git("init", "--bare", ".git/remote.git")
            refs = git("--git-dir=.git/remote.git", "for-each-ref")
            for detached in (False, True):
                if detached:
                    git("checkout", "--detach", "HEAD")
                token = f"manual-{time.monotonic_ns()}"
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, dict(env, FIXTURE_TOKEN=token))
                try:
                    self.assertEqual(terminal.wait(10), 0, terminal.output.decode(errors="replace"))
                    run = max(root.glob("logs/prepush/*"))
                    summary = json.loads((run / "summary.json").read_text())
                    self.assertEqual(summary["invocation_mode"], "manual")
                    self.assertEqual(summary["status"], "passed")
                    self.assertEqual(len(summary["validations"]), 7)
                    assert_layout(self, run, summary)
                    self.assertIn(b"qa-manual", terminal.output)
                    self.assertNotIn(b"qa-gate", terminal.output)
                    self.assertEqual(git("--git-dir=.git/remote.git", "for-each-ref"), refs)
                finally:
                    terminal.close()

    def test_manual_dirty_missing_head_invalid_context_reject_without_reports(self):
        with assembled() as (root, git, env):
            before = git("write-tree"), git("stash", "list")
            (root / "untracked").write_text("leave this unchanged")
            result = subprocess.run([LEFTHOOK, "run", "pre-push"], cwd=root, env=env,
                capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"clean index/worktree", result.stdout + result.stderr)
            self.assertFalse((root / "logs/prepush").exists())
            self.assertEqual((root / "untracked").read_text(), "leave this unchanged")
            self.assertEqual(before, (git("write-tree"), git("stash", "list")))
            (root / "untracked").unlink()
            invalid = subprocess.run([LEFTHOOK, "run", "pre-push"], cwd=root,
                env=dict(env, QA_HOOKS_GIT_PUSH="invalid"), capture_output=True, timeout=10)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn(b"Invalid Git/manual launcher context", invalid.stdout + invalid.stderr)
            forged = subprocess.run([root / "tools/git-hooks", "boundary", "manual", str(os.getpid())],
                cwd=root, env=env, capture_output=True, timeout=10)
            self.assertNotEqual(forged.returncode, 0)
            self.assertIn(b"frontend identity", forged.stderr)
            git("checkout", "--orphan", "unborn")
            git("rm", "-r", "--cached", ".")
            missing = subprocess.run([LEFTHOOK, "run", "pre-push"], cwd=root, env=env,
                capture_output=True, timeout=10)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((root / "logs/prepush").exists())

    def test_docker_confirmation_failure_is_truthful_and_local_processes_stop(self):
        with assembled() as (root, git, env):
            token = f"php-failure-{time.monotonic_ns()}"
            terminal = Terminal([LEFTHOOK, "run", "pre-push"], root,
                dict(env, FIXTURE_TOKEN=token, QA_TEST_HOLD="1", QA_TEST_PHP_FAIL="1"))
            try:
                deadline = time.monotonic() + 10
                while len(list(root.glob("logs/prepush/*/*.started"))) < 6:
                    terminal.drain()
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                began = time.monotonic()
                os.write(terminal.master, b"\x03")
                self.assert_stopped(terminal, token, began, native=False)
                summary = json.loads(next(root.glob("logs/prepush/*/summary.json")).read_text())
                self.assertEqual(summary["status"], "interrupted")
                self.assertTrue(any("Container cleanup unconfirmed" in e for e in summary["errors"]), summary["errors"])
                self.assertTrue(any("unreachable" in e for e in summary["errors"]))
            finally:
                terminal.close()

    def test_sigint_sigterm_every_phase_actual_npm_frontend(self):
        phases = ("entry", "environment", "git-root", "git-probe", "checkout",
                "runtime", "openspec-probe", "openspec-launch", "openspec-report", "compose-version", "running-service", "composer-probe", "dependencies",
            "allocation", "allocation-created", "initial-publication", "qa",
            "native-command", "native-report", "result-publication",
            "final-consolidation", "final-publication", "return",
            "initial-atomic", "result-atomic", "final-atomic", "runtime-template",
            "container-intent", "container-create", "container-acknowledgement",
            "container-id-publication", "container-start", "container-reconcile",
            "container-removal", "container-absence", "container-id-atomic",
            "jobs-directory", "jobs-directory-atomic", "jobs-directory-created",
            "results-tool-directory", "results-tool-directory-atomic", "results-tool-directory-created",
            "containers-tool-directory", "containers-tool-directory-atomic", "containers-tool-directory-created")
        self.phase_cancellation_matrix(phases)

    def test_native_state_snapshot_and_proof_publication_cancellation(self):
        self.phase_cancellation_matrix(("container-observation", "container-completion",
            "container-log-collection", "container-logs-collected", "native-proof-atomic"))

    def phase_cancellation_matrix(self, phases):
        with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
            self.instrument(root, git)
            before = git("status", "--porcelain"), git("write-tree"), git("stash", "list")
            for phase in phases:
                for number in (signal.SIGINT, signal.SIGTERM):
                    with self.subTest(phase=phase, signal=number):
                        token = f"phase-{time.monotonic_ns()}"
                        marker = Path(controls) / token
                        options = dict(env, FIXTURE_PHASE=phase, FIXTURE_BARRIER=str(marker), FIXTURE_TOKEN=token)
                        if phase == "qa":
                            options["QA_TEST_HOLD"] = "1"
                        terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
                        previous = set(root.glob("logs/prepush/*"))
                        try:
                            self.await_barrier(terminal, marker)
                            began = time.monotonic()
                            if number == signal.SIGINT:
                                os.write(terminal.master, b"\x03")
                                if phase in ("final-consolidation", "final-atomic"):
                                    time.sleep(.02)
                                    os.write(terminal.master, b"\x03")
                            else:
                                # Signal native frontend directly; preserve open PTY stdin.
                                frontend = next(item for item in live_fixture(token)
                                    if b"pre-push" in Path(f"/proc/{item['pid']}/cmdline").read_bytes().split(b"\0")
                                    and b"lefthook-linux" in Path(f"/proc/{item['pid']}/cmdline").read_bytes())
                                os.kill(frontend["pid"], number)
                            self.assert_stopped(terminal, token, began)
                            runs = set(root.glob("logs/prepush/*")) - previous
                            for run in runs:
                                summary = json.loads((run / "summary.json").read_text())
                                self.assertEqual(summary["status"], "interrupted")
                                self.assertEqual(summary["exit_code"], 1)
                                assert_layout(self, run, summary, complete=False)
                                self.assertTrue(all(c["exit_code"] is None for c in summary["validations"]
                                    if c["status"] == "not_run"))
                            self.assertEqual(before, (git("status", "--porcelain"), git("write-tree"), git("stash", "list")))
                        finally:
                            terminal.close()

    def test_installed_git_input_cancellation_and_empty_never_manual(self):
        with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
            self.instrument(root, git)
            subprocess.run([PROJECT / "docker/dev/bin/setup-git-hooks"], cwd=root, env=env,
                           check=True, capture_output=True)
            hook = root / ".git/hooks/pre-push"
            empty = subprocess.run([hook, "origin", "opaque remote"], cwd=root, env=env,
                                   input=b"", capture_output=True, timeout=10)
            self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
            self.assertFalse((root / "logs/prepush").exists())
            for number in (signal.SIGINT, signal.SIGTERM):
                token = f"git-input-{time.monotonic_ns()}"
                marker = Path(controls) / token
                options = dict(env, FIXTURE_PHASE="input", FIXTURE_BARRIER=str(marker), FIXTURE_TOKEN=token)
                terminal = Terminal([hook, "origin", "opaque remote"], root, options)
                try:
                    self.await_barrier(terminal, marker)
                    worker = int(marker.read_text())
                    marker.with_suffix(".release").touch()
                    wait_deadline = time.monotonic() + 5
                    # Kernel wchan is hidden on some container hosts. With no
                    # probe pipes left, this sole epoll fd is the real stdin selector.
                    def reading_stdin():
                        descriptors = list(Path(f"/proc/{worker}/fd").iterdir())
                        return len(descriptors) == 4 and any(
                            os.readlink(fd) == "anon_inode:[eventpoll]" for fd in descriptors)
                    while not reading_stdin():
                        self.assertLess(time.monotonic(), wait_deadline, "Worker never entered actual stdin read")
                        time.sleep(.005)
                    began = time.monotonic()
                    os.killpg(terminal.process.pid, number)
                    self.assert_stopped(terminal, token, began)
                    self.assertFalse((root / "logs/prepush").exists())
                finally:
                    terminal.close()

    def test_cancellation_inside_actual_git_and_runtime_probe_processes(self):
        probes = (("rev-parse --show-toplevel", "git"), ("rev-parse --verify HEAD", "git"),
                  ("diff --ignore-submodules=none --name-only -z --", "git"),
                  ("compose version", "docker"), ("compose ps --services --status running", "docker"),
                  ("compose exec -T php composer --no-ansi --version", "docker"),
                  ("compose exec -T php sh -c test -r vendor/autoload.php && test -x vendor/bin/phpcs"
                   " && test -x vendor/bin/php-cs-fixer && test -x vendor/bin/phpmd"
                   " && test -x vendor/bin/phpstan && test -x vendor/bin/phpunit", "docker"))
        with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
            shim = Path(controls) / "git"
            real_git = subprocess.check_output(["which", "git"]).decode().strip()
            shim.write_text("""#!/usr/bin/env python3
import os, pathlib, sys, time
if os.environ.get('FIXTURE_PROBE') == ' '.join(sys.argv[1:]):
    pathlib.Path(os.environ['FIXTURE_BARRIER']).write_text(str(os.getpid()))
    while True: time.sleep(.05)
os.execv(os.environ['FIXTURE_REAL_GIT'], ['git', *sys.argv[1:]])
""")
            shim.chmod(0o755)
            for probe, kind in probes:
                for number in (signal.SIGINT, signal.SIGTERM):
                    with self.subTest(probe=probe, signal=number):
                        token = f"probe-{time.monotonic_ns()}"
                        marker = Path(controls) / token
                        options = dict(env, FIXTURE_PROBE=probe, FIXTURE_BARRIER=str(marker),
                            FIXTURE_TOKEN=token, FIXTURE_REAL_GIT=real_git)
                        if kind == "git":
                            options["PATH"] = controls + os.pathsep + env["PATH"]
                        terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
                        try:
                            self.await_barrier(terminal, marker)
                            began = time.monotonic()
                            os.killpg(terminal.process.pid, number)
                            self.assert_stopped(terminal, token, began)
                            self.assertFalse((root / "logs/prepush").exists())
                        finally:
                            terminal.close()

    def test_installed_git_push_cancellation_retains_evidence_and_remote_refs(self):
        phases = ("input", "allocation-created", "initial-atomic", "native-report",
            "result-atomic", "final-consolidation", "final-atomic", "hold",
            "container-create", "container-acknowledgement", "container-id-publication",
            "container-start", "container-removal", "container-absence",
            "jobs-directory-atomic", "results-tool-directory-atomic", "containers-tool-directory-atomic")
        with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
            self.instrument(root, git)
            git("init", "--bare", ".git/remote.git")
            git("remote", "add", "fixture", str(root / ".git/remote.git"))
            subprocess.run([PROJECT / "docker/dev/bin/setup-git-hooks"], cwd=root, env=env,
                check=True, capture_output=True)
            before = git("write-tree"), git("stash", "list"), git("status", "--porcelain")
            for phase in phases:
                for number in (signal.SIGINT, signal.SIGTERM):
                    with self.subTest(phase=phase, signal=number):
                        token = f"git-push-{time.monotonic_ns()}"
                        marker = Path(controls) / token
                        options = dict(env, FIXTURE_PHASE=phase, FIXTURE_BARRIER=str(marker), FIXTURE_TOKEN=token)
                        if phase == "hold":
                            options["QA_TEST_HOLD"] = "1"
                        previous = set(root.glob("logs/prepush/*"))
                        terminal = Terminal(["git", "push", "fixture", "main"], root, options)
                        try:
                            if phase == "hold":
                                deadline = time.monotonic() + 10
                                while len([p for p in root.glob("logs/prepush/*/*.started")
                                           if p.parent not in previous]) < 6:
                                    terminal.drain()
                                    self.assertIsNone(terminal.process.poll(), terminal.output.decode(errors="replace"))
                                    self.assertLess(time.monotonic(), deadline)
                                    time.sleep(.01)
                            else:
                                self.await_barrier(terminal, marker)
                            began = time.monotonic()
                            os.killpg(terminal.process.pid, number)
                            self.assert_stopped(terminal, token, began)
                            self.assertEqual(git("--git-dir=.git/remote.git", "for-each-ref"), "")
                            self.assertEqual(before, (git("write-tree"), git("stash", "list"), git("status", "--porcelain")))
                            for run in set(root.glob("logs/prepush/*")) - previous:
                                summary = json.loads((run / "summary.json").read_text())
                                self.assertEqual(summary["invocation_mode"], "git")
                                self.assertEqual(summary["status"], "interrupted")
                        finally:
                            terminal.close()

    def test_grace_budget_and_repeated_signal_force_owned_probe(self):
        with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
            shim = Path(controls) / "git"
            real_git = subprocess.check_output(["which", "git"]).decode().strip()
            shim.write_text("""#!/usr/bin/env python3
import os, pathlib, signal, sys, time
if sys.argv[1:] == ['rev-parse', '--show-toplevel']:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    pathlib.Path(os.environ['FIXTURE_BARRIER']).write_text(str(os.getpid()))
    while True: time.sleep(.05)
os.execv(os.environ['FIXTURE_REAL_GIT'], ['git', *sys.argv[1:]])
""")
            shim.chmod(0o755)
            for repeated in (False, True):
                token = f"forced-probe-{time.monotonic_ns()}"
                marker = Path(controls) / token
                options = dict(env, PATH=controls + os.pathsep + env["PATH"],
                    FIXTURE_REAL_GIT=real_git, FIXTURE_BARRIER=str(marker), FIXTURE_TOKEN=token)
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
                try:
                    self.await_barrier(terminal, marker)
                    owner = execution.identity(int(marker.read_text()))["parent"]
                    began = time.monotonic()
                    os.write(terminal.master, b"\x03")
                    if repeated:
                        time.sleep(.1)
                        os.kill(owner, signal.SIGTERM)
                    self.assert_stopped(terminal, token, began)
                    elapsed = time.monotonic() - began
                    self.assertLess(elapsed, 5 if repeated else 10)
                    if not repeated:
                        self.assertGreaterEqual(elapsed, 5)
                    self.assertFalse((root / "logs/prepush").exists())
                finally:
                    terminal.close()

    def test_creation_owner_settles_after_frontend_and_job_clients_exit(self):
        for delay in ("1.2", "2.0"):
            with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
                token = f"late-create-{time.monotonic_ns()}"
                marker = Path(controls) / token
                options = dict(env, FIXTURE_TOKEN=token, FIXTURE_BARRIER=str(marker),
                    FIXTURE_CREATE_DELAY=delay)
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
                try:
                    self.await_barrier(terminal, marker)
                    began = time.monotonic()
                    os.write(terminal.master, b"\x03")
                    self.assert_stopped(terminal, token, began)
                    self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])
                    summary = json.loads(next(root.glob("logs/prepush/*/summary.json")).read_text())
                    self.assertEqual(summary["status"], "interrupted")
                    self.assertFalse(any("unconfirmed" in e for e in summary["errors"]), summary["errors"])
                    self.assertEqual(list(root.glob("logs/prepush/*/*.started")), [])
                    records = list(root.glob("logs/prepush/*/containers/*/create.done.json"))
                    self.assertTrue(records, "Creation acknowledgement did not outlive killed jobs")
                    self.assertEqual(git("status", "--porcelain"), "")
                finally:
                    terminal.close()

    def test_atomic_container_identity_publication_keeps_owned_cleanup(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with assembled() as (root, git, env), tempfile.TemporaryDirectory() as controls:
                self.instrument(root, git)
                token = f"atomic-id-{time.monotonic_ns()}"
                marker = Path(controls) / token
                options = dict(env, FIXTURE_TOKEN=token, FIXTURE_BARRIER=str(marker),
                    FIXTURE_PHASE="container-id-atomic")
                terminal = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
                try:
                    self.await_barrier(terminal, marker)
                    began = time.monotonic()
                    os.killpg(terminal.process.pid, number)
                    self.assert_stopped(terminal, token, began)
                    self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])
                    run = next(root.glob("logs/prepush/*"))
                    record = json.loads((run / "containers/stan/metadata.json").read_text())
                    self.assertEqual(record["cleanup"], "removed")
                    self.assertRegex(record["id"], "^[0-9a-f]{64}$")
                    self.assertEqual(json.loads((run / "summary.json").read_text())["status"], "interrupted")
                finally:
                    terminal.close()

    def test_repeated_interrupt_escalates_and_preserves_overlapping_run(self):
        with assembled() as (root, git, env):
            token = f"overlap-{time.monotonic_ns()}"
            options = dict(env, QA_TEST_HOLD="1", FIXTURE_TOKEN=token)
            first = Terminal([LEFTHOOK, "run", "pre-push"], root, options)
            second = Terminal([LEFTHOOK, "run", "pre-push"], root, dict(options, FIXTURE_TOKEN=token + "-second"))
            try:
                deadline = time.monotonic() + 10
                while len(list(root.glob("logs/prepush/*/*.started"))) < 12:
                    first.drain(); second.drain()
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                began = time.monotonic()
                os.write(first.master, b"\x03")
                time.sleep(.03)
                os.write(first.master, b"\x03")
                self.assert_stopped(first, token, began)
                self.assertIsNone(second.process.poll())
                self.assertTrue(live_fixture(token + "-second"))
                began = time.monotonic()
                os.write(second.master, b"\x03")
                self.assert_stopped(second, token + "-second", began)
                self.assertEqual(len(list(root.glob("logs/prepush/*/summary.json"))), 2)
            finally:
                first.close(); second.close()
