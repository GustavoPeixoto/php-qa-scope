"""Recheck publication eligibility using current GitHub data before credentials."""

import base64
import json
import os
from pathlib import Path
import re
import sys

if __package__:
    from .contract import ReleaseError, validate
    from .github_api import api, remote_tags, validate_repository
else:
    automation = Path(__file__).resolve().parent
    for module in ("contract.py", "github_api.py"):
        if not (automation / module).is_file():
            raise ImportError(f"Required release automation module is missing: {module}")
    sys.path.insert(0, str(automation))
    from contract import ReleaseError, validate
    from github_api import api, remote_tags, validate_repository


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def authorize(repository, event, request=api):
    """Bind the event to the merged PR and evaluate fresh publication inputs."""
    validate_repository(repository)
    require(isinstance(event, dict) and event.get("action") == "closed", "Expected closed PR event")
    number = event.get("number")
    require(type(number) is int and number > 0, "Invalid PR number")
    event_pr = event.get("pull_request")
    require(isinstance(event_pr, dict), "Invalid PR event")
    expected_sha = event_pr.get("merge_commit_sha")
    require(isinstance(expected_sha, str) and re.fullmatch(r"[0-9a-f]{40}", expected_sha), "Invalid integrated SHA")

    pr = request(f"repos/{repository}/pulls/{number}")
    require(isinstance(pr, dict), "Invalid PR response")
    require(type(pr.get("number")) is int and pr["number"] == number, "PR identity mismatch")
    require(pr.get("merged") is True and pr.get("state") == "closed", "PR has not merged")
    base, head = pr.get("base"), pr.get("head")
    require(isinstance(base, dict) and isinstance(base.get("repo"), dict), "Invalid release base")
    require(base["repo"].get("full_name") == repository, "Wrong release base repository")
    require(isinstance(head, dict) and isinstance(head.get("repo"), dict), "Invalid release origin")
    branch = head.get("ref")
    require(isinstance(branch, str) and branch.startswith("release/"), "Expected release branch")
    sha = pr.get("merge_commit_sha")
    require(sha == expected_sha, "Integrated SHA changed")

    content = request(f"repos/{repository}/contents/composer.json?ref={sha}")
    require(isinstance(content, dict) and content.get("type") == "file" and content.get("path") == "composer.json", "Invalid manifest response")
    require(content.get("encoding") == "base64" and isinstance(content.get("content"), str), "Invalid manifest encoding")
    encoded = content["content"].replace("\n", "").replace("\r", "")
    manifest = json.loads(base64.b64decode(encoded, validate=True).decode("utf-8"))
    result = validate(branch, manifest, remote_tags(repository, request), repository,
                      head["repo"].get("full_name"), base.get("ref"))
    require(result["release"] is True, "Expected eligible release")
    return {"tag": result["tag"], "sha": sha}


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    result = authorize(os.environ["GITHUB_REPOSITORY"], event)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"tag={result['tag']}\nsha={result['sha']}\n")


if __name__ == "__main__":
    main()
