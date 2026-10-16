"""Execution isolation, evidence validation, and coordinator summary tests."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import io
import json
import signal
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from git_hooks import containers, execution, reports


def native_text(key):
    return {
        "qa-scope": "OK phpstan.neon\nOK phpcs.xml\nOK php-cs-fixer.dist.php\n",
        "sniffer": '{"totals":{"errors":0,"warnings":0,"fixable":0},"files":{}}',
        "fixer": '{"files":[],"about":"PHP CS Fixer"}',
        "stan": '{"totals":{"errors":0,"file_errors":0},"files":{},"errors":[]}',
        "md": '{"package":"phpmd","files":[]}',
        "test": '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="fixture"/></testsuite></testsuites>',
    }[key]


def native_proof(run, key, code=0):
    if not (run / "runtime.json").exists():
        containers.configure(run, {"Id": "a" * 64, "Image": "sha256:" + "b" * 64,
            "Config": {"Labels": {"com.docker.compose.project": "unit"}}})
    return containers.update(run, containers.context(run), key, id="d" * 64,
        state="removed", cleanup="removed", native_completion="confirmed", exit_code=code,
        log_collection="complete", stdout_bytes=len(native_text(key).encode()) if key in ("qa-scope", "fixer", "stan") else 0, stderr_bytes=0,
        terminal_state={"Status": "exited", "Running": False, "Restarting": False,
            "StartedAt": "2026-10-15T00:00:00Z", "FinishedAt": "2026-10-15T00:00:01Z",
            "ExitCode": code, "OOMKilled": False, "Error": ""})


def successful(run, key):
    reports.directory(run, "results", key, create=True)
    filename = reports.CHECKS[key][1]
    (run / filename).write_text(json.dumps({"version": "1.0", "root": {"path": str(run.parents[2])},
        "items": [], "summary": {"totals": {"items": 0, "passed": 0, "failed": 0}}}) if key == "openspec" else native_text(key))
    (run / f"results/{key}/execution.log").write_text("")
    if key in ("sniffer", "md", "test"):
        (run / f"results/{key}/stdout.log").write_text("")
    record = reports.outcome(run, key, "passed", 0, 0.25, True)
    record["container_cleanup"] = "removed" if key in reports.PHP_CHECKS else "not_applicable"
    if key in reports.PHP_CHECKS:
        record["container_id"] = native_proof(run, key)["id"]
    reports.write_result(run, record)
    return record


class ReportTests(unittest.TestCase):
    def test_historic_schema4_false_positive_is_not_migrated_or_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            old = reports.allocate(directory)
            reports.directory(old, "results", "qa-scope", create=True)
            (old / "results/qa-scope/result.log").write_text("")
            (old / "results/qa-scope/execution.log").write_text("")
            record = reports.outcome(old, "qa-scope", "passed", 0, 1, True)
            record.update(container_id="e" * 64, container_cleanup="removed")
            reports.write_result(old, record)
            summary = reports.initial_summary(old, "historic")
            summary.update(status="passed", exit_code=0)
            summary["validations"][0] = record
            reports.atomic_json(old / "summary.json", summary)
            snapshot = {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}
            new = reports.allocate(directory)
            initial = reports.initial_summary(new, "new")
            for key in reports.CHECKS:
                successful(new, key)
            self.assertEqual(reports.finalize(new, initial, 0)["status"], "passed")
            self.assertEqual(snapshot, {p.relative_to(old): p.read_bytes()
                                       for p in old.rglob("*") if p.is_file()})
            self.assertEqual((old / "results/qa-scope/result.log").stat().st_size, 0)

    def test_native_proof_cannot_be_missing_foreign_or_contradictory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            for changes in ({"id": "e" * 64}, {"native_completion": "pending"},
                            {"log_collection": "failed"}, {"exit_code": 7},
                            {"terminal_state": {}}, {"stdout_bytes": -1}, {"stdout_bytes": 1},
                            {"execution_id": "foreign"}):
                successful(run, "stan")
                path = run / "containers/stan/metadata.json"
                data = json.loads(path.read_text())
                data.update(changes)
                reports.atomic_json(path, data)
                self.assertEqual(reports.collect(run, "stan")["status"], "failed")
                path.unlink()
            successful(run, "stan")
            (run / "containers/stan/metadata.json").unlink()
            self.assertEqual(reports.collect(run, "stan")["status"], "failed")

    def test_empty_incomplete_and_arbitrary_native_evidence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            for key in reports.PHP_CHECKS:
                successful(run, key)
                path = run / reports.CHECKS[key][1]
                for content in (("", "  ", "OK phpcs.xml\n") if key == "qa-scope" else
                                ("<testsuites/>",) if key == "test" else ("{}", "[]")):
                    path.write_text(content)
                    self.assertEqual(reports.collect(run, key)["status"], "failed")

    def test_mixed_backend_identity_and_bulk_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            initial = reports.initial_summary(run, "start")
            self.assertEqual(initial["schema_version"], 4)
            self.assertEqual(list(reports.CHECKS)[-1], "openspec")
            for changes in ({"execution_backend": "php-container"},
                            {"execution_backend": None}, {"container_cleanup": "removed"},
                            {"container_id": "fake"}, {"execution_id": "foreign"}):
                record = successful(run, "openspec")
                record.update(changes)
                reports.write_result(run, record)
                self.assertEqual(reports.collect(run, "openspec")["status"], "failed")
            record = successful(run, "stan")
            record["container_cleanup"] = "not_applicable"
            reports.write_result(run, record)
            self.assertEqual(reports.collect(run, "stan")["status"], "failed")
            for changes in ({"version": "4"}, {"items": [{}]},
                            {"root": {"path": "/foreign"}}, {"summary": {"totals": {}}}):
                record = successful(run, "openspec")
                path = run / record["report"]
                data = json.loads(path.read_text())
                data.update(changes)
                path.write_text(json.dumps(data))
                self.assertEqual(reports.collect(run, "openspec")["status"], "failed")
            with self.assertRaises(ValueError):
                reports.directory(run, "containers", "openspec", create=True)

    def test_utc_names_collisions_overlap_and_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            fixed = datetime(2026, 10, 7, 1, 2, 3, 123456, timezone.utc)
            old = reports.allocate(directory, lambda: fixed)
            (old / "jobs").rmdir()
            (old / "results").mkdir()
            (old / "results" / "stan.json").write_text('{"old": true}')
            (old / "stan.json").write_text('{"native": "old"}')
            (old / "stan.diagnostics.log").write_text("old diagnostics")
            (old / "summary.json").write_text('{"schema_version": 3, "status": "passed"}')
            snapshot = {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}
            (old / "keep").write_text("old")
            with self.assertRaisesRegex(RuntimeError, "unused"):
                reports.allocate(directory, lambda: fixed, attempts=2)
            with ThreadPoolExecutor(max_workers=2) as executor:
                runs = list(executor.map(reports.allocate, [directory, directory]))
            self.assertNotEqual(runs[0], runs[1])
            self.assertEqual(old.name, "20261007-010203-123")
            self.assertTrue(all(reports.RUN_NAME.fullmatch(r.name) for r in runs))
            self.assertEqual((old / "keep").read_text(), "old")
            self.assertEqual(snapshot, {p.relative_to(old): p.read_bytes() for p in old.rglob("*")
                                       if p.is_file() and p.name != "keep"})
            bad = Path(directory) / "file"
            bad.write_text("x")
            with self.assertRaises(OSError):
                reports.allocate(bad)

    def test_context_rejects_foreign_invalid_and_symlink_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            env = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
            self.assertEqual(reports.context(directory, env, "stan"), run)
            for bad in ({}, dict(env, QA_HOOKS_EXECUTION_ID="other"),
                        dict(env, QA_HOOKS_RUN_DIR=str(run.parent))):
                with self.assertRaises(ValueError):
                    reports.context(directory, bad, "stan")
            with self.assertRaises(ValueError):
                reports.context(directory, env, "unknown")
            with tempfile.TemporaryDirectory() as other:
                with self.assertRaises(ValueError):
                    reports.context(other, env, "stan")

    def test_all_six_required_and_scheduler_success(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            initial = reports.initial_summary(run, reports.utc_now().isoformat())
            self.assertEqual(initial["status"], "incomplete")
            absent = reports.finalize(run, initial, 0)
            self.assertEqual(absent["exit_code"], 1)
            self.assertTrue(all(x["status"] == "failed" for x in absent["validations"]))
            for key in reports.CHECKS:
                successful(run, key)
            good = reports.finalize(run, initial, 0)
            self.assertEqual(good["exit_code"], 0)
            self.assertEqual(list(reports.CHECKS), [x["validation_id"] for x in good["validations"]])
            for code in (1, None):
                self.assertEqual(reports.finalize(run, initial, code)["exit_code"], 1)
            self.assertEqual(reports.finalize(run, initial, 0, interrupted=True)["status"], "interrupted")

    def test_grouped_directories_reject_symlinks_and_flat_context(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            env = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
            self.assertTrue((run / "jobs").is_dir())
            for namespace in ("results", "containers"):
                target = reports.directory(run, namespace, "fixer", create=True)
                self.assertEqual(target, run / namespace / "fixer")
                target.rmdir()
                target.symlink_to(run / "jobs", target_is_directory=True)
                with self.assertRaises(ValueError):
                    reports.directory(run, namespace, "fixer", create=True)
                target.unlink()
                target.parent.rmdir()
                target.parent.symlink_to(run / "jobs", target_is_directory=True)
                with self.assertRaises(ValueError):
                    reports.directory(run, namespace, "fixer", create=True)
                target.parent.unlink()
            (run / "jobs").rmdir()
            (run / "results").mkdir()
            with self.assertRaises(ValueError):
                reports.context(directory, env, "fixer")
            for key in ("unknown", "../fixer"):
                with self.assertRaises(ValueError):
                    reports.directory(run, "results", key, create=True)

    def test_interrupted_directory_creation_retains_partial_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            mkdir = Path.mkdir
            with execution.Session() as session:
                session.attach(run)
                initial = reports.initial_summary(run, "start", "manual")
                def interrupted(path, *args, **kwargs):
                    value = mkdir(path, *args, **kwargs)
                    if path == run / "results" / "stan":
                        session.interrupt(signal.SIGTERM, None)
                    return value
                with patch.object(Path, "mkdir", interrupted), self.assertRaises(execution.Interrupted):
                    reports.directory(run, "results", "stan", create=True)
                session.teardown()
                summary = reports.finalize(run, initial, None, interrupted=True)
                self.assertEqual(summary["status"], "interrupted")
                self.assertTrue((run / "results" / "stan").is_dir())
                self.assertTrue((run / "summary.json").is_file())

    def test_malformed_incomplete_foreign_and_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            for changes in ({"execution_id": "other"}, {"validation_id": "test"},
                            {"status": "running"}, {"report": "../foreign.json"},
                            {"exit_code": None}, {"duration_seconds": -1},
                            {"report_valid": False}):
                record = successful(run, "stan")
                record.update(changes)
                reports.atomic_json(run / "jobs/stan.json", record)
                self.assertEqual(reports.collect(run, "stan")["status"], "failed")
            for content in ("{invalid", "[]", "null"):
                (run / "jobs/stan.json").write_text(content)
                self.assertEqual(reports.collect(run, "stan")["status"], "failed")
            successful(run, "stan")
            (run / "results/stan/result.json").write_text("runtime error")
            self.assertEqual(reports.collect(run, "stan")["status"], "failed")
            successful(run, "test")
            (run / "results/test/result.junit.xml").write_text("<wrong/>")
            self.assertEqual(reports.collect(run, "test")["status"], "failed")
            (run / "results/test/result.junit.xml").unlink()
            self.assertEqual(reports.collect(run, "test")["status"], "failed")

    def test_results_independent_and_terminal_concise(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = reports.allocate(directory), reports.allocate(directory)
            for run in (first, second):
                for key in reports.CHECKS:
                    successful(run, key)
            changed = reports.outcome(first, "stan", "failed", 2, 1, True)
            reports.write_result(first, changed)
            self.assertEqual(reports.collect(second, "stan")["status"], "passed")
            initial = reports.initial_summary(first, "start")
            summary = reports.finalize(first, initial, 1)
            with redirect_stdout(io.StringIO()) as output:
                reports.terminal(first, summary)
            self.assertIn("PHPStan", output.getvalue())
            self.assertIn(str(first), output.getvalue())
            self.assertLess(len(output.getvalue().splitlines()), 8)

    def test_native_report_cannot_replace_missing_job_record(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            record = successful(run, "stan")
            (run / "jobs/stan.json").unlink()
            self.assertTrue((run / record["report"]).is_file())
            self.assertEqual(reports.collect(run, "stan")["status"], "failed")
