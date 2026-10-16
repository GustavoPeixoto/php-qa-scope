"""Read-only Git policy and contributor-runtime checks."""
import os
from pathlib import Path
import re
import shutil

from . import containers, execution


class Rejected(RuntimeError):
    """An actionable pre-flight rejection."""


def git(root, *args, optional=False):
    execution.phase("git-probe")
    result = execution.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode and not optional:
        raise Rejected(result.stderr.decode(errors="replace").strip() or "Git query failed")
    return result


def root_directory():
    return Path(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.decode().strip())


def environment(env=None):
    env = os.environ if env is None else env
    container = Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()
    if env.get("QA_HOOKS_SERVICE") != "dev" or not container:
        raise Rejected("Pre-push validation must run inside the Compose dev service (QA_HOOKS_SERVICE=dev).")


def updates(root, stream):
    fmt = git(root, "rev-parse", "--show-object-format").stdout.decode().strip()
    length = {"sha1": 40, "sha256": 64}.get(fmt)
    if not length:
        raise Rejected(f"Unsupported Git object format: {fmt}")
    oid_pattern = re.compile(rf"[0-9a-fA-F]{{{length}}}\Z")
    zero = "0" * length
    records = []
    for number, line in enumerate(execution.read(stream).splitlines(), 1):
        fields = line.split()
        if len(fields) != 4:
            raise Rejected(f"Malformed pre-push record at line {number}: expected four fields")
        source, local, destination, remote = fields
        if not oid_pattern.fullmatch(local) or not oid_pattern.fullmatch(remote):
            raise Rejected(f"Malformed object ID at pre-push line {number}")
        if (not destination.startswith("refs/") or
                git(root, "check-ref-format", destination, optional=True).returncode):
            raise Rejected(f"Malformed destination reference at line {number}")
        if (source == "(delete)") != (local.lower() == zero):
            raise Rejected(f"Malformed deletion at line {number}")
        records.append((source, local.lower(), destination, remote.lower()))
    if len(records) > 1:
        raise Rejected("Push one effective reference update at a time, including deletions.")
    if not records or records[0][0] == "(delete)":
        return None
    return records[0]


def checkout(root, record):
    source, local, destination, _ = record
    resolved = git(root, "rev-parse", "--symbolic-full-name", "--verify", source,
                   optional=True)
    source_ref = resolved.stdout.decode().strip()
    if resolved.returncode or not source_ref.startswith(("refs/heads/", "refs/tags/")):
        raise Rejected("Unsupported push source; use the checked-out branch or an explicit tag.")
    source_oid = git(root, "rev-parse", "--verify", source_ref).stdout.decode().strip()
    if local != source_oid:
        raise Rejected("Supplied local object ID differs from the source reference.")
    head = git(root, "rev-parse", "--verify", "HEAD").stdout.decode().strip()
    branch = git(root, "symbolic-ref", "-q", "HEAD", optional=True).stdout.decode().strip()
    if source_ref.startswith("refs/heads/"):
        if not destination.startswith("refs/heads/"):
            raise Rejected("A branch update requires a refs/heads destination.")
        if source_ref != branch or local != head:
            raise Rejected("Push the currently checked-out source branch at HEAD.")
    else:
        if not destination.startswith("refs/tags/"):
            raise Rejected("A tag update requires a refs/tags destination.")
        peeled = git(root, "rev-parse", "--verify", local + "^{commit}", optional=True)
        if peeled.returncode:
            raise Rejected("The transmitted tag must resolve to a commit.")
        if branch or peeled.stdout.decode().strip() != head:
            raise Rejected("Explicitly check out the intended tag with detached HEAD before pushing it.")
    clean(root)


def clean(root):
    # Require an existing HEAD and keep manual/reference policies separate.
    git(root, "rev-parse", "--verify", "HEAD")
    # NUL-delimited filenames are never split on whitespace or rendered unsafely.
    staged = git(root, "diff", "--cached", "--ita-visible-in-index", "--ignore-submodules=none",
                 "--name-only", "-z", "HEAD", "--").stdout
    tracked = git(root, "diff", "--ignore-submodules=none", "--name-only", "-z", "--").stdout
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout
    if staged or tracked or untracked:
        raise Rejected("Pre-push validation requires a clean index/worktree and no untracked files. "
                       "Stash or explicitly resolve local changes before a newly authorized push.")


def runtime(root):
    execution.phase("openspec-probe")
    try:
        probe = execution.run(["openspec", "--version"], cwd=root, capture_output=True)
    except OSError as exc:
        raise Rejected(f"QA needs OpenSpec 1.14.0 in dev: {exc}") from exc
    if probe.returncode or probe.stdout.decode().strip() != "1.14.0":
        raise Rejected("QA needs OpenSpec 1.14.0 in dev; rebuild the dev environment.")
    for executable in ("docker", "lefthook"):
        if not shutil.which(executable):
            raise Rejected(f"Missing {executable}; rebuild dev or restore its tooling.")
    files = ("docker-compose.yml", "composer.json", "php-qa-scope.yml", "phpcs.xml",
             "php-cs-fixer.dist.php", "phpmd.xml", "phpstan.neon", "phpunit.xml.dist", "lefthook.yml")
    for filename in files:
        if not (root / filename).is_file():
            raise Rejected(f"Missing required configuration: {filename}")
    commands = [
        ["docker", "compose", "version"],
        ["docker", "compose", "ps", "--services", "--status", "running"],
        ["docker", "compose", "exec", "-T", "php", "composer", "--no-ansi", "--version"],
        ["docker", "compose", "exec", "-T", "php", "sh", "-c",
         "test -r vendor/autoload.php && " + " && ".join(
             f"test -x vendor/bin/{name}" for name in
             ("phpcs", "php-cs-fixer", "phpmd", "phpstan", "phpunit"))],
    ]
    for index, command in enumerate(commands):
        execution.phase(("compose-version", "running-service", "composer-probe", "dependencies")[index])
        try:
            result = execution.run(command, cwd=root, capture_output=True)
        except OSError as exc:
            raise Rejected(f"Runtime pre-flight failed: {exc}") from exc
        if result.returncode or (index == 1 and b"php" not in result.stdout.splitlines()):
            detail = result.stderr.decode(errors="replace").strip()
            raise Rejected("QA needs Docker Compose access, a running php service, Composer, "
                           f"and installed dev dependencies. {detail}")
    execution.phase("runtime-template")
    try:
        containers.capabilities(root)
        return containers.template(root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Rejected(f"QA needs a reusable active PHP runtime and Docker container lifecycle: {exc}") from exc
