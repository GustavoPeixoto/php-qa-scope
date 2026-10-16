"""Run-owned Docker lifecycle; native commands need no container-side supervisor."""
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

from . import execution, reports

OWNER = "php-qa-scope.execution"
CHECK = "php-qa-scope.validation"
PROJECT = "php-qa-scope.project"
ID = re.compile(r"[0-9a-f]{64}\Z")


def query(root, args, timeout=None):
    result = execution.run(["docker", *args], cwd=root, capture_output=True,
                           timeout=timeout, control=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or "Docker operation failed")
    return result.stdout.decode()


def inspect(root, ids, timeout=None):
    data = json.loads(query(root, ["inspect", "--type", "container", *ids], timeout))
    if not isinstance(data, list) or len(data) != len(ids):
        raise ValueError("Invalid Docker container response")
    return data


def template(root, container_id=None, expected_image=None):
    if container_id is None:
        container_id = query(root, ["compose", "ps", "-q", "php"]).strip()
    if not ID.fullmatch(container_id):
        raise ValueError("QA requires one existing PHP service container")
    item = inspect(root, [container_id])[0]
    config = item["Config"]
    labels = config.get("Labels") or {}
    if (item["Id"] != container_id or not item["State"]["Running"]
            or labels.get("com.docker.compose.service") != "php"
            or not labels.get("com.docker.compose.project")
            or config.get("WorkingDir") != str(Path(root))
            or not isinstance(config.get("Env"), list)
            or not all(isinstance(v, str) and "=" in v for v in config["Env"])
            or not isinstance(config.get("User"), str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", item["Image"])
            or (expected_image and item["Image"] != expected_image)):
        raise ValueError("Invalid or changed active PHP runtime template")
    mounts = item.get("Mounts", [])
    if (not any(Path(root).is_relative_to(m["Destination"]) for m in mounts)
            or any(m["Type"] not in ("bind", "volume") for m in mounts)):
        raise ValueError("PHP runtime needs reusable workspace/dependency mounts")
    networks = item["NetworkSettings"]["Networks"]
    if not networks or any(not ID.fullmatch(n["NetworkID"]) for n in networks.values()):
        raise ValueError("PHP runtime needs existing project networks")
    query(root, ["image", "inspect", item["Image"]])
    for network in networks.values():
        query(root, ["network", "inspect", network["NetworkID"]])
    return item


def capabilities(root):
    for name, required in (("create", ("--init", "--label", "--volumes-from", "--pull")),
                           ("start", ()), ("logs", ("--follow",)), ("stop", ("--timeout",)), ("kill", ("--signal",)),
                           ("rm", ("--force", "--volumes")), ("ps", ("--all", "--format"))):
        text = query(root, [name, "--help"])
        if any(option not in text for option in required):
            raise ValueError(f"Docker {name} lacks required lifecycle options")


def configure(run, item):
    # Environment values are reused in memory, never copied into retained reports.
    context = {"execution_id": run.name, "owner": uuid.uuid4().hex,
               "template_id": item["Id"], "image": item["Image"],
               "project": item["Config"]["Labels"]["com.docker.compose.project"]}
    reports.atomic_json(run / "runtime.json", context)
    return context


def context(run):
    path = run / "runtime.json"
    if path.is_symlink():
        raise ValueError("Foreign runtime context")
    value = json.loads(path.read_text())
    if (value.get("execution_id") != run.name or not re.fullmatch(r"[0-9a-f]{32}", value.get("owner", ""))
            or not ID.fullmatch(value.get("template_id", "")) or not value.get("project")):
        raise ValueError("Invalid runtime context")
    return value


def name(ctx, check_id):
    if check_id not in reports.PHP_CHECKS:
        raise ValueError("Only registered PHP checks own containers")
    return f"qa-{ctx['owner']}-{check_id}"


def labels(ctx, check_id):
    return {OWNER: ctx["owner"], CHECK: check_id, PROJECT: ctx["project"]}


def path(run, check_id):
    return reports.directory(run, "containers", check_id) / "metadata.json"


def receipt(run, check_id):
    return reports.directory(run, "containers", check_id) / "create.done.json"


def load(run, ctx, check_id):
    file = path(run, check_id)
    if not file.exists():
        return None
    if file.is_symlink():
        raise ValueError("Symlink container identity")
    record = json.loads(file.read_text())
    if (record.get("execution_id") != run.name or record.get("validation_id") != check_id
            or record.get("name") != name(ctx, check_id) or record.get("labels") != labels(ctx, check_id)
            or (record.get("id") and not ID.fullmatch(record["id"]))):
        raise ValueError("Foreign container identity")
    return record


def update(run, ctx, check_id, **changes):
    reports.directory(run, "containers", check_id, create=True)
    record = load(run, ctx, check_id) or {
        "execution_id": run.name, "validation_id": check_id,
        "name": name(ctx, check_id), "labels": labels(ctx, check_id), "id": None,
        "state": "reserved", "creation_requested": False, "exit_code": None,
        "cleanup": "pending", "errors": [],
        "native_completion": "pending", "terminal_state": None,
        "start_client_exit_code": None, "log_collection": "pending",
    }
    record.update(changes)
    reports.atomic_json(path(run, check_id), record)
    return record


def create_args(item, ctx, check_id, native):
    config = item["Config"]
    networks = list(item["NetworkSettings"]["Networks"].values())
    args = ["docker", "create", "--init", "--pull", "never", "--name", name(ctx, check_id),
            "--volumes-from", item["Id"], "--network", networks[0]["NetworkID"],
            "--user", config["User"], "--workdir", config["WorkingDir"],
            "--entrypoint", native[0]]
    for key, value in labels(ctx, check_id).items():
        args.extend(["--label", f"{key}={value}"])
    for value in config["Env"]:
        args.extend(["--env", value])
    # Shared-service startup (often sleep infinity) is not a QA entrypoint.
    # This matches the direct native argv previously used by docker exec.
    return [*args, item["Image"], *native[1:]]


def owned(item, ctx, check_id):
    actual = item["Config"].get("Labels") or {}
    return (all(actual.get(k) == v for k, v in labels(ctx, check_id).items())
            and item["Name"].lstrip("/") == name(ctx, check_id)
            and ID.fullmatch(item["Id"]))


def execute(root, run, check_id, native, stdout, stderr):
    session = execution.CURRENT
    ctx = context(run)
    item = template(root, ctx["template_id"], ctx["image"])
    directory = reports.directory(run, "containers", check_id, create=True)
    execution.phase("container-intent")
    update(run, ctx, check_id)
    execution.phase("container-create")
    with (directory / "create.stdout.log").open("wb") as out, \
            (directory / "create.stderr.log").open("wb") as err:
        with session.atomic():
            update(run, ctx, check_id, state="creating", creation_requested=True)
            process = session.spawn(create_args(item, ctx, check_id, native), cwd=root,
                stdout=out, stderr=err, receipt=receipt(run, check_id))
        while process.poll() is None:
            session.check()
            time.sleep(.01)
        process.wait()
        session.children.pop(process, None)
        session.publish()
    execution.phase("container-acknowledgement")
    response = json.loads(receipt(run, check_id).read_text())
    if response["code"] != 0:
        detail = (directory / "create.stderr.log").read_text().strip()
        raise ValueError(detail or response.get("error") or "Container creation failed")
    container_id = (directory / "create.stdout.log").read_text().strip()
    if not ID.fullmatch(container_id):
        raise ValueError("Container creation returned no immutable ID")
    execution.phase("container-id-publication")
    update(run, ctx, check_id, id=container_id, state="created")
    actual = inspect(root, [container_id])[0]
    if not owned(actual, ctx, check_id) or actual["HostConfig"]["AutoRemove"] or not actual["HostConfig"]["Init"]:
        raise ValueError("Created container ownership/runtime mismatch")
    for network in list(item["NetworkSettings"]["Networks"].values())[1:]:
        query(root, ["network", "connect", network["NetworkID"], container_id])
    execution.phase("container-start")
    update(run, ctx, check_id, state="starting")
    session.check()
    execution.phase("native-command")
    started = execution.run(["docker", "start", container_id], cwd=root, capture_output=True)
    update(run, ctx, check_id, start_client_exit_code=started.returncode)
    if started.stderr:
        stderr.write(b"Docker startup diagnostics: " + started.stderr + b"\n")
        stderr.flush()
    while True:
        execution.phase("container-observation")
        actual = inspect(root, [container_id])[0]
        if not owned(actual, ctx, check_id):
            raise ValueError("Foreign native container state")
        state = actual["State"]
        if state.get("Status") == "exited":
            snapshot = terminal_state(state)
            execution.phase("container-completion")
            update(run, ctx, check_id, state="exited", native_completion="confirmed",
                   terminal_state=snapshot, exit_code=snapshot["ExitCode"])
            break
        if (state.get("Status") not in ("created", "running") or state.get("Restarting")
                or state.get("Error") or (started.returncode and state.get("Status") == "created")):
            update(run, ctx, check_id, native_completion="unknown")
            raise ValueError("Native container startup/state could not be confirmed")
        session.check()
        time.sleep(.05)
    execution.phase("container-log-collection")
    out_start, err_start = stdout.tell(), stderr.tell()
    try:
        result = execution.run(["docker", "logs", container_id], cwd=root, stdout=stdout, stderr=stderr)
        stdout.flush()
        stderr.flush()
        if result.returncode:
            raise ValueError("Native Docker log collection failed")
        execution.phase("container-logs-collected")
        update(run, ctx, check_id, log_collection="complete",
               stdout_bytes=stdout.tell() - out_start, stderr_bytes=stderr.tell() - err_start)
    except (OSError, ValueError):
        update(run, ctx, check_id, log_collection="failed")
        raise
    if snapshot["OOMKilled"] or snapshot["Error"]:
        raise ValueError("Native container reported an OOM/runtime failure")
    return snapshot["ExitCode"]


def terminal_state(state):
    """Require daemon evidence of an actually started and completed process."""
    from datetime import datetime
    selected = {key: state.get(key) for key in
                ("Status", "Running", "Restarting", "StartedAt", "FinishedAt", "ExitCode", "OOMKilled", "Error")}
    if (selected["Status"] != "exited" or selected["Running"] is not False
            or selected["Restarting"] is not False or type(selected["ExitCode"]) is not int
            or type(selected["OOMKilled"]) is not bool or not isinstance(selected["Error"], str)):
        raise ValueError("Malformed native terminal state")
    try:
        began = datetime.fromisoformat(selected["StartedAt"].replace("Z", "+00:00"))
        ended = datetime.fromisoformat(selected["FinishedAt"].replace("Z", "+00:00"))
        if began.year <= 1 or ended < began or began.tzinfo is None or ended.tzinfo is None:
            raise ValueError("Invalid native completion timestamps")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Missing/inconsistent native completion timestamps") from exc
    return selected


def completion_proof(run, check_id, record):
    """Cross-check native proof after the owned Docker object was removed."""
    proof = load(run, context(run), check_id)
    if (not proof or proof.get("id") != record.get("container_id")
            or not ID.fullmatch(proof.get("id") or "")
            or proof.get("native_completion") != "confirmed" or proof.get("log_collection") != "complete"
            or proof.get("cleanup") != "removed" or proof.get("exit_code") != record.get("exit_code")
            or terminal_state(proof.get("terminal_state") or {})["ExitCode"] != record.get("exit_code")
            or any(type(proof.get(k)) is not int or proof[k] < 0 for k in ("stdout_bytes", "stderr_bytes"))):
        raise ValueError("Missing/contradictory native completion or collection proof")
    if proof["terminal_state"]["OOMKilled"] or proof["terminal_state"]["Error"]:
        raise ValueError("Native runtime failure cannot pass")
    output = run / (record["report"] if check_id in ("qa-scope", "fixer", "stan") else f"results/{check_id}/stdout.log")
    diagnostics = run / record["diagnostics"]
    if (output.is_symlink() or not output.is_file() or output.stat().st_size != proof["stdout_bytes"]
            or diagnostics.stat().st_size < proof["stderr_bytes"]):
        raise ValueError("Native snapshot byte counts do not match retained output")


class Cleanup:
    """Reconcile Docker identities while local workers/creation owners settle."""
    def __init__(self, root, run, session, check_id=None):
        self.root, self.run, self.session, self.check_id = root, run, session, check_id
        self.started = session.started or time.monotonic()
        self.deadline = self.started + execution.LIMIT
        self.stops = {}
        self.errors = []
        self.ctx = None
        try:
            if check_id is not None and check_id not in reports.PHP_CHECKS:
                pass
            elif (run / "runtime.json").exists():
                self.ctx = context(run)
            elif any(file.exists() for key in reports.PHP_CHECKS
                     for file in (path(run, key), receipt(run, key))):
                raise ValueError("Missing runtime ownership context")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.fail(str(exc))
        self.complete = self.ctx is None and not self.errors
        self.last_check = 0.0

    def remaining(self):
        if self.session.started:
            self.deadline = min(self.deadline, self.session.started + execution.LIMIT)
        # Reserve bounded time to reap clients, publish evidence, and return
        # through the guardian inside the same ten-second user-visible budget.
        return max(.001, self.deadline - time.monotonic() - .7)

    def rpc(self, args):
        return query(self.root, args, self.remaining())

    def fail(self, message):
        text = f"Container cleanup unconfirmed: {message}"
        if text not in self.errors:
            self.errors.append(text)

    def creation_settled(self, check_id, record):
        if not record or not record.get("creation_requested"):
            return True
        file = receipt(self.run, check_id)
        if file.is_file() and not file.is_symlink():
            response = json.loads(file.read_text())
            return type(response.get("code")) is int or response.get("error") is not None
        # The command cannot pass the local gate before its ownership is recorded.
        for file in (self.run / "processes" / "local").glob("*.json"):
            local = json.loads(file.read_text())
            if local.get("execution_id") != self.run.name:
                raise ValueError("Foreign creation-request owner")
            for child in local.get("children", []):
                if child.get("receipt") == str(receipt(self.run, check_id)):
                    return False
        return True

    def tick(self):
        if self.ctx is None:
            return
        now = time.monotonic()
        if now - self.last_check < .08:
            return
        self.last_check = now
        self.complete = False
        try:
            execution.phase("container-reconcile")
            selected = ([self.check_id] if self.check_id in reports.PHP_CHECKS else []) if self.check_id else list(reports.PHP_CHECKS)
            records = {key: load(self.run, self.ctx, key) for key in selected}
            ids = {r["id"] for r in records.values() if r and r.get("id")}
            names = {name(self.ctx, key) for key in selected}
            rows = self.rpc(["ps", "-a", "--no-trunc", "--format", "{{json .}}"])
            candidates = []
            for line in rows.splitlines():
                row = json.loads(line)
                labelled = f"{OWNER}={self.ctx['owner']}" in row.get("Labels", "").split(",")
                if row["ID"] in ids or row["Names"].lstrip("/") in names or labelled:
                    candidates.append(row["ID"])
            live = []
            if candidates:
                raw = json.loads(self.rpc(["inspect", "--type", "container", *candidates]))
                for item in raw:
                    key = (item["Config"].get("Labels") or {}).get(CHECK)
                    if key not in reports.PHP_CHECKS or not owned(item, self.ctx, key):
                        raise ValueError("Foreign container ownership; refusing removal")
                    if key not in selected:
                        continue
                    if records[key] and records[key].get("id") not in (None, item["Id"]):
                        raise ValueError("Container immutable identity changed")
                    update(self.run, self.ctx, key, id=item["Id"], cleanup="pending")
                    live.append(item)
            force = self.session.repeated or time.monotonic() - self.started >= execution.GRACE
            execution.phase("container-removal")
            for item in live:
                container_id = item["Id"]
                if not item["State"]["Running"] or force:
                    if item["State"]["Running"] and force:
                        try:
                            self.rpc(["kill", container_id])
                        except ValueError as exc:
                            if "is not running" not in str(exc).lower():
                                raise
                    self.rpc(["rm", "-f", "-v", container_id])
                elif container_id not in self.stops:
                    log = (reports.directory(self.run, "containers", item["Config"]["Labels"][CHECK])
                           / "cleanup.log").open("ab")
                    try:
                        process = self.session.spawn(["docker", "stop", "--timeout",
                            str(max(0, int(execution.GRACE - (time.monotonic() - self.started)))),
                            container_id], cwd=self.root, stdout=log, stderr=log, control=True)
                        self.stops[container_id] = process
                    finally:
                        log.close()
            for container_id, process in list(self.stops.items()):
                if process.poll() is not None:
                    process.wait()
                    self.session.children.pop(process, None)
                    self.stops.pop(container_id)
            settled = all(self.creation_settled(key, record) for key, record in records.items())
            execution.phase("container-absence")
            if not live and settled:
                for key, record in records.items():
                    if record:
                        update(self.run, self.ctx, key, state="removed", cleanup="removed", errors=[])
                self.complete = True
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            # AutoRemove can win between a successful list and inspect/remove.
            # Re-query the daemon before absence is confirmed; connectivity and
            # unrelated errors must never be swallowed as a missing container.
            if not re.search(r"no such (container|object)|removal of container .+ is already in progress", str(exc), re.I):
                self.fail(str(exc))

    def finish(self):
        while self.ctx is not None and not self.complete and time.monotonic() < self.deadline - .7:
            self.tick()
            if not self.complete:
                time.sleep(.02)
        if not self.complete:
            self.fail("owned container absence or creation completion was not confirmed within deadline")
        for container_id, process in list(self.stops.items()):
            if process.poll() is None:
                execution.signal_owned(self.session.children.get(process), 9, True)
            try:
                process.wait(timeout=max(.001, min(.1, self.remaining())))
            except subprocess.TimeoutExpired:
                self.fail("cleanup control process could not be reaped")
            self.session.children.pop(process, None)
        if self.ctx:
            selected = ([self.check_id] if self.check_id in reports.PHP_CHECKS else []) if self.check_id else list(reports.PHP_CHECKS)
            if self.errors:
                for key in selected:
                    try:
                        if load(self.run, self.ctx, key):
                            update(self.run, self.ctx, key, cleanup="unconfirmed", errors=self.errors)
                    except (OSError, ValueError):
                        pass
            self.session.errors.extend(e for e in self.errors if e not in self.session.errors)
        return self.complete and not self.errors


def cleanup(root, run, session, check_id=None):
    owner = Cleanup(root, run, session, check_id)
    owner.tick()
    return owner.finish()
