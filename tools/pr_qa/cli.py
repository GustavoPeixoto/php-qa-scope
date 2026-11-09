"""Independent CI execution using the shared native QA validation contract."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

from git_hooks import qa, reports


STDOUT_REPORTS = {"qa-scope", "fixer", "stan", "openspec"}


class Cancelled(Exception):
    """A catchable runner interruption; never a successful native result."""


@contextmanager
def interruption():
    previous = {}

    def cancel(number, frame):
        raise Cancelled(f"Interrupted by signal {number}")

    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            previous[number] = signal.signal(number, cancel)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def process(argv, **kwargs):
    """Keep Docker clients out of terminal signal groups and reap on interruption."""
    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, start_new_session=True, **kwargs)
    try:
        return child.wait()
    except BaseException:
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        raise


def safe_path(base, relative):
    """Only fixed relative paths under an evidence tree, without symlinks."""
    base = Path(base)
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid evidence path")
    current = base
    for part in ("", *relative.parts):
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink in evidence path")
    return current


def validate_report(path, check_id, root, code):
    if check_id == "openspec":
        reports.valid_openspec(path, root, code)
    else:
        reports.valid_native(path, check_id, code)


def validate_revision(root, revision):
    if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", revision):
        raise ValueError("Revision must be a full commit SHA")
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                            capture_output=True, text=True).stdout.strip()
    if actual != revision:
        raise ValueError("Revision does not match checked-out HEAD")


def check(root, check_id, image, revision):
    if check_id not in reports.CHECKS:
        raise ValueError(f"Unknown check: {check_id}")
    run = safe_path(root, "logs/pr-qa")
    directory = safe_path(run, f"results/{check_id}")
    directory.mkdir(parents=True, exist_ok=True)
    outcome_path = safe_path(run, f"outcomes/{check_id}.json")
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    outcome = dict(kind="pr-qa", schema_version=1, check_id=check_id, revision=revision,
                   native_exit_code=None, report_valid=False, status="failed", error=None)
    report = safe_path(run, reports.CHECKS[check_id][1])
    # Never accept a report or outcome from an earlier invocation.
    report.unlink(missing_ok=True)
    outcome_path.unlink(missing_ok=True)
    name = f"pr-qa-{check_id}-{uuid.uuid4().hex}"
    created = False
    try:
        with interruption(), (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr, (directory / "preparation.stdout.log").open("wb") as preparation, (directory / "preparation.stderr.log").open("wb") as diagnostics:
            validate_revision(root, revision)
            if not image or image.startswith("-") or any(c.isspace() for c in image):
                raise ValueError("Invalid image reference")
            created = True  # The reserved name also covers interrupted creation.
            native = qa.command(check_id, run)
            code = process(["docker", "create", "--init", "--name", name,
                            "--user", f"{os.getuid()}:{os.getgid()}",
                            "--tmpfs", "/tmp:rw,mode=1777", "--env", "HOME=/tmp",
                            "--env", "COMPOSER_HOME=/tmp/composer",
                            "--mount", f"type=bind,source={root},target={root}",
                            "--workdir", str(root), "--entrypoint", native[0], "--", image, *native[1:]],
                           cwd=root, stdout=preparation, stderr=diagnostics)
            if code:
                raise ValueError(f"Container creation failed ({code})")
            attached = process(["docker", "start", "--attach", name], cwd=root,
                               stdout=stdout, stderr=stderr)
            state = subprocess.run(["docker", "inspect", "--format", "{{json .State}}", name],
                                   capture_output=True, text=True, check=True)
            state = json.loads(state.stdout)
            if (state.get("Status") != "exited" or state.get("Error") or
                    not state.get("StartedAt") or state["StartedAt"].startswith("0001-") or
                    type(state.get("ExitCode")) is not int):
                raise ValueError("Native completion is unknown")
            stderr.flush()
            if state["ExitCode"] in (126, 127) and re.search(
                    rb"^\[FATAL tini \(\d+\)\] exec .+ failed:",
                    (directory / "stderr.log").read_bytes(), re.MULTILINE):
                raise ValueError("Native command could not start")
            code = outcome["native_exit_code"] = state["ExitCode"]
            stdout.flush()
            if check_id in STDOUT_REPORTS:
                captured = directory / "stdout.log"
                validate_report(captured, check_id, root, code)
                shutil.copyfile(captured, report)
            validate_report(report, check_id, root, code)
            outcome["report_valid"] = True
            if attached != code or state.get("OOMKilled"):
                raise ValueError("Container attachment/completion failed")
            outcome["status"] = "passed" if code == 0 else "failed"
    except Cancelled as exc:
        outcome.update(status="cancelled", error=str(exc))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError, ET.ParseError) as exc:
        outcome["error"] = str(exc)
    finally:
        if created:
            try:
                cleanup = subprocess.run(["docker", "rm", "--force", name], stdin=subprocess.DEVNULL,
                                         capture_output=True, timeout=20)
                (directory / "cleanup.stdout.log").write_bytes(cleanup.stdout)
                (directory / "cleanup.stderr.log").write_bytes(cleanup.stderr)
                if cleanup.returncode:
                    outcome.update(status="failed", error="Container cleanup failed")
            except (OSError, subprocess.SubprocessError) as exc:
                outcome.update(status="failed", error=f"Container cleanup failed: {exc}")
        outcome_path.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(f"{check_id}: {outcome['status']} (native exit: {outcome['native_exit_code']})")
    if outcome["error"]:
        print(outcome["error"], file=sys.stderr)
    return 0 if outcome["status"] == "passed" else 1
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, choices=reports.CHECKS)
    parser.add_argument("--image", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    root = Path.cwd().resolve()
    try:
        return check(root, args.check, args.image, args.revision)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"QA execution failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
