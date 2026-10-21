"""Test-owned OpenSpec inputs; never imported by the hook runtime.

``create_project(root, scenario)`` creates a new local OpenSpec tree in an
existing disposable repository. Scenarios are ``base`` (durable spec only),
``pending`` (valid active delta and unchecked task), ``invalid`` (active delta
without a scenario), and ``archived`` (invalid archived delta and unchecked
task). No contributor files, environment configuration, or CLI are read.
``add_invalid_change`` adds the same invalid delta to native acceptance's
already committed pending project.
"""
from pathlib import Path


SPEC = """# Fixture specification

## Purpose
Define deterministic test-owned behavior for isolated hook validation projects.

## Requirements

### Requirement: Fixture behavior
The fixture SHALL provide a stable validation input.

#### Scenario: Fixture validation
- **WHEN** the fixture is validated
- **THEN** its durable specification is valid
"""

VALID_DELTA = """## ADDED Requirements

### Requirement: Pending fixture behavior
The fixture SHALL allow unfinished implementation tasks during validation.

#### Scenario: Pending implementation
- **WHEN** the implementation task remains unchecked
- **THEN** the change is still a valid validation input
"""

INVALID_DELTA = """## ADDED Requirements

### Requirement: Invalid fixture behavior
The fixture SHALL reject this requirement because it has no scenario.
"""


def _write_change(directory, valid):
    """Write deterministic planning artifacts beneath a new change directory."""
    directory.mkdir(parents=True, exist_ok=False)
    files = {
        ".openspec.yaml": "schema: spec-driven\ncreated: 2000-01-01\n",
        "proposal.md": "# Fixture proposal\n\n## Why\nExercise isolated hook validation.\n",
        "design.md": "# Fixture design\n\nUse only test-owned validation inputs.\n",
        "tasks.md": "- [ ] Implement the synthetic fixture behavior.\n",
        "specs/fixture-spec/spec.md": VALID_DELTA if valid else INVALID_DELTA,
    }
    for name, content in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def create_project(root, scenario="base"):
    """Create a deterministic local project, rejecting existing OpenSpec trees."""
    if scenario not in ("base", "pending", "invalid", "archived"):
        raise ValueError(f"Unknown OpenSpec fixture scenario: {scenario}")
    tree = Path(root) / "openspec"
    tree.mkdir(exist_ok=False)
    (tree / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
    spec = tree / "specs/fixture-spec/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(SPEC, encoding="utf-8")
    if scenario == "pending":
        _write_change(tree / "changes/fixture-pending-change", valid=True)
    elif scenario == "invalid":
        add_invalid_change(root)
    elif scenario == "archived":
        _write_change(tree / "changes/archive/2000-01-01-fixture-archived-change", valid=False)


def add_invalid_change(root):
    """Add a test-owned invalid active delta without replacing existing inputs."""
    _write_change(Path(root) / "openspec/changes/fixture-invalid-change", valid=False)
