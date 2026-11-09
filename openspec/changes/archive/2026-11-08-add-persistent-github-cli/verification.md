# Verification

## Local implementation — 2026-11-08 (America/Sao_Paulo)

The new development image and shared configuration volume were implemented on
`change/release-validation-tooling`, based on `72b2342da420efe6a183cc54024a90b3eb703f5b`.
This is uncommitted working-tree validation, not a GitHub check run for this
implementation. Delivery remains in the existing PR #6 after separately
authorized staging, commit, push, and description updates.

## Image and runtime evidence

Build command:

```sh
docker build --file docker/dev/Dockerfile --target development --build-arg WORKSPACE_DIR=/php-qa-scope --tag php-qa-scope-pr-node-development .
```

The build completed successfully and produced image
`sha256:63fdacc566fa947302663addb6343375ea056df84594c462b1effb62e11e2ae5`.
It used the existing shared tooling stages and development utility installation,
without real account credentials or token build arguments.

Observed in terminated probe containers, before their removal:

| Probe | Result |
| --- | --- |
| GitHub CLI | `gh version 2.23.0 (2023-02-27 Debian 2.23.0+dfsg1-1)` |
| Node | `v24.22.1`, matching the existing tooling image |
| OpenSpec | `1.14.0` |
| Configuration directory | `/home/dev/.config/gh`, mode `700`, owner `dev:dev` |
| Account file in the fresh image | Absent |
| Modern `--skip-ssh-key` login flag | Not supported by this distribution version |

The login documentation therefore uses supported flags and tells the operator
to decline SSH key generation and select `Skip` for upload. No real login,
SSH provisioning, credential-helper configuration, or GitHub account mutation
was performed.

## Configuration and persistence evidence

`docker compose config --format json` resolved exactly one dev mount with source
`github-cli` and target `/home/dev/.config/gh`. Its project-scoped volume name is
`php-qa-scope_github-cli`; PHP has no corresponding mount. The Dev Container
uses the same Compose service without another mount for that path. Its separate
Codex mount and all existing Codex/hook initialization commands remain intact.

The new runtime case created a uniquely named, labeled test volume and used two
containers from the built image, with networking disabled. It verified:

- Initial directory mode `0700`, matching dev UID/GID, and non-root writing.
- No initial `hosts.yml` or CLI configuration file in the fresh volume.
- A marker set through `gh config set`, then read back through `gh config get`
  in the replacement container.
- A synthetic account file with mode `0600`, whose SHA-256 remained identical
  across container replacement; no credential content was printed or sent to
  GitHub.
- Removal of the test containers and volume. No labeled test volumes remained
  after the suite.

This proves image availability and persistence mechanics. Compose/Dev Container
configuration was inspected, but the active Dev Container was not rebuilt and
its real post-create lifecycle was not run. A real browser login and credential
reuse after active recreation remain specifically authorized rollout operations,
outside this implementation checklist. Expiration, revocation, logout, and volume
removal can still invalidate authentication.

## Checks

- `PYTHONPATH=tools python3 -B -m unittest discover -s tools/pr_qa -p 'test_*.py' -q`:
  **21 tests, 16 passed, 5 opt-in skips** before actual-image execution.
- `PR_QA_RUNTIME_TESTS=1 PYTHONPATH=tools python3 -B -m unittest pr_qa.test_runtime -v`:
  **3 passed**, including persistent CLI configuration, Node/development tooling,
  and shared PHP versions/development isolation; 27.260 seconds observed.
- Resolved Compose and parsed Dev Container checks passed, including no duplicate
  credential mount and retained Codex initialization.
- Selected strict OpenSpec validation passed. Before spec sync, all strict
  validation passed for **7 items** (six main specs plus this change).
- `git diff --check` passed.

## Preservation and remaining operational gates

Before/after checks confirmed unchanged HEAD, index entries, and stash
`4623b179667bb347b6e8dadf8c0be380162f7a11`. Tracked content outside the five
implementation paths remained byte-identical, including the archived QA change,
Composer manifest/lock, PHP Dockerfile, and QA workflow.

The running dev container remained `9c6ce9fec1f4` and PHP remained `9ffe34b6ea71`.
The actual credential/Codex volumes and the former laboratory checkout/evidence
were not removed or modified. Temporary runtime resources were the only volumes
created and removed by this work.

The implementation can be synced and archived before its commit without claiming
deployment or merge. Real environment recreation and browser login, Git staging/
commit/push, PR editing, approval, and merge require their separate authorization.
No authentication token was placed in image layers, source files, or logs.

## Local closure

The apply workflow reported **6/6 implementation tasks complete**. All three
requirements and seven scenarios were synced into the new main specification
`openspec/specs/development-github-cli/spec.md`. Purpose and requirement/scenario
blocks were compared verbatim with the delta and matched; no delta operation
headers remain in the main spec.

All six change files were archived under
`openspec/changes/archive/2026-11-08-add-persistent-github-cli/` without content
changes during the move. This closure note was appended afterward. Strict final
OpenSpec validation passed for **7/7 main specifications**, and no active change
remains. `git diff --check` and post-create shell syntax checks passed.

Archive means locally completed implementation and disposable-runtime proof.
The active environment still uses its earlier image; real authentication and
recreation are not claimed. Publication in PR #6 and eventual merge remain
separate operations, without another closure PR or an implementation checkbox
that depends on future merge.

## Follow-up: Compose-owned Codex state — 2026-11-08 (America/Sao_Paulo)

This section supersedes the earlier setup and closure details for the current
revision while retaining their evidence. The user requested removal of the
redundant post-create chmod and moving the Codex mount into Compose. The same
local change was reopened, its six affected implementation tasks revalidated,
and its specification extended with the existing-Codex-volume reuse scenario.

Before editing, the active dev mount at `/home/dev/.codex` was inspected. Its
physical volume was `php-qa-scope_codex`, with Compose project label
`php-qa-scope` and volume-key label `codex`. Adding `codex: {}` to Compose
resolved to that exact physical name. Both Codex and GitHub CLI mounts are now
declared only on the dev service; the Dev Container inherits them with no
separate mounts and PHP inherits neither.

The post-create command retains ownership repair for both directories and all
existing setup commands, with no chmod. GH mode `0700` remains established by
image initialization. The image now also creates `.codex` as dev so a fresh
Codex volume is writable without root. The current Codex volume was never
mounted into a probe, copied, renamed, removed, or recreated.

### Revised runtime proof

The same development build command succeeded, producing image
`sha256:db4976ff7b7b406f7f38855aecef667b79706411c1426c6f48bad685e71fd169`.
The existing dependency/tooling layers were reused; only the final dev-directory
initialization layer changed. No tool version declaration changed.

The revised persistence case used two uniquely named disposable volumes and two
successive containers with networking disabled. It verified matching dev UID/GID
and non-root writing in both directories, retained GH directory mode `0700`,
CLI configuration readback, and unchanged SHA-256 values for synthetic GitHub
and Codex account files with mode `0600`. All owned test containers and both
volumes were removed; no volumes with the fixture label remained afterward.

- PR QA discovery: **21 tests, 16 passed, 5 opt-in skips**, 0.298 seconds.
- Actual-image runtime suite: **3 passed**, 24.224 seconds, including Node/dev
  tooling, PHP shared/development isolation, and both persistent state volumes.
- Resolved Compose checks confirmed the same active Codex volume name and no
  duplicate or PHP state mounts. Parsed Dev Container checks confirmed retained
  ownership/setup commands, no separate mounts, and no post-create chmod.
- Post-create shell syntax and `git diff --check` passed. Selected/all strict
  OpenSpec validation passed before resynchronizing the updated main spec.

### Preserved state and gates

Before/after checks confirmed identical HEAD, stash, index entries, and staged
diff. Existing staged files were preserved; this adjustment changes only their
worktree versions. Active dev/PHP service IDs and the Codex volume name,
creation metadata, and labels stayed identical. Tracked content outside this
change's implementation/specification paths remained unchanged, including the
archived QA change, Composer inputs, PHP Dockerfile, and workflows.

The active environment has not been recreated, and no real account was
authenticated. Moving the mount declaration preserves data by identity; it does
not prove a future active recreation or account login has already occurred.
Activation, authentication, staging/commit, push, PR edits, approval, and merge
remain separately authorized operations.

### Follow-up closure

All six revised tasks were completed. The main specification was resynced with
the Codex volume-reuse scenario; all three requirements and eight scenarios
match the delta, with Purpose preserved. The same change was rearchived at its
original local archive path after verifying completion and sync equivalence.
Strict final validation passed for **7/7 main specifications**, with no active
change remaining, and the full HEAD diff passed whitespace checks. Earlier
staged versions were preserved; no staging, commit, push, active recreation,
authentication, or real-volume mutation was performed for this adjustment.
