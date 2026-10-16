"""Owned creation/removal, template parity, native outcomes, and Docker failures."""
import copy
import json
import os
import signal
import subprocess
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from git_hooks import containers, execution, qa, reports
from test_hooks_integration import assembled, LEFTHOOK
from test_reports import native_text


@unittest.skipUnless(LEFTHOOK, "Pinned npm Lefthook required")
class ContainerTests(unittest.TestCase):
    def test_client_zero_does_not_finish_or_stop_running_native_work(self):
        with assembled() as (root, git, env), patch.dict(os.environ, env):
            run = reports.allocate(root)
            containers.configure(run, containers.template(root))
            options = dict(env, FIXTURE_ONE_CHECK="1", QA_TEST_HOLD="1",
                QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
            p = subprocess.Popen([root / "tools/git-hooks", "check", "stan"], cwd=root,
                                 env=options, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 10
                while not (run / "stan.started").exists():
                    self.assertIsNone(p.poll())
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                record = containers.load(run, containers.context(run), "stan")
                self.assertEqual(record["start_client_exit_code"], 0)
                self.assertEqual(record["native_completion"], "pending")
                self.assertIsNone(record["exit_code"])
                self.assertIsNone(p.poll())
                self.assertFalse((run / "results/stan/result.json").exists())
                self.assertTrue(json.loads((Path(env["FIXTURE_ENGINE"]) / (record["id"] + ".json")).read_text())["State"]["Running"])
                began = time.monotonic()
                p.send_signal(signal.SIGTERM)
                p.communicate(timeout=10)
                self.assertLess(time.monotonic() - began, 10)
                self.assertNotEqual(p.returncode, 0)
                self.assertIsNone(reports.collect(run, "stan")["exit_code"])
                self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])
            finally:
                if p.poll() is None:
                    p.kill()
                    p.wait()

    def test_log_failure_and_truncation_preserve_native_code_and_remove(self):
        for failure in ("FIXTURE_LOG_FAIL", "FIXTURE_LOG_TRUNCATE"):
            with assembled() as (root, git, env):
                run = reports.allocate(root)
                options = dict(env, FIXTURE_ONE_CHECK="1", QA_HOOKS_RUN_DIR=str(run),
                               QA_HOOKS_EXECUTION_ID=run.name, **{failure: "1"})
                with patch.dict(os.environ, options):
                    containers.configure(run, containers.template(root))
                    self.assertEqual(qa.check(root, "stan", options), 1)
                    result = reports.collect(run, "stan")
                    self.assertEqual(result["exit_code"], 0)
                    self.assertFalse(result["report_valid"])
                    self.assertEqual(result["container_cleanup"], "removed")
                    self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])

    def test_template_context_and_native_argv(self):
        with assembled() as (root, git, env), patch.dict(os.environ, env):
            item = containers.template(root)
            containers.capabilities(root)
            self.assertEqual(item["Config"]["WorkingDir"], str(root))
            run = reports.allocate(root)
            ctx = containers.configure(run, item)
            saved = json.loads((run / "runtime.json").read_text())
            self.assertNotIn("Env", saved)
            item["Config"]["Env"].append("OPAQUE=space 'quote' $(touch SHOULD_NOT_EXIST)")
            args = containers.create_args(item, ctx, "stan", qa.command("stan", run))
            self.assertEqual(args[args.index("--volumes-from") + 1], item["Id"])
            self.assertEqual(args[args.index("--entrypoint") + 1], "composer")
            self.assertIn(item["Config"]["Env"][-1], args)
            self.assertNotIn("--rm", args)
            self.assertIn("--init", args)
            self.assertNotIn("--publish", args)
            self.assertFalse((root / "SHOULD_NOT_EXIST").exists())
            self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])

    def test_invalid_active_runtime_never_creates_work(self):
        with assembled() as (root, git, env), patch.dict(os.environ, env):
            item = containers.template(root)
            for field, replacement in (("State", {"Running": False}), ("Mounts", []),
                                       ("NetworkSettings", {"Networks": {}})):
                broken = copy.deepcopy(item)
                broken[field] = replacement
                with patch.object(containers, "inspect", return_value=[broken]), self.assertRaises(ValueError):
                    containers.template(root, item["Id"])
            for field, value in (("WorkingDir", "/different"), ("Env", None), ("User", None)):
                broken = copy.deepcopy(item)
                broken["Config"][field] = value
                with patch.object(containers, "inspect", return_value=[broken]), self.assertRaises(ValueError):
                    containers.template(root, item["Id"])
            self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])

    def test_native_fast_exit_codes_reports_and_complete_removal(self):
        for fail in ("", "stan"):
            with assembled() as (root, git, env):
                run = reports.allocate(root)
                options = dict(env, FIXTURE_ONE_CHECK="1", QA_TEST_FAIL=fail,
                    QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
                with patch.dict(os.environ, options), execution.Session() as session:
                    containers.configure(run, containers.template(root))
                    session.attach(run, "stan")
                    with (run / "native.stdout").open("wb") as out, (run / "native.stderr").open("wb") as err:
                        code = containers.execute(root, run, "stan", qa.command("stan", run), out, err)
                    self.assertEqual(code, 1 if fail else 0)
                    self.assertTrue(containers.cleanup(root, run, session, "stan"))
                    ctx = containers.context(run)
                    record = containers.load(run, ctx, "stan")
                    self.assertEqual(record["exit_code"], code)
                    self.assertEqual(record["cleanup"], "removed")
                    self.assertEqual(json.loads((run / "native.stdout").read_text())["totals"]["errors"], 0)
                    self.assertIn("Composer fixture diagnostics", (run / "native.stderr").read_text())
                    self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])
                    self.assertTrue(containers.receipt(run, "stan").exists())

    def test_creation_failure_unknown_native_code_and_no_container(self):
        with assembled() as (root, git, env):
            run = reports.allocate(root)
            options = dict(env, FIXTURE_CREATE_FAIL="1",
                QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
            with patch.dict(os.environ, options), execution.Session() as session:
                containers.configure(run, containers.template(root))
                session.attach(run, "stan")
                with (run / "out").open("wb") as out, (run / "err").open("wb") as err:
                    with self.assertRaisesRegex(ValueError, "creation failure"):
                        containers.execute(root, run, "stan", qa.command("stan", run), out, err)
                self.assertTrue(containers.cleanup(root, run, session, "stan"))
                record = containers.load(run, containers.context(run), "stan")
                self.assertIsNone(record["exit_code"])
                self.assertEqual(record["cleanup"], "removed")
                self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])

    def test_foreign_identity_is_never_removed_or_started(self):
        with assembled() as (root, git, env), patch.dict(os.environ, env), execution.Session() as session:
            run = reports.allocate(root)
            item = containers.template(root)
            ctx = containers.configure(run, item)
            (run / "containers").mkdir()
            cid = "d" * 64
            containers.update(run, ctx, "stan", id=cid)
            file = Path(env["FIXTURE_ENGINE"]) / (cid + ".json")
            file.write_text(json.dumps({"Id": cid, "Image": item["Image"], "Name": "/" + containers.name(ctx, "stan"),
                "Config": {"Labels": {containers.OWNER: "foreign", containers.CHECK: "stan", containers.PROJECT: "fixture"}},
                "State": {"Running": False}, "HostConfig": {"AutoRemove": True, "Init": True}}))
            owner = containers.Cleanup(root, run, session, "stan")
            owner.deadline = time.monotonic() + 2
            owner.tick()
            self.assertFalse(owner.finish())
            self.assertTrue(file.exists())
            self.assertTrue(any("Foreign container ownership" in e for e in session.errors), session.errors)

    def test_created_but_never_started_container_is_removed(self):
        with assembled() as (root, git, env):
            run = reports.allocate(root)
            options = dict(env, FIXTURE_START_FAIL="1", QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
            with patch.dict(os.environ, options), execution.Session() as session:
                containers.configure(run, containers.template(root))
                session.attach(run, "stan")
                with (run / "out").open("wb") as out, (run / "err").open("wb") as err:
                    with self.assertRaisesRegex(ValueError, "startup"):
                        containers.execute(root, run, "stan", qa.command("stan", run), out, err)
                self.assertTrue(containers.cleanup(root, run, session, "stan"))
                record = containers.load(run, containers.context(run), "stan")
                self.assertIsNone(record["exit_code"])
                self.assertEqual(record["cleanup"], "removed")
                self.assertEqual(list(Path(env["FIXTURE_ENGINE"]).glob("*.json")), [])

    def test_creation_name_collision_does_not_touch_foreign_work(self):
        with assembled() as (root, git, env):
            run = reports.allocate(root)
            options = dict(env, QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
            with patch.dict(os.environ, options), execution.Session() as session:
                ctx = containers.configure(run, containers.template(root))
                session.attach(run, "stan")
                file = Path(env["FIXTURE_ENGINE"]) / ("e" * 64 + ".json")
                foreign = {"Id": "e" * 64, "Name": "/" + containers.name(ctx, "stan"),
                    "Config": {"Labels": {}}, "State": {"Running": False}}
                file.write_text(json.dumps(foreign))
                with (run / "out").open("wb") as out, (run / "err").open("wb") as err:
                    with self.assertRaisesRegex(ValueError, "already in use"):
                        containers.execute(root, run, "stan", qa.command("stan", run), out, err)
                owner = containers.Cleanup(root, run, session, "stan")
                owner.deadline = time.monotonic() + 2
                owner.tick()
                self.assertFalse(owner.finish())
                self.assertEqual(json.loads(file.read_text()), foreign)
                self.assertEqual(list(root.glob("logs/prepush/*/*.started")), [])

    def test_native_pass_with_unconfirmed_removal_is_unsuccessful(self):
        with assembled() as (root, git, env):
            run = reports.allocate(root)
            options = dict(env, QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
            with patch.dict(os.environ, options):
                containers.configure(run, containers.template(root))
                def native(root, run, key, argv, stdout, stderr):
                    stdout.write(native_text("stan").encode())
                    return 0
                def failed(root, run, session, key):
                    containers.update(run, containers.context(run), key, cleanup="unconfirmed")
                    session.errors.append("Container cleanup unconfirmed: Docker unavailable")
                    return False
                (run / "containers").mkdir()
                containers.update(run, containers.context(run), "stan")
                with patch.object(containers, "execute", side_effect=native), patch.object(containers, "cleanup", side_effect=failed):
                    self.assertEqual(qa.check(root, "stan", options), 1)
                record = reports.collect(run, "stan")
                self.assertEqual(record["exit_code"], 0)
                self.assertTrue(record["report_valid"])
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["container_cleanup"], "unconfirmed")

    def test_missing_identity_with_failed_cleanup_never_claims_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = reports.allocate(root)
            options = {"QA_HOOKS_RUN_DIR": str(run), "QA_HOOKS_EXECUTION_ID": run.name}
            def native(root, run, key, argv, stdout, stderr):
                stdout.write(b"{}")
                return 0
            def failed(root, run, session, key):
                session.errors.append("Container cleanup unconfirmed: missing ownership evidence")
                return False
            with patch.object(containers, "execute", side_effect=native), patch.object(containers, "cleanup", side_effect=failed):
                self.assertEqual(qa.check(root, "stan", options), 1)
            record = reports.collect(run, "stan")
            self.assertEqual(record["exit_code"], 0)
            self.assertEqual(record["container_cleanup"], "unconfirmed")
