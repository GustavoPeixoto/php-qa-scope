"""Read-only release contract checks; no package imports or dependencies."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


COMPONENT = r"(0|[1-9][0-9]*)"
VERSION = re.compile(rf"{COMPONENT}\.{COMPONENT}\.{COMPONENT}")


class ReleaseError(ValueError):
    """A release cannot safely proceed."""


def api(endpoint):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ReleaseError("GitHub API lookup failed")
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise ReleaseError("Malformed GitHub API JSON") from error


def remote_tags(repository, request=api):
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ReleaseError("Invalid repository identity")
    tags = []
    seen = set()
    for page in range(1, 10001):
        data = request(f"repos/{repository}/tags?per_page=100&page={page}")
        if not isinstance(data, list) or len(data) > 100:
            raise ReleaseError("Malformed tag page")
        names = []
        for tag in data:
            if not isinstance(tag, dict) or not isinstance(tag.get("name"), str) or not tag["name"]:
                raise ReleaseError("Malformed tag entry")
            names.append(tag["name"])
        if any(name in seen for name in names) or len(set(names)) != len(names):
            raise ReleaseError("Repeated/inconsistent tag pagination")
        seen.update(names)
        tags.extend(names)
        if len(data) < 100:
            return tags
    raise ReleaseError("Incomplete tag pagination")


def version_tuple(value):
    if not isinstance(value, str) or VERSION.fullmatch(value) is None:
        return None
    return tuple(int(part) for part in value.split("."))


def validate(branch, manifest, tags, repository, head_repository, base="main"):
    if base != "main" or not isinstance(branch, str):
        raise ReleaseError("Release must target main with a branch name")
    if not branch.startswith("release/"):
        return {"release": False}
    if head_repository != repository:
        raise ReleaseError("Release origin must be the same repository")
    candidate = branch.removeprefix("release/v") if branch.startswith("release/v") else ""
    proposed = version_tuple(candidate)
    if proposed is None:
        raise ReleaseError("Expected canonical release/vX.Y.Z branch")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("version"), str) or manifest["version"] != candidate:
        raise ReleaseError(f"Manifest version must equal {candidate} exactly")
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ReleaseError("Malformed tag list")
    tag = "v" + candidate
    if tag in tags:
        raise ReleaseError(f"Target ref already exists: {tag}")
    stable = [value for name in tags if (value := version_tuple(name.removeprefix("v"))) is not None]
    baseline = max(stable) if stable else None
    if baseline is None:
        allowed = [(0, 1, 0)]
    else:
        major, minor, patch = baseline
        allowed = [(major + 1, 0, 0), (major, minor + 1, 0), (major, minor, patch + 1)]
    display = lambda value: ".".join(map(str, value))
    if proposed not in allowed:
        raise ReleaseError(f"Proposed {candidate}; baseline {display(baseline) if baseline else 'none'}; allowed {', '.join(map(display, allowed))}")
    return {"release": True, "tag": tag, "version": candidate, "baseline": display(baseline) if baseline else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="composer.json")
    parser.add_argument("--tags", help="JSON array of tag names; otherwise enumerate GitHub")
    parser.add_argument("--branch", default=os.environ.get("RELEASE_BRANCH"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--head-repository", default=os.environ.get("HEAD_REPOSITORY"))
    parser.add_argument("--base", default=os.environ.get("BASE_BRANCH", "main"))
    args = parser.parse_args()
    try:
        manifest = json.loads(Path(args.manifest).read_text())
        tags = json.loads(Path(args.tags).read_text()) if args.tags else remote_tags(args.repository)
        print(json.dumps(validate(args.branch, manifest, tags, args.repository, args.head_repository, args.base), sort_keys=True))
        return 0
    except (ReleaseError, OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
