"""One synchronous native validation per Lefthook job."""
import json
import os
import shutil
import time
import xml.etree.ElementTree as ET

from . import containers, execution, reports


def command(check_id, run):
    if check_id == "openspec":
        return ["openspec", "validate", "--all", "--strict", "--no-interactive", "--json"]
    report = str(run / reports.CHECKS[check_id][1])
    adapters = {
        "qa-scope": ["qa-scope", "--", "check"],
        "sniffer": ["sniffer-check", "--", "--report=json", f"--report-file={report}",
                    "--no-colors", "-q"],
        "fixer": ["fixer-check", "--", "--format=json", "--no-ansi", "--show-progress=none"],
        "md": ["md-check", "--", "--reportfile-json", report],
        "stan": ["stan-check", "--", "--error-format=json", "--no-progress", "--no-ansi"],
        "test": ["test", "--", "--log-junit", report, "--colors=never"],
    }
    return ["composer",
            "--no-interaction", "--no-ansi", *adapters[check_id]]


def check(root, check_id, env=None):
    if execution.CURRENT is None:
        with execution.Session():
            return check(root, check_id, env)
    run = reports.context(root, os.environ if env is None else env, check_id)
    session = execution.CURRENT
    session.attach(run, check_id)
    record = reports.outcome(run, check_id)
    started = time.monotonic()
    primary = run / record["report"]
    diagnostics = run / record["diagnostics"]
    local = check_id == "openspec"
    stdout_report = check_id in ("qa-scope", "fixer", "stan", "openspec")
    directory = reports.directory(run, "results", check_id, create=True)
    temporary = directory / "stdout.log"
    error = None
    code = None
    valid = False
    interrupted = False
    try:
        reports.write_result(run, record)
        with diagnostics.open("wb") as stderr, temporary.open("wb") as stdout:
            if local:
                execution.phase("openspec-launch")
                if not shutil.which("openspec"):
                    raise FileNotFoundError("OpenSpec 1.14.0 is unavailable in dev")
                code = execution.run(command(check_id, run), cwd=root, stdout=stdout, stderr=stderr).returncode
                execution.phase("openspec-report")
            else:
                code = containers.execute(root, run, check_id, command(check_id, run), stdout, stderr)
        execution.phase("native-report")
        if stdout_report:
            # Validate JSON before publishing; retain invalid stdout as diagnostics.
            if check_id != "qa-scope":
                with temporary.open(encoding="utf-8") as handle:
                    native = json.load(handle)
                if not isinstance(native, (dict, list)):
                    raise ValueError("Invalid native JSON report")
            if local:
                reports.valid_openspec(temporary, root, code)
            else:
                reports.valid_native(temporary, check_id, code)
            with session.atomic():
                os.replace(temporary, primary)
        else:
            with diagnostics.open("ab") as handle, temporary.open("rb") as captured:
                shutil.copyfileobj(captured, handle)
        if local:
            reports.valid_report(primary)
        else:
            reports.valid_native(primary, check_id, code)
        valid = True
    except execution.Interrupted:
        interrupted = True
        session.teardown()
        error = f"Interrupted by signal {session.number}"
        if session.errors:
            error += "; " + "; ".join(session.errors)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        error = f"Execution/report failure: {exc}"
        with diagnostics.open("ab") as handle:
            handle.write((error + "\n").encode())
            if stdout_report and temporary.exists():
                with temporary.open("rb") as invalid:
                    shutil.copyfileobj(invalid, handle)
    try:
        if local:
            if session.children:
                session.teardown()
            cleaned = not session.errors
        else:
            cleaned = containers.cleanup(root, run, session, check_id)
    except execution.Interrupted:
        interrupted = True
        session.teardown()
        cleaned = not session.errors
    if session.errors:
        error = "; ".join(([error] if error else []) + session.errors)
    container_record = None
    if not local and (run / "runtime.json").exists():
        try:
            container_record = containers.load(run, containers.context(run), check_id)
            if container_record and container_record.get("native_completion") == "confirmed" and code is None:
                code = container_record["exit_code"]
            elif container_record and code is None:
                container_record = containers.update(run, containers.context(run), check_id, native_completion="unknown")
            if interrupted and container_record and container_record.get("log_collection") == "pending":
                container_record = containers.update(run, containers.context(run), check_id, log_collection="interrupted")
        except (OSError, ValueError):
            cleaned = False
    record.update(status="interrupted" if interrupted else ("passed" if code == 0 and valid else "failed"), exit_code=code,
                  duration_seconds=time.monotonic() - started, report_valid=valid, error=error)
    record.update(container_id=container_record.get("id") if container_record else None,
                  container_cleanup="not_applicable" if local else "unconfirmed" if not cleaned else
                      (container_record.get("cleanup") if container_record else "not_created"))
    if not cleaned and not interrupted:
        record["status"] = "failed"
    try:
        execution.phase("result-publication")
        reports.write_result(run, record)
    except execution.Interrupted:
        session.teardown()
        record.update(status="interrupted", error=f"Interrupted by signal {session.number}")
        reports.write_result(run, record)
    return 0 if record["status"] == "passed" else 1
