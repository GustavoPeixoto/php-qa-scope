"""Verify a published tag and create its GitHub Release without retagging."""

import json
import os
import re
import subprocess

def api(endpoint):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise SystemExit(f"GitHub API lookup failed for {endpoint} (exit {result.returncode})")
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise SystemExit(f"Malformed GitHub API JSON for {endpoint}")


def main():
    """Publish or accept the Release using validated publisher environment inputs."""
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    tag = os.environ.get("TAG", "")
    sha = os.environ.get("MERGE_SHA", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SystemExit("Invalid repository identity")
    if not re.fullmatch(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", tag):
        raise SystemExit("Missing or invalid publisher tag output")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SystemExit("Missing or invalid publisher SHA output")

    reference = api(f"repos/{repository}/git/ref/tags/{tag}")
    if (not isinstance(reference, dict) or reference.get("ref") != f"refs/tags/{tag}"
            or not isinstance(reference.get("object"), dict)
            or reference["object"].get("type") != "commit"
            or reference["object"].get("sha") != sha):
        raise SystemExit(f"Remote tag {tag} is not a lightweight reference to expected SHA {sha}")

    seen = set()
    matches = []
    for page in range(1, 10001):
        releases = api(f"repos/{repository}/releases?per_page=100&page={page}")
        if not isinstance(releases, list) or len(releases) > 100:
            raise SystemExit("Malformed GitHub Release page")
        for release in releases:
            if (not isinstance(release, dict) or type(release.get("id")) is not int
                    or release["id"] <= 0 or not isinstance(release.get("tag_name"), str)
                    or type(release.get("draft")) is not bool
                    or type(release.get("prerelease")) is not bool):
                raise SystemExit("Malformed GitHub Release record")
            if release["id"] in seen:
                raise SystemExit("Repeated/inconsistent GitHub Release pagination")
            seen.add(release["id"])
            if release["tag_name"] == tag:
                matches.append(release)
        if len(releases) < 100:
            break
    else:
        raise SystemExit("Incomplete GitHub Release pagination")

    if any(release["draft"] or release["prerelease"] for release in matches):
        raise SystemExit(f"Conflicting draft or prerelease exists for {tag}")
    if matches:
        if (len(matches) != 1 or not isinstance(matches[0].get("published_at"), str)
                or not matches[0]["published_at"]):
            raise SystemExit(f"Inconsistent published GitHub Release state for {tag}")
        print(f"GitHub Release already published for {tag}; leaving it unchanged")
    else:
        result = subprocess.run([
            "gh", "release", "create", tag, "--repo", repository, "--verify-tag",
            "--target", sha, "--title", tag, "--generate-notes",
            "--draft=false", "--prerelease=false",
        ])
        if result.returncode:
            raise SystemExit(f"GitHub Release creation failed for {tag} (exit {result.returncode})")


if __name__ == "__main__":
    main()
