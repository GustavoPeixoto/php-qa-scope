"""Synthetic project construction and contributor-source isolation checks."""
from contextlib import contextmanager, ExitStack
import builtins
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from openspec_test_fixture import create_project


@contextmanager
def forbid_source_openspec(source):
    """Reject source-tree reads, traversal, and metadata probes during setup."""
    forbidden = os.path.abspath(source / "openspec")

    def guarded(original):
        def call(path, *args, **kwargs):
            if isinstance(path, (str, bytes, os.PathLike)):
                target = os.fsdecode(path)
                if kwargs.get("dir_fd") is not None and not os.path.isabs(target):
                    target = os.path.join(os.readlink(f"/proc/self/fd/{kwargs['dir_fd']}"), target)
                absolute = os.path.abspath(target)
                if absolute == forbidden or absolute.startswith(forbidden + os.sep):
                    raise AssertionError(f"Contributor OpenSpec access: {absolute}")
            return original(path, *args, **kwargs)
        return call

    with ExitStack() as stack:
        for module, name in ((builtins, "open"), (io, "open"), (os, "open"),
                             (os, "scandir"), (os, "stat"), (os, "lstat"), (os, "readlink")):
            stack.enter_context(patch.object(module, name, guarded(getattr(module, name))))
        yield


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class OpenSpecFixtureTests(unittest.TestCase):
    def test_deterministic_scenarios_without_contributor_reads(self):
        source = Path(__file__).resolve().parents[2]
        for scenario in ("base", "pending", "invalid", "archived"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                roots = [Path(directory) / name for name in ("first", "second")]
                for root in roots:
                    root.mkdir()
                    with forbid_source_openspec(source):
                        with self.assertRaisesRegex(AssertionError, "Contributor OpenSpec access"):
                            (source / "openspec/config.yaml").read_text()
                        create_project(root, scenario)
                self.assertEqual(snapshot(roots[0]), snapshot(roots[1]))
                files = snapshot(roots[0])
                self.assertEqual(files["openspec/config.yaml"], b"schema: spec-driven\n")
                self.assertTrue(all(b"store:" not in data and b"context:" not in data
                                    and b"rules:" not in data for data in files.values()))
                self.assertIn("openspec/specs/fixture-spec/spec.md", files)
                tasks = [data for path, data in files.items() if path.endswith("tasks.md")]
                self.assertEqual(len(tasks), int(scenario != "base"))
                self.assertTrue(all(b"- [ ]" in data for data in tasks))

    def test_existing_tree_is_rejected_without_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_project(root, "pending")
            before = snapshot(root)
            with self.assertRaises(FileExistsError):
                create_project(root, "invalid")
            self.assertEqual(snapshot(root), before)

    def test_unknown_scenario_leaves_no_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create_project(Path(directory), "unknown")
            self.assertFalse((Path(directory) / "openspec").exists())

    def test_assembled_without_contributor_openspec_access(self):
        from test_hooks_integration import assembled, LEFTHOOK, PROJECT
        if not LEFTHOOK:
            self.skipTest("Install pinned Lefthook or set QA_HOOKS_TEST_LEFTHOOK")
        with forbid_source_openspec(PROJECT), assembled() as (root, git, env):
            self.assertEqual((root / "openspec/config.yaml").read_text(), "schema: spec-driven\n")
            self.assertFalse((root / "openspec/changes").exists())
            self.assertEqual(subprocess.check_output(["openspec", "--version"], env=env).strip(), b"1.14.0")
            self.assertEqual(git("status", "--porcelain"), "")

    def test_native_source_preparation_without_contributor_openspec_access(self):
        from test_hooks_integration import prepare_native_sources, PROJECT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with forbid_source_openspec(PROJECT):
                prepare_native_sources(root)
            with tempfile.TemporaryDirectory() as expected:
                create_project(Path(expected), "pending")
                self.assertEqual(snapshot(root / "openspec"), snapshot(Path(expected) / "openspec"))
            self.assertTrue((root / "composer.json").is_file())
            self.assertTrue((root / "tools/git-hooks").is_file())
            self.assertTrue((root / "docker/dev/.env").is_file())
            self.assertFalse((root / ".git").exists())
