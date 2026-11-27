# Implementation Verification

## Initial Inline Implementation Evidence (Historical)

Verification ran in the existing `dev` environment on November 27, 2026, against
the working implementation based on commit
`b7cd10d06f36711769ff09f40ae6e18a4eca6fb1`. This records local implementation
evidence for the initial inline implementation, not deployment or live publication
acceptance. The dedicated-script extraction is recorded separately below.

| Check | Result |
| --- | --- |
| Complete `tools/release` unittest suite | 42 tests passed, including shared PHP/Composer image and strict Composer fixtures |
| Changed workflow YAML | Parsed successfully with unique-key checking using the development environment's installed YAML library |
| Existing workflow definitions | Trigger, workflow permissions, and integrated validation matched the baseline; protected publisher matched after excluding its added `tag`/`sha` outputs |
| Strict change validation | `add-automated-github-releases` passed |
| Strict project validation | One change and all eight existing specs passed; zero failures |
| Artifact and diff review | 24 acceptance scenarios retained, original modified-requirement details preserved, no unresolved local links or temporary-file dependencies, and `git diff --check` passed |

The full release test command was:

```sh
PYTHONPATH=tools python3 -B -m unittest discover -s tools/release -p 'test_*.py'
```

`RELEASE_TEST_HOST_WORKSPACE` was set to the existing container's discovered host
workspace mount so the Docker-backed Composer fixtures could access their
temporary inputs. The documented tooling and development images were used.
Tests did not install package dependencies or publish a version.

OpenSpec checks used:

```sh
openspec validate add-automated-github-releases --strict --no-interactive
openspec validate --all --strict --no-interactive
```

## Initial Publication and Recovery Coverage (Historical)

`tools/release/test_github_release.py` executes the actual new workflow block
against an executable fake `gh` with synthetic credentials and persisted fake
remote state. It also connects the existing real authority harness and native
tag-creation command to that state. The fake client never delegates to installed
GitHub tooling or contacts GitHub.

| Acceptance area | Verified behavior |
| --- | --- |
| Successful publication | Actual authority/job-output mapping supplies the original tag and integrated SHA; first and subsequent releases use the required CLI arguments with generated notes and normal publication settings |
| Job dependency | Failed, canceled, skipped, and ineligible upstream outcomes prevent Release execution; native tag-creation failure produces no Release queries |
| Remote tag verification | Missing tags, wrong SHA/type/reference, missing or invalid outputs, and malformed responses fail before publication or existing-Release acceptance |
| Existing Release | A normal published Release completes repeated attempts without changes to title, notes, assets, or tag refs |
| Conflicts and lookup failures | Drafts, prereleases, malformed records, inconsistent publication state, authentication/API/network errors, HTTP 404, and failed/repeated later pages fail without writes |
| Independent recovery | After failed creation, rerunning only the Release job reuses stored outputs without repeating authority, progression, App-token generation, or tag creation; recovery also succeeds after a later stable tag appears |
| Uncertain creation result | A Release created remotely before a simulated client failure is accepted on retry without edits or duplicate creation |
| Existing guarantees | Bounded job selectors keep permission/checkout assertions separate; all original authority, version, concurrency, and tag-immutability tests still pass |

## Dedicated Script Extraction Evidence (Current)

The approved extraction was verified in `dev` on November 27, 2026. The coordinator
now lives in `tools/release/github_release.py`, with an independent `main()` and
standard-library-only imports. Its main body was checked for AST equivalence to
the previous inline publication body during extraction; environment inputs,
diagnostics, CLI arguments, and recovery behavior were retained.

| Check | Result |
| --- | --- |
| Complete release unittest suite | 44 tests passed, including Docker-backed Composer fixtures and all prior publication/recovery cases |
| Actual workflow command | Existing fixtures execute `python3 -I -B tools/release/github_release.py` against the script copied into a selected temporary checkout |
| Checkout configuration | Release checkout matches the protected publisher's name, action pin, repository, exact `github.workflow_sha`, full/default scope, and disabled credential persistence; all four checkout labels verified |
| Selected automation unavailable | Removing the selected script fails before any API request; candidate, previous-path, root fallback files, and poison Python modules are never executed |
| YAML and regression audit | Unique-key YAML parsing passed; existing trigger, validation job, default permissions, and protected publisher remain unchanged except the previously added publisher outputs |
| Strict OpenSpec validation | Revised change and all eight existing specs passed; 29 acceptance scenarios are present |
| Scope and artifact audit | No formatting/reference errors or temporary-file dependencies; package metadata, required PR workflow, tag authority, shared contract, and API transport remain unchanged |

The full release command and host-workspace mapping described above were reused
with the documented tooling/development images. The fake GitHub CLI uses synthetic
credentials and local state only. Its Python runtime is isolated so poison module
fixtures test the coordinator's isolation without affecting the fake client.

Earlier no-checkout statements in completed task sections 1-4 describe the initial
implementation; section 5 and the current design/specification describe the final
dedicated-script implementation. The historical 42-test result above is not the
validation result for this extraction.

## Evidence Limits

No real App token was issued and no live Release creation or hosted partial-job
rerun was exercised. The tests model dependency scheduling; they do not prove
GitHub's hosted scheduler or runtime token grants. Those live behaviors remain
for a separately authorized real release, without disposable production versions.

No production release branch, manifest version declaration, tag, or GitHub
Release was created. Repository protections, App permissions, and Packagist
configuration were not changed. No commit, push, PR, or merge was performed.
