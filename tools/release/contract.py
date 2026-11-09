"""Pure release eligibility and version rules shared by both entry points."""

import re


COMPONENT = r"(0|[1-9][0-9]*)"
VERSION = re.compile(rf"{COMPONENT}\.{COMPONENT}\.{COMPONENT}")


class ReleaseError(ValueError):
    """A release cannot safely proceed."""


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
