"""Policy tests exercise real temporary Git state, never contributor state."""
from contextlib import contextmanager
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from git_hooks import preflight


@contextmanager
def repository(object_format="sha1"):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
        git("init", "-b", "main", f"--object-format={object_format}")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "Hook fixture")
        (root / "tracked").write_text("original\n")
        (root / ".gitignore").write_text("logs/\nignored/\n")
        git("add", ".")
        git("commit", "-m", "fixture")
        yield root, git


class PreflightTests(unittest.TestCase):
    def test_openspec_preflight_pin_and_missing_cli(self):
        with repository() as (root, git):
            for result in (subprocess.CompletedProcess([], 0, b"2.0.0\n", b""),
                           subprocess.CompletedProcess([], 1, b"1.14.0\n", b"")):
                with patch("git_hooks.preflight.execution.run", return_value=result) as probe:
                    with self.assertRaisesRegex(preflight.Rejected, "OpenSpec 1.14.0"):
                        preflight.runtime(root)
                    self.assertEqual(probe.call_args.args[0], ["openspec", "--version"])
            with patch("git_hooks.preflight.execution.run", side_effect=FileNotFoundError("openspec")):
                with self.assertRaisesRegex(preflight.Rejected, "OpenSpec 1.14.0"):
                    preflight.runtime(root)

    def test_environment_rejects_all_paths_outside_dev(self):
        for env in ({}, {"QA_HOOKS_SERVICE": "php"}):
            with self.assertRaisesRegex(preflight.Rejected, "Compose dev"):
                preflight.environment(env)
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(preflight.Rejected):
                preflight.environment({"QA_HOOKS_SERVICE": "dev"})

    def test_records_and_object_formats(self):
        for fmt, size in (("sha1", 40), ("sha256", 64)):
            with repository(fmt) as (root, git):
                oid = git("rev-parse", "HEAD")
                zero = "0" * size
                self.assertIsNone(preflight.updates(root, io.StringIO("")))
                self.assertIsNone(preflight.updates(root, io.StringIO(f"(delete) {zero} refs/heads/old {oid}\n")))
                row = f"refs/heads/main {oid} refs/heads/review {zero}\n"
                self.assertEqual(preflight.updates(root, io.StringIO(row))[1], oid)
                for bad in (row + row, "\n", "broken\n", row.replace(oid, "x" * size),
                            f"(delete) {oid} refs/heads/old {oid}\n",
                            f"HEAD {zero} refs/heads/new {zero}\n",
                            row.replace("refs/heads/review", "refs/heads/bad..name")):
                    with self.assertRaises(preflight.Rejected):
                        preflight.updates(root, io.StringIO(bad))

    def test_branch_identity_and_supported_namespaces(self):
        with repository() as (root, git):
            oid = git("rev-parse", "HEAD")
            before = git("status", "--porcelain=v1"), git("stash", "list"), git("write-tree")
            for source in ("refs/heads/main", "HEAD", "main"):
                preflight.checkout(root, (source, oid, "refs/heads/review", "0" * 40))
            git("branch", "other")
            for source, local, target in (("refs/heads/other", oid, "refs/heads/main"),
                                           (oid, oid, "refs/heads/main"),
                                           ("HEAD", "1" * 40, "refs/heads/main"),
                                           ("HEAD", oid, "refs/tags/main")):
                with self.assertRaises(preflight.Rejected):
                    preflight.checkout(root, (source, local, target, "0" * 40))
            self.assertEqual(before, (git("status", "--porcelain=v1"), git("stash", "list"), git("write-tree")))

    def test_detached_lightweight_annotated_and_noncommit_tags(self):
        with repository() as (root, git):
            git("tag", "light")
            git("tag", "-a", "annotated", "-m", "tag")
            commit = git("rev-parse", "HEAD")
            for name in ("light", "annotated"):
                oid = git("rev-parse", name)
                row = (f"refs/tags/{name}", oid, f"refs/tags/{name}", "0" * 40)
                with self.assertRaisesRegex(preflight.Rejected, "detached"):
                    preflight.checkout(root, row)
                git("checkout", "--detach", name)
                preflight.checkout(root, row)
                git("checkout", "main")
            blob = git("rev-parse", "HEAD:tracked")
            git("tag", "blob", blob)
            git("checkout", "--detach", "light")
            with self.assertRaisesRegex(preflight.Rejected, "commit"):
                preflight.checkout(root, ("refs/tags/blob", blob, "refs/tags/blob", "0" * 40))
            with self.assertRaises(preflight.Rejected):
                preflight.checkout(root, ("refs/tags/light", commit, "refs/heads/tag", "0" * 40))
            git("checkout", "main")
            (root / "tracked").write_text("next\n")
            git("commit", "-am", "next")
            git("checkout", "--detach", "HEAD")
            with self.assertRaisesRegex(preflight.Rejected, "detached"):
                preflight.checkout(root, ("refs/tags/light", commit, "refs/tags/light", "0" * 40))

    def test_cleanliness_is_nul_safe_and_ignores_output(self):
        for state in ("staged", "unstaged", "untracked", "ignored"):
            with repository() as (root, git):
                oid = git("rev-parse", "HEAD")
                if state in ("staged", "unstaged"):
                    (root / "tracked").write_text("dirty\n")
                    if state == "staged":
                        git("add", "tracked")
                else:
                    name = "ignored/report" if state == "ignored" else "odd\nfile name"
                    path = root / name
                    path.parent.mkdir(exist_ok=True)
                    path.write_text("data")
                row = ("HEAD", oid, "refs/heads/main", "0" * 40)
                if state == "ignored":
                    preflight.checkout(root, row)
                else:
                    with self.assertRaisesRegex(preflight.Rejected, "Stash"):
                        preflight.checkout(root, row)

    def test_runtime_prerequisites_fail_clearly(self):
        with repository() as (root, git), patch("git_hooks.preflight.shutil.which", return_value=None):
            with self.assertRaisesRegex(preflight.Rejected, "Missing docker"):
                preflight.runtime(root)
        with repository() as (root, git), patch("git_hooks.preflight.shutil.which", return_value="tool"):
            with self.assertRaisesRegex(preflight.Rejected, "configuration"):
                preflight.runtime(root)
