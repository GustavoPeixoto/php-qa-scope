#!/usr/bin/env python3
"""Isolated OpenSpec CLI double; never used by contributor hooks."""
import json
import os
from pathlib import Path
import sys


def node_hold():
    os.execvp("node", ["node", "-e", """
const {spawn} = require('node:child_process');
const fs = require('node:fs');
process.on('SIGTERM', () => {});
spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)']);
fs.writeFileSync(process.env.FIXTURE_OPENSPEC_PROBE_MARKER || process.env.QA_HOOKS_RUN_DIR + '/openspec.started', '');
setInterval(() => {}, 1000);
"""])


if sys.argv[1:] == ["--version"]:
    if os.environ.get("FIXTURE_OPENSPEC_PROBE_MARKER"):
        node_hold()
    print(os.environ.get("FIXTURE_OPENSPEC_VERSION", "1.14.0"))
    raise SystemExit(0)
if sys.argv[1:] != ["validate", "--all", "--strict", "--no-interactive", "--json"]:
    raise SystemExit(2)
mode = os.environ.get("FIXTURE_OPENSPEC", "passed")
if mode == "node-hold":
    node_hold()
if mode == "malformed":
    print("not JSON")
else:
    valid = mode != "failed"
    print(json.dumps({"version": "1.0", "root": {"path": str(Path.cwd())},
        "items": [{"id": "fixture", "type": "change", "valid": valid, "issues": []}],
        "summary": {"totals": {"items": 1, "passed": int(valid), "failed": int(not valid)}}}))
raise SystemExit(1 if mode == "failed" else 0)
