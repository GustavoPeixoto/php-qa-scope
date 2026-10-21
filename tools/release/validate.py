"""Read-only release contract checks; no package imports or dependencies."""

import argparse
import json
import os
from pathlib import Path
import sys


if __package__:
    from .contract import ReleaseError, validate, version_tuple
    from .github_api import api, remote_tags
else:
    from contract import ReleaseError, validate, version_tuple
    from github_api import api, remote_tags


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
