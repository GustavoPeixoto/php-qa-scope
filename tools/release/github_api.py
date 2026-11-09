"""Read-only GitHub API access shared by release automation."""

import json
import re
import subprocess

if __package__:
    from .contract import ReleaseError
else:
    from contract import ReleaseError


def validate_repository(repository):
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ReleaseError("Invalid repository identity")


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
    validate_repository(repository)
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
