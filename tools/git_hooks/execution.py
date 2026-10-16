"""Cancellation and verified ownership for one invocation, never QA scheduling."""
from contextlib import contextmanager
import io
import stat
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

CURRENT = None
GRACE = 5.0
LIMIT = 10.0
GATED_EXEC = """
import json,os,signal,subprocess,sys,tempfile
fd=int(sys.argv[1]); ready=os.read(fd,1); os.close(fd)
receipt=sys.argv[2]; args=sys.argv[3:]
if ready != b'1':
    if receipt != '-':
        with tempfile.NamedTemporaryFile(mode='w',dir=os.path.dirname(receipt),delete=False) as handle:
            json.dump({'code':None,'error':'Creation gate never started'},handle); name=handle.name
        os.replace(name,receipt)
    sys.exit(1)
if receipt == '-': os.execvpe(args[0],args,os.environ)
# A local create-request owner outlives a hard-killed Lefthook job. Its
# acknowledgement must settle before container absence can be confirmed.
signal.signal(signal.SIGINT,signal.SIG_IGN)
signal.signal(signal.SIGTERM,signal.SIG_IGN)
try: code=subprocess.run(args).returncode; error=None
except OSError as exc: code=None; error=str(exc)
with tempfile.NamedTemporaryFile(mode='w',dir=os.path.dirname(receipt),delete=False) as handle:
    json.dump({'code':code,'error':error},handle); name=handle.name
os.replace(name,receipt)
sys.exit(code if code is not None and code >= 0 else 1)
"""


class Interrupted(Exception):
    def __init__(self, number):
        self.number = number
        super().__init__(f"Interrupted by signal {number}")


def identity(pid):
    """Linux start time prevents reusing an unrelated process ID."""
    try:
        fields = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
        return {"pid": int(pid), "parent": int(fields[1]), "start": fields[19], "group": int(fields[2]),
                "session": int(fields[3]), "state": fields[0]}
    except (OSError, ValueError, IndexError):
        return None


def alive(record):
    current = identity(record["pid"]) if record else None
    return bool(current and current["start"] == record["start"] and current["state"] != "Z")


def members(record):
    """A dedicated session remains owned after its leader exits."""
    if not record or record["session"] != record["pid"]:
        return [record] if alive(record) else []
    current = identity(record["pid"])
    if current and current["start"] != record["start"]:
        return []
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdecimal():
            item = identity(int(entry.name))
            if (item and item["session"] == record["session"] and item["state"] != "Z"
                    and int(item["start"]) >= int(record["start"])):
                found.append(item)
    return found


def signal_owned(record, number, group=False):
    if group:
        for item in members(record):
            signal_owned(item, number)
        return
    if not alive(record):
        return
    try:
        os.kill(record["pid"], number)
    except ProcessLookupError:
        pass


class Session:
    def __init__(self):
        self.number = None
        self.started = None
        self.repeated = False
        self.finishing = False
        self.depth = 0
        self.children = {}
        self.run_dir = None
        self.errors = []
        self.phase_name = "entry"
        self.job_id = None
        self.force_published = False

    def __enter__(self):
        global CURRENT
        self.previous = CURRENT
        CURRENT = self
        self.handlers = {n: signal.signal(n, self.interrupt)
                         for n in (signal.SIGINT, signal.SIGTERM)}
        return self

    def __exit__(self, *unused):
        global CURRENT
        for number, handler in self.handlers.items():
            signal.signal(number, handler)
        CURRENT = self.previous

    def interrupt(self, number, frame):
        if self.number is None:
            self.number, self.started = number, time.monotonic()
        else:
            self.repeated = True
        if not self.depth and not self.finishing:
            raise Interrupted(self.number)

    def check(self):
        if self.finishing and self.repeated and self.run_dir and not self.depth and not self.force_published:
            from . import reports
            marker = self.run_dir / (f"{self.job_id}.cancel.json" if self.job_id else "cancel.json")
            if marker.is_file():
                self.force_published = True
                request = json.loads(marker.read_text())
                request["force"] = True
                reports.atomic_json(marker, request)
        if self.run_dir and self.job_id and not self.finishing and not self.depth:
            marker = self.run_dir / "cancel.json"
            if marker.is_file():
                request = json.loads(marker.read_text())
                if request.get("execution_id") != self.run_dir.name:
                    raise ValueError("Foreign cancellation request")
                self.number = request.get("signal") or signal.SIGTERM
                began = time.monotonic() - max(0, LIMIT - (request["deadline"] - time.time()))
                self.started = min(self.started, began) if self.started else began
                self.repeated = self.repeated or bool(request.get("force"))
        if self.number and not self.finishing and not self.depth:
            raise Interrupted(self.number)

    def phase(self, name):
        self.phase_name = name
        self.check()

    @contextmanager
    def atomic(self):
        self.depth += 1
        try:
            yield
        finally:
            self.depth -= 1
        self.check()

    def attach(self, run, job_id=None):
        self.run_dir = Path(run)
        self.job_id = job_id
        if job_id is None:
            from . import reports
            (self.run_dir / "processes").mkdir(exist_ok=True)
            reports.atomic_json(self.run_dir / "processes" / "coordinator.json", {
                "execution_id": self.run_dir.name, "process": identity(os.getpid()),
            })
        self.publish()

    def publish(self):
        if self.run_dir and self.job_id:
            from . import reports
            directory = self.run_dir / "processes" / "local"
            directory.mkdir(parents=True, exist_ok=True)
            reports.atomic_json(directory / f"{self.job_id}.json", {
                "execution_id": self.run_dir.name, "validation_id": self.job_id,
                "process": identity(os.getpid()), "children": list(self.children.values()),
            })

    def spawn(self, args, *, cwd=None, env=None, stdout=None, stderr=None,
              input=None, receipt=None, control=False):
        self.check()
        with self.atomic():
            read_fd, write_fd = os.pipe()
            try:
                # No external command starts before ownership is published. A
                # hard-killed job closes the pipe and the unused gate exits.
                process = subprocess.Popen([sys.executable, "-c", GATED_EXEC, str(read_fd),
                    str(receipt) if receipt else "-", *args],
                    cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                    stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                    start_new_session=True, pass_fds=(read_fd,))
                self.children[process] = identity(process.pid)
                self.children[process].update(receipt=str(receipt) if receipt else None, control=control)
                self.publish()
                os.write(write_fd, b"1")
            finally:
                os.close(read_fd)
                os.close(write_fd)
        return process

    def run(self, args, *, cwd=None, env=None, capture_output=False,
            stdout=None, stderr=None, input=None, timeout=None, receipt=None, control=False):
        if capture_output:
            stdout, stderr = subprocess.PIPE, subprocess.PIPE
        process = self.spawn(args, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                             input=input, receipt=receipt, control=control)
        began = time.monotonic()
        first = True
        while True:
            self.check()
            try:
                out, err = process.communicate(input=input if first else None, timeout=.05)
                if not members(self.children[process]):
                    self.children.pop(process, None)
                self.publish()
                return subprocess.CompletedProcess(args, process.returncode, out, err)
            except subprocess.TimeoutExpired:
                first = False
                if timeout is not None and time.monotonic() - began >= timeout:
                    signal_owned(self.children[process], signal.SIGKILL, True)
                    process.wait()
                    self.children.pop(process, None)
                    for stream in (process.stdin, process.stdout, process.stderr):
                        if stream and not stream.closed:
                            stream.close()
                    raise subprocess.TimeoutExpired(args, timeout)

    def teardown(self):
        """Bound the whole local cleanup, including registered Lefthook jobs."""
        self.finishing = True
        if self.started is None:
            self.started = time.monotonic()
        records = [r for r in self.children.values() if not r.get("control")]
        if self.run_dir:
            from . import reports
            marker = f"{self.job_id}.cancel.json" if self.job_id else "cancel.json"
            reports.atomic_json(self.run_dir / marker, {
                "execution_id": self.run_dir.name, "signal": self.number,
                "deadline": time.time() + max(0, LIMIT - (time.monotonic() - self.started)),
                "force": self.repeated,
            })
            self.force_published = self.repeated
        def terminate(record, number):
            if record.get("control"):
                return
            receipt = record.get("receipt")
            if receipt and not Path(receipt).is_file():
                if time.monotonic() - self.started < LIMIT - 1.0:
                    return
                message = "Container creation request did not settle within deadline"
                if message not in self.errors:
                    self.errors.append(message)
            signal_owned(record, number, True)

        def discover():
            files = [] if self.job_id or not self.run_dir else (self.run_dir / "processes" / "local").glob("*.json")
            for file in files:
                try:
                    if file.is_symlink():
                        raise ValueError("Symlink local process identity")
                    item = json.loads(file.read_text())
                    if (item.get("execution_id") != self.run_dir.name
                            or item.get("validation_id") + ".json" != file.name):
                        raise ValueError("Foreign local process identity")
                    for record in [item["process"], *item.get("children", [])]:
                        if record and record.get("control"):
                            continue
                        if not any(known and record and known["pid"] == record["pid"]
                                   and known["start"] == record["start"] for known in records):
                            records.append(record)
                            terminate(record, signal.SIGTERM)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    message = f"Cannot verify local process identity: {exc}"
                    if message not in self.errors:
                        self.errors.append(message)
        discover()
        for record in records:
            terminate(record, signal.SIGTERM)
        cleanup = None
        if self.run_dir:
            from . import containers
            cleanup = containers.Cleanup(self.run_dir.parents[2], self.run_dir, self, self.job_id)
            cleanup.tick()
        while True:
            # Jobs can publish a child while their scheduler is shutting down.
            # Re-read after the scheduler's death before declaring local cleanup.
            discover()
            if cleanup:
                cleanup.tick()
            if not any(members(record) for record in records):
                break
            elapsed = time.monotonic() - self.started
            if elapsed >= GRACE or self.repeated:
                if self.run_dir and self.repeated:
                    request = json.loads((self.run_dir / marker).read_text())
                    request["force"] = True
                    reports.atomic_json(self.run_dir / marker, request)
                    self.force_published = True
                for record in records:
                    terminate(record, signal.SIGKILL)
            if elapsed >= LIMIT - .2:
                self.errors.append("Local process teardown deadline exceeded")
                break
            time.sleep(.02)
        if cleanup:
            cleanup.finish()
        for process in list(self.children):
            try:
                process.wait(timeout=max(.001, min(.1, LIMIT - (time.monotonic() - self.started))))
            except subprocess.TimeoutExpired:
                self.errors.append("Owned process could not be reaped")
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream and not stream.closed:
                    stream.close()
        self.children.clear()


def run(args, **kwargs):
    if CURRENT:
        return CURRENT.run(args, **kwargs)
    kwargs.pop("control", None)
    kwargs.pop("receipt", None)
    return subprocess.run(args, **kwargs)


def phase(name):
    if CURRENT:
        CURRENT.phase(name)


def read(stream):
    """Signals can interrupt input even when a pipe never reaches EOF."""
    if isinstance(stream, io.StringIO) or not CURRENT:
        return stream.read()
    chunks = []
    if stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        CURRENT.check()
        return stream.read()
    with selectors.DefaultSelector() as selector:
        try:
            selector.register(stream.fileno(), selectors.EVENT_READ)
        except PermissionError:
            return stream.read()
        while True:
            CURRENT.check()
            if not selector.select(.05):
                continue
            data = os.read(stream.fileno(), 65536)
            if not data:
                return b"".join(chunks).decode("utf-8")
            chunks.append(data)


def boundary(mode, frontend_pid):
    """Keep cleanup alive when Lefthook kills its command shell or frontend."""
    frontend = identity(frontend_pid)
    parent = identity(os.getppid())
    if not frontend or not parent or parent["parent"] != frontend["pid"]:
        print("Pre-push rejected: missing managed frontend identity", file=sys.stderr)
        return 1
    try:
        command = Path(f"/proc/{frontend['pid']}/cmdline").read_bytes().split(b"\0")
    except OSError:
        command = []
    if not command or b"lefthook" not in command[0] or b"pre-push" not in command:
        print("Pre-push rejected: invalid managed frontend identity", file=sys.stderr)
        return 1
    wrapper = identity(frontend["parent"])
    if wrapper:
        try:
            argv = Path(f"/proc/{wrapper['pid']}/cmdline").read_bytes().split(b"\0")
        except OSError:
            argv = []
        if not any(b"lefthook" in argument for argument in argv) or b"pre-push" not in argv:
            wrapper = None
    numbers = []
    previous = {}
    child = None
    def stop(number, frame):
        numbers.append(number)
    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            previous[number] = signal.signal(number, stop)
        # Lefthook may kill its command's whole foreground group. The guardian
        # must survive that group and detect the verified parent's termination.
        if os.getsid(0) != os.getpid():
            os.setsid()
        pid = os.fork()
        if pid == 0:
            os.setsid()
            for number, handler in previous.items():
                signal.signal(number, handler)
            from . import runner
            try:
                code = runner.main(["pre-push", mode])
            except KeyboardInterrupt:
                code = 130
            # The native frontend can close its capture pipe during cancellation.
            for stream in (sys.stdout, sys.stderr):
                try:
                    stream.flush()
                except OSError:
                    code = 1
            os._exit(code)
        child = identity(pid)
        while child and child["group"] != pid:
            time.sleep(.001)
            child = identity(pid)
        cancellation = None
        forwarded = 0
        while True:
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                code = os.waitstatus_to_exitcode(status)
                break
            if numbers or not alive(frontend) or not alive(parent) or (wrapper and not alive(wrapper)):
                if cancellation is None:
                    cancellation = time.monotonic()
                if forwarded < len(numbers):
                    for number in numbers[forwarded:]:
                        signal_owned(child, number)
                    forwarded = len(numbers)
                elif not numbers and forwarded == 0:
                    signal_owned(child, signal.SIGTERM)
                    forwarded = 1
            if cancellation and time.monotonic() - cancellation >= LIMIT - .1:
                signal_owned(child, signal.SIGKILL, True)
            time.sleep(.01)
        if cancellation is not None or numbers:
            # Lefthook may still be copying an open stdin after its job exited.
            signal_owned(frontend, signal.SIGTERM)
            return 1
        return max(0, code) if code >= 0 else 1
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)
