"""Independent run evidence and coordinator-owned summaries."""
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from . import execution

CHECKS = {
    "qa-scope": ("QA Scope", "results/qa-scope/result.log"),
    "sniffer": ("Sniffer", "results/sniffer/result.json"),
    "fixer": ("Fixer", "results/fixer/result.json"),
    "md": ("PHPMD", "results/md/result.json"),
    "stan": ("PHPStan", "results/stan/result.json"),
    "test": ("tests", "results/test/result.junit.xml"),
    "openspec": ("OpenSpec", "results/openspec/result.json"),
}
PHP_CHECKS = tuple(key for key in CHECKS if key != "openspec")
BACKENDS = {key: "php-container" if key in PHP_CHECKS else "dev-process" for key in CHECKS}
RUN_NAME = re.compile(r"\d{8}-\d{6}-\d{3}\Z")


def utc_now():
    return datetime.now(timezone.utc)


def directory(run, namespace, check_id=None, *, create=False):
    """Resolve run-local directories without following artifact symlinks."""
    if namespace not in ("jobs", "results", "containers"):
        raise ValueError("Unknown artifact namespace")
    if check_id is not None and check_id not in CHECKS:
        raise ValueError(f"Unknown validation: {check_id}")
    if namespace == "containers" and check_id is not None and check_id not in PHP_CHECKS:
        raise ValueError("Local checks have no container artifacts")
    paths = [Path(run) / namespace]
    if check_id is not None:
        paths.append(paths[0] / check_id)
    for path in paths:
        if path.is_symlink():
            raise ValueError("Artifact directory must belong to this execution")
        if create and not path.is_dir():
            phase = namespace + ("-tool-directory" if path == paths[-1] and check_id else "-directory")
            execution.phase(phase)
            if execution.CURRENT:
                with execution.CURRENT.atomic():
                    path.mkdir(exist_ok=True)
                    execution.phase(phase + "-atomic")
            else:
                path.mkdir(exist_ok=True)
            execution.phase(phase + "-created")
        if path.exists() and not path.is_dir():
            raise ValueError("Artifact directory is not a directory")
    return paths[-1]


def job_path(run, check_id):
    if check_id not in CHECKS:
        raise ValueError(f"Unknown validation: {check_id}")
    return directory(run, "jobs") / f"{check_id}.json"


def allocate(root, clock=utc_now, attempts=100):
    """Exclusively allocate a UTC millisecond name, retaining all old runs."""
    parent = Path(root) / "logs" / "prepush"
    parent.mkdir(parents=True, exist_ok=True)
    for _ in range(attempts):
        now = clock().astimezone(timezone.utc)
        name = now.strftime("%Y%m%d-%H%M%S-") + f"{now.microsecond // 1000:03d}"
        run = parent / name
        try:
            if execution.CURRENT:
                with execution.CURRENT.atomic():
                    run.mkdir()
                    execution.CURRENT.attach(run.resolve())
            else:
                run.mkdir()
        except FileExistsError:
            time.sleep(0.001)
            continue
        execution.phase("allocation-created")
        directory(run, "jobs", create=True)
        return run.resolve()
    raise RuntimeError("Could not allocate an unused UTC report directory")


def context(root, env, check_id):
    if check_id not in CHECKS:
        raise ValueError(f"Unknown validation: {check_id}")
    value = env.get("QA_HOOKS_RUN_DIR", "")
    run = Path(value)
    execution = env.get("QA_HOOKS_EXECUTION_ID", "")
    parent = (Path(root) / "logs" / "prepush").resolve()
    if (not value or not run.is_absolute() or not RUN_NAME.fullmatch(execution)
            or run.name != execution or run.resolve().parent != parent
            or run.is_symlink() or not run.is_dir()
            or not (run / "jobs").is_dir() or (run / "jobs").is_symlink()):
        raise ValueError("qa-checks requires an allocated pre-push run context")
    return run.resolve()


def atomic_json(path, data):
    """Replace from the same directory; no shared temporary filenames."""
    session = execution.CURRENT
    if session and not session.depth:
        with session.atomic():
            return atomic_json(path, data)
    path = Path(path)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".result-", delete=False) as handle:
            name = handle.name
            json.dump(data, handle, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def outcome(run, check_id, status="running", exit_code=None, duration=0.0,
            report_valid=False, error=None):
    return {
        "execution_id": run.name, "validation_id": check_id, "status": status,
        "execution_backend": BACKENDS[check_id],
        "exit_code": exit_code, "duration_seconds": duration,
        "report": CHECKS[check_id][1], "diagnostics": f"results/{check_id}/execution.log",
        "report_valid": report_valid, "error": error,
        "container_id": None, "container_cleanup": "not_created" if check_id in PHP_CHECKS else "not_applicable",
    }


def write_result(run, record):
    atomic_json(job_path(run, record["validation_id"]), record)


def valid_report(path):
    """Require parseable native structured output, never runtime text."""
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing report: {path.name}")
    if path.suffix == ".json":
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, (dict, list)):
            raise ValueError(f"Invalid native JSON report: {path.name}")
    elif path.suffix == ".xml":
        if ET.parse(path).getroot().tag not in ("testsuites", "testsuite"):
            raise ValueError(f"Invalid JUnit report: {path.name}")


def valid_native(path, check_id, code):
    """Require the installed tool's native evidence, including meaningful text."""
    valid_report(path)
    if check_id == "qa-scope":
        expected = {"phpstan.neon", "phpcs.xml", "php-cs-fixer.dist.php"}
        statuses = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line == "Run vendor/bin/php-qa-scope sync to synchronize the blocks.":
                continue
            match = re.fullmatch(r"(OK|OUT-OF-SYNC) (.+)", line)
            if not match or match[2] not in expected or match[2] in statuses:
                raise ValueError("Invalid/duplicate QA Scope target status")
            statuses[match[2]] = match[1]
        if set(statuses) != expected or (code == 0 and any(v != "OK" for v in statuses.values())):
            raise ValueError("Missing/inconsistent QA Scope target statuses")
        return
    if check_id == "test":
        root = ET.parse(path).getroot()
        suites = list(root.iter("testsuite"))
        if not suites or not any(int(s.get("tests", "0")) > 0 for s in suites):
            raise ValueError("JUnit report lacks completed configured tests")
        top = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        if len(list(root.iter("testcase"))) != sum(int(s.get("tests", "0")) for s in top):
            raise ValueError("JUnit test case/count mismatch")
        for suite in suites:
            counts = {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")}
            if (any(v < 0 for v in counts.values()) or
                    sum(counts[k] for k in ("failures", "errors", "skipped")) > counts["tests"] or
                    (code == 0 and (counts["failures"] or counts["errors"]))):
                raise ValueError("Inconsistent JUnit result counts")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Missing native result structure")
    if check_id in ("sniffer", "stan"):
        counts = ("errors", "warnings", "fixable") if check_id == "sniffer" else ("errors", "file_errors")
        totals = data.get("totals")
        if (not isinstance(totals, dict) or not isinstance(data.get("files"), dict) or
                any(type(totals.get(k)) is not int or totals[k] < 0 for k in counts)):
            raise ValueError("Missing native totals/files")
        if check_id == "stan" and not isinstance(data.get("errors"), list):
            raise ValueError("Missing PHPStan error list")
        if code == 0 and (any(totals[k] for k in counts) or (check_id == "stan" and data["errors"])):
            raise ValueError("Native zero contradicts report findings")
    elif check_id in ("fixer", "md"):
        if not isinstance(data.get("files"), list):
            raise ValueError("Missing native file results")
        if check_id == "md" and data.get("package") != "phpmd":
            raise ValueError("Invalid PHPMD report identity")
        if code == 0 and data["files"]:
            raise ValueError("Native zero contradicts changed/violating files")


def initial_summary(run, started, mode="git"):
    data = {
        "schema_version": 4, "execution_id": run.name, "hook": "pre-push",
        "invocation_mode": mode,
        "started_at": started, "ended_at": None, "status": "incomplete",
        "exit_code": None, "lefthook_exit_code": None, "errors": [],
        "validations": [outcome(run, key, "not_run") for key in CHECKS],
    }
    atomic_json(run / "summary.json", data)
    return data


def valid_openspec(path, root, code):
    """Validate the native bulk contract, including its selected project root."""
    valid_report(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "1.0":
        raise ValueError("Invalid OpenSpec bulk report version")
    selected = data.get("root")
    if (not isinstance(selected, dict) or not isinstance(selected.get("path"), str)
            or Path(selected["path"]).resolve() != Path(root).resolve()):
        raise ValueError("Foreign OpenSpec report root")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("Missing OpenSpec bulk items")
    identities = set()
    for item in items:
        if (not isinstance(item, dict) or item.get("type") not in ("change", "spec")
                or not isinstance(item.get("id"), str) or not item["id"]
                or type(item.get("valid")) is not bool or not isinstance(item.get("issues"), list)):
            raise ValueError("Malformed OpenSpec bulk item")
        identity = (item["type"], item["id"])
        if identity in identities:
            raise ValueError("Duplicate OpenSpec bulk item")
        identities.add(identity)
    summary = data.get("summary")
    totals = summary.get("totals") if isinstance(summary, dict) else None
    passed = sum(item["valid"] for item in items)
    expected = {"items": len(items), "passed": passed, "failed": len(items) - passed}
    if (not isinstance(totals, dict) or any(type(totals.get(k)) is not int
            or totals[k] != v for k, v in expected.items())):
        raise ValueError("Inconsistent OpenSpec bulk totals")
    if code == 0 and expected["failed"]:
        raise ValueError("Successful OpenSpec command reported invalid items")


def collect(run, check_id):
    try:
        result_path = job_path(run, check_id)
        if result_path.is_symlink():
            raise ValueError("Result record must belong to this execution")
        with result_path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        expected = outcome(run, check_id)
        if not isinstance(record, dict) or any(record.get(k) != expected[k] for k in
                ("execution_id", "validation_id", "execution_backend", "report", "diagnostics")):
            raise ValueError("Mismatched result identity or artifact paths")
        if record.get("status") not in ("passed", "failed", "interrupted", "not_run"):
            raise ValueError("Incomplete result record")
        code = record.get("exit_code")
        duration = record.get("duration_seconds")
        if (code is not None and type(code) is not int) or type(duration) not in (int, float):
            raise ValueError("Malformed result code or duration")
        if duration < 0 or not math.isfinite(duration):
            raise ValueError("Invalid result duration")
        if type(record.get("report_valid")) is not bool:
            raise ValueError("Missing report validity")
        directory(run, "results", check_id)
        diagnostics = run / record["diagnostics"]
        if not diagnostics.is_file() or diagnostics.is_symlink():
            raise ValueError("Missing diagnostics")
        if record["report_valid"]:
            valid_report(run / record["report"])
            if check_id == "openspec":
                valid_openspec(run / record["report"], run.parents[2], code)
            else:
                valid_native(run / record["report"], check_id, code)
        if record["status"] == "passed" and (code != 0 or not record["report_valid"]):
            raise ValueError("Passed record lacks successful command and report")
        if check_id == "openspec":
            if "container_id" not in record or record["container_id"] is not None or record.get("container_cleanup") != "not_applicable":
                raise ValueError("Local check contains container evidence")
        elif record.get("container_cleanup") not in ("not_created", "removed", "unconfirmed", "pending"):
            raise ValueError("Missing container cleanup outcome")
        if check_id in PHP_CHECKS and record["status"] == "passed" and record["container_cleanup"] != "removed":
            raise ValueError("Passed record lacks confirmed container removal")
        if check_id in PHP_CHECKS and record["status"] == "passed":
            from . import containers
            containers.completion_proof(run, check_id, record)
        return record
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        return outcome(run, check_id, "failed", error=f"Result execution failure: {exc}")


def finalize(run, initial, scheduler_code, errors=(), interrupted=False):
    execution.phase("final-consolidation")
    checks = [collect(run, key) for key in CHECKS]
    if interrupted:
        for check in checks:
            if check["status"] == "failed" and check["error"] and check["error"].startswith("Result execution failure:"):
                path = job_path(run, check["validation_id"])
                check.update(status="interrupted" if path.exists() else "not_run",
                             exit_code=None, error="Interrupted before validation completed")
    if scheduler_code is None and not interrupted:
        for check in checks:
            if not job_path(run, check["validation_id"]).exists():
                check.update(status="not_run", error="Validation not run: scheduler did not complete")
    errors = list(errors)
    if scheduler_code is None:
        errors.append("Lefthook did not complete")
    elif scheduler_code != 0:
        errors.append(f"Lefthook exited with code {scheduler_code}")
    passed = not errors and not interrupted and all(c["status"] == "passed" for c in checks)
    data = dict(initial, ended_at=utc_now().isoformat(),
                status="interrupted" if interrupted else ("passed" if passed else "failed"),
                exit_code=0 if passed else 1, lefthook_exit_code=scheduler_code,
                errors=errors, validations=checks,
                container_cleanup="unconfirmed" if any(c.get("container_cleanup") in ("pending", "unconfirmed") for c in checks if c["validation_id"] in PHP_CHECKS)
                    or any("cleanup unconfirmed" in e for e in errors) else "removed")
    execution.phase("final-publication")
    atomic_json(run / "summary.json", data)
    return data


def terminal(run, summary):
    failed = [CHECKS[c["validation_id"]][0] for c in summary["validations"]
              if c["status"] != "passed"]
    if failed:
        print("The following validations failed: " + ", ".join(failed) + ".")
    elif summary["status"] == "passed":
        print("All seven pre-push validations passed.")
    for error in summary["errors"]:
        print(f"Execution failure: {error}")
    for check in summary["validations"]:
        if check.get("error"):
            print(f"{CHECKS[check['validation_id']][0]}: {check['error']}")
    print(f"Check reports in {run}.")
