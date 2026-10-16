"""Ordering, launch failure, interruption, and coordinator handoff."""
import io
import json
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack, redirect_stdout

from git_hooks import execution, preflight, reports, runner
from test_reports import successful


class RunnerTests(unittest.TestCase):
    def test_early_paths_have_no_checkout_runtime_or_scheduler(self):
        for record in (None, preflight.Rejected("multiple updates")):
            with patch.object(preflight, "environment"), patch.object(preflight, "root_directory"), \
                    patch.object(preflight, "updates") as updates, patch.object(preflight, "checkout") as checkout, \
                    patch.object(preflight, "runtime") as runtime, patch.object(runner, "dispatch") as dispatch:
                if isinstance(record, Exception):
                    updates.side_effect = record
                    with self.assertRaises(preflight.Rejected):
                        runner.pre_push(io.StringIO())
                else:
                    updates.return_value = record
                    self.assertEqual(runner.pre_push(io.StringIO()), 0)
                checkout.assert_not_called()
                runtime.assert_not_called()
                dispatch.assert_not_called()

    def test_handoff_and_finalization_after_nonzero(self):
        for code in (0, 1):
            with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                for name in ("environment", "checkout", "runtime"):
                    stack.enter_context(patch.object(preflight, name))
                stack.enter_context(patch.object(preflight, "root_directory", return_value=root))
                stack.enter_context(patch.object(preflight, "updates", return_value=("record",)))
                stack.enter_context(patch.object(runner.containers, "cleanup", return_value=True))
                def dispatch(actual_root, run, env):
                    self.assertEqual(actual_root, root)
                    self.assertEqual(env["QA_HOOKS_EXECUTION_ID"], run.name)
                    self.assertEqual(env["QA_HOOKS_RUN_DIR"], str(run))
                    self.assertEqual(json.loads((run / "summary.json").read_text())["status"], "incomplete")
                    for key in reports.CHECKS:
                        successful(run, key)
                    return code, [], False
                stack.enter_context(patch.object(runner, "dispatch", side_effect=dispatch))
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.pre_push(io.StringIO(), {}), code)
                summary = json.loads(next(root.glob("logs/prepush/*/summary.json")).read_text())
                self.assertEqual(summary["lefthook_exit_code"], code)

    def test_scheduler_launch_failure_finalizes(self):
        with tempfile.TemporaryDirectory() as directory:
            run = reports.allocate(directory)
            initial = reports.initial_summary(run, "start")
            with patch.object(subprocess, "Popen", side_effect=FileNotFoundError("lefthook missing")):
                code, errors, interrupted = runner.dispatch(Path(directory), run, {})
            summary = reports.finalize(run, initial, code, errors, interrupted)
            self.assertEqual(summary["exit_code"], 1)
            self.assertIn("Cannot launch", summary["errors"][0])
            self.assertTrue(all(c["status"] == "not_run" for c in summary["validations"]))
            self.assertTrue((run / "runner.log").exists())

    def test_catchable_signal_stops_scheduler_and_marks_interrupted(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            old = signal.getsignal(number)
            with execution.Session() as session:
                with self.assertRaises(execution.Interrupted):
                    session.interrupt(number, None)
                self.assertEqual(session.number, number)
                session.finishing = True
                session.interrupt(number, None)
                self.assertTrue(session.repeated)
            self.assertEqual(signal.getsignal(number), old)
