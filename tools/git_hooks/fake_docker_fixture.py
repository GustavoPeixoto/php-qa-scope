#!/usr/bin/env python3
"""Disposable test Docker daemon state and native work, never production tooling."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

args = sys.argv[1:]
engine = Path(os.environ["FIXTURE_ENGINE"])
engine.mkdir(exist_ok=True)
root = str(Path.cwd())
TEMPLATE = "a" * 64
IMAGE = "sha256:" + "b" * 64
NETWORK = "c" * 64


def die(text, code=1):
    print(text, file=sys.stderr)
    raise SystemExit(code)


def read(cid):
    return json.loads((engine / (cid + ".json")).read_text())


def write(cid, record):
    temporary = engine / (cid + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(record))
    temporary.replace(engine / (cid + ".json"))


def native_alive(pid):
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
        return state != "Z"
    except OSError:
        return False


def remove(cid):
    try:
        record = read(cid)
        if record.get("pid") and native_alive(record["pid"]):
            os.killpg(record["pid"], signal.SIGKILL)
        (engine / (cid + ".json")).unlink(missing_ok=True)
    except FileNotFoundError:
        pass


if os.environ.get("FIXTURE_PROBE") == " ".join(args):
    Path(os.environ["FIXTURE_BARRIER"]).write_text(str(os.getpid()))
    while True:
        time.sleep(.05)
if args == ["compose", "version"]:
    print("Docker Compose fixture")
elif args[:3] == ["compose", "ps", "--services"]:
    print("php")
elif args == ["compose", "ps", "-q", "php"]:
    print(TEMPLATE)
elif args and args[0] in ("create", "start", "logs", "stop", "kill", "rm", "ps") and "--help" in args:
    print("--rm --init --label --volumes-from --pull --attach --follow --timeout --signal --force --volumes --all --format")
elif args[:2] in (["image", "inspect"], ["network", "inspect"]):
    print("[]")
elif args[:3] == ["inspect", "--type", "container"]:
    records = []
    for cid in args[3:]:
        if cid == TEMPLATE:
            records.append({"Id": TEMPLATE, "Image": IMAGE, "Name": "/fixture-php",
                "Config": {"User": "dev", "WorkingDir": root,
                    "Env": ["FIXTURE_RUNTIME=value"], "Entrypoint": [],
                    "Labels": {"com.docker.compose.service": "php", "com.docker.compose.project": "fixture"}},
                "State": {"Running": True}, "Mounts": [{"Type": "bind", "Destination": root, "RW": True}],
                "NetworkSettings": {"Networks": {"fixture": {"NetworkID": NETWORK}}},
                "HostConfig": {"AutoRemove": False, "Init": False}})
        else:
            try:
                record = read(cid)
            except FileNotFoundError:
                die("No such container: " + cid)
            records.append(record)
    print(json.dumps(records))
elif args[:2] == ["compose", "exec"]:
    if "sh" in args or "--version" in args:
        raise SystemExit(0)
    die("QA must not execute inside the shared PHP service")
elif args[:2] == ["ps", "-a"]:
    if os.environ.get("QA_TEST_PHP_FAIL") == "1" and next(Path(root).glob("logs/prepush/*/cancel.json"), None):
        die("Docker daemon unreachable")
    for file in engine.glob("*.json"):
        record = json.loads(file.read_text())
        print(json.dumps({"ID": record["Id"], "Names": record["Name"].lstrip("/"),
            "Labels": ",".join(k + "=" + v for k, v in record["Config"]["Labels"].items())}))
elif args and args[0] == "create":
    if os.environ.get("FIXTURE_CREATE_FAIL") == "1":
        die("Controlled creation failure")
    container_name = args[args.index("--name") + 1]
    if any(json.loads(file.read_text())["Name"].lstrip("/") == container_name for file in engine.glob("*.json")):
        die("Error response from daemon: container name is already in use")
    labels = {}
    for n, arg in enumerate(args):
        if arg == "--label":
            key, value = args[n + 1].split("=", 1)
            labels[key] = value
    if os.environ.get("FIXTURE_CREATE_DELAY"):
        marker = Path(os.environ["FIXTURE_BARRIER"])
        marker.write_text(str(os.getpid()))
        time.sleep(float(os.environ["FIXTURE_CREATE_DELAY"]))
    cid = uuid.uuid4().hex * 2
    command = [args[args.index("--entrypoint") + 1], *args[args.index(IMAGE) + 1:]]
    record = {"Id": cid, "Image": IMAGE, "Name": "/" + container_name,
        "Config": {"Labels": labels}, "State": {"Running": False, "Status": "created", "Restarting": False,
            "StartedAt": "0001-01-01T00:00:00Z", "FinishedAt": "0001-01-01T00:00:00Z",
            "ExitCode": 0, "OOMKilled": False, "Error": ""},
        "HostConfig": {"AutoRemove": "--rm" in args, "Init": True}, "command": command, "pid": None,
        "fixture_token": os.environ.get("FIXTURE_TOKEN")}
    write(cid, record)
    print(cid)
elif args[:2] == ["network", "connect"]:
    pass
elif args and args[0] == "start":
    if os.environ.get("FIXTURE_START_FAIL") == "1":
        die("Error response from daemon: controlled startup failure")
    cid = args[-1]
    try:
        record = read(cid)
    except FileNotFoundError:
        die("No such container: " + cid)
    native_env = dict(os.environ)
    native_env.pop("FIXTURE_TOKEN", None)
    child = subprocess.Popen([sys.executable, __file__, "fixture-monitor", cid], env=native_env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    (engine / "actors").mkdir(exist_ok=True)
    fields = Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()
    (engine / "actors" / (cid + ".json")).write_text(json.dumps({
        "pid": child.pid, "start": fields[19], "group": child.pid, "session": child.pid,
        "token": record.get("fixture_token")}))
    record["pid"] = child.pid
    record["State"]["Running"] = True
    record["State"].update(Status="running", StartedAt=datetime.now(timezone.utc).isoformat())
    if not (engine / (cid + ".json")).exists():
        child.kill()
        child.wait()
        die("No such container: " + cid)
    write(cid, record)
    print(cid)
elif args and args[0] == "fixture-monitor":
    cid = args[1]
    while read(cid).get("pid") != os.getpid():
        time.sleep(.005)
    with (engine / (cid + ".stdout")).open("wb") as out, (engine / (cid + ".stderr")).open("wb") as err:
        child = subprocess.Popen([sys.executable, __file__, "fixture-native", cid], stdout=out, stderr=err)
        record = read(cid)
        record["native_pid"] = child.pid
        write(cid, record)
        code = child.wait()
    try:
        record = read(cid)
        record["State"].update(Running=False, Status="exited", ExitCode=max(0, code),
                               FinishedAt=datetime.now(timezone.utc).isoformat())
        write(cid, record)
    except FileNotFoundError:
        pass
elif args and args[0] == "logs":
    cid = args[-1]
    if os.environ.get("FIXTURE_LOG_FAIL") == "1":
        die("Controlled log snapshot failure")
    out = (engine / (cid + ".stdout")).read_bytes()
    err = (engine / (cid + ".stderr")).read_bytes()
    sys.stdout.buffer.write(out[:5] if os.environ.get("FIXTURE_LOG_TRUNCATE") == "1" else out)
    sys.stderr.buffer.write(err)
elif args and args[0] == "stop":
    cid = args[-1]
    try:
        record = read(cid)
    except FileNotFoundError:
        die("No such container: " + cid)
    pid = record.get("pid")
    if pid and native_alive(pid):
        os.killpg(pid, signal.SIGTERM)
    deadline = time.monotonic() + int(args[args.index("--timeout") + 1])
    while pid and native_alive(pid) and time.monotonic() < deadline:
        time.sleep(.01)
    remove(cid)
elif args and args[0] in ("rm", "kill"):
    remove(args[-1])
elif args and args[0] == "fixture-native":
    cid = args[1]
    while True:
        try:
            record = read(cid)
        except FileNotFoundError:
            raise SystemExit(1)
        if record.get("native_pid") == os.getpid():
            break
        time.sleep(.005)
    run = Path(os.environ["QA_HOOKS_RUN_DIR"])
    key = record["Config"]["Labels"]["php-qa-scope.validation"]
    command = record["command"]
    (run / (key + ".started")).touch()
    deadline = time.monotonic() + 15
    while os.environ.get("FIXTURE_ONE_CHECK") != "1" and len(list(run.glob("*.started"))) != 6:
        if time.monotonic() > deadline:
            die("Six-job concurrency barrier timed out", 99)
        time.sleep(.01)
    if os.environ.get("QA_TEST_HOLD") == "1":
        while True:
            time.sleep(.1)
    print("Composer fixture diagnostics", file=sys.stderr)
    if key == "qa-scope":
        print("OK phpstan.neon\nOK phpcs.xml\nOK php-cs-fixer.dist.php")
    elif key == "fixer":
        print('{"files": [], "about": "PHP CS Fixer fixture"}')
    elif key == "stan":
        print('{"totals": {"errors": 0, "file_errors": 0}, "files": {}, "errors": []}')
    elif key == "sniffer":
        Path(next(v.split("=", 1)[1] for v in command if v.startswith("--report-file="))).write_text('{"totals": {"errors": 0, "warnings": 0, "fixable": 0}, "files": {}}')
    elif key == "md":
        Path(command[command.index("--reportfile-json") + 1]).write_text('{"package": "phpmd", "files": []}')
    else:
        Path(command[command.index("--log-junit") + 1]).write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="fixture"/></testsuite></testsuites>')
    raise SystemExit(1 if os.environ.get("QA_TEST_FAIL") == key else 0)
else:
    die("Unsupported fixture Docker operation: " + repr(args))
