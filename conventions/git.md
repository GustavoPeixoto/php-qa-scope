---
id: git
title: Git Convention
when: Whenever inspecting or changing Git state, repository configuration, branches, commits, pushes, tags, history, or GitHub pull requests and reviews.
---

# Git Convention

## Mandatory Explicit Authorization

Agents MUST obtain prior explicit confirmation from the developer before every
operation that changes Git or GitHub state. There are no exceptions to this
requirement. This applies to local and remote operations, regardless of the tool
or execution path: Git, GitHub CLI, APIs, MCP tools, scripts, wrappers, integrations
or delegated execution.

Operations requiring confirmation include, without limitation:

- staging or unstaging; commits and amendments; fetch, pull and push;
- creating, switching, merging or deleting branches; tags and worktrees;
- merge, rebase, cherry-pick, revert, reset, restore, clean and stash operations;
- changes to Git configuration, remotes, hooks or repository settings;
- creating, editing, closing, reopening or merging pull requests;
- submitting, approving, rejecting/requesting changes on, dismissing or otherwise
  changing pull request reviews, including publishing review comments.

Before requesting confirmation, the agent MUST present a concrete, reviewable
description of every proposed operation, its targets and its respective effects.
Identify the repository, affected files/commits, local or remote branches/tags,
remote destination or pull request as applicable. Explain the resulting changes
and any automatic downstream effects, including triggered workflows or
publication. The developer MUST explicitly confirm that disclosed scope before
execution.

An instruction to implement a change, apply an OpenSpec task, continue work,
finalize a change or follow a workflow MUST NOT be interpreted as authorization
for Git or GitHub operations that were not explicitly disclosed and confirmed.
Passing checks, available credentials, repository permissions, branch protection
settings, urgency, convenience, documentation-only changes and recovery needs
MUST NOT substitute for developer confirmation. Silence, an unanswered question
or elapsed time MUST NOT count as confirmation.

### Bounded Batches

The developer MAY confirm a bounded batch in one response only after every
operation in that batch and its respective targets and effects have been
explicitly presented. Confirmation authorizes exactly those operations within
that scope; it MUST NOT extend to subsequent steps or future work.

For example, confirmation to commit does not authorize push. Confirmation to
commit and push does not authorize creating a pull request. Confirmation to
create a pull request does not authorize submitting a review or merging it.

If an operation, target, approved content or effect changes, the agent MUST stop
and obtain new explicit confirmation before proceeding. Unlisted follow-up
actions, retries, recovery and cleanup operations also require new confirmation.
An approval MUST NOT become continuing authority to repeat an operation or
perform additional operations.

## Read-only Inspection

Read-only inspection MAY proceed without confirmation. Examples include
`git status`, `git diff`, `git log`, `git show`, branch/ref listings,
`git ls-remote` and read-only queries of pull requests, reviews and checks.

Judge an operation by its effects, not its name or the tool used. `git fetch`
and `git pull` require confirmation because they change local state. An operation
combining inspection with a state change is subject to mandatory confirmation.

## Working State

Before editing, check the repository state when the task involves commits, branches, pushes, or change review. Do not revert someone else's changes without an explicit request.

## Branches

After authorization to create a branch, use short descriptive names, preferably tied to an OpenSpec change:

```text
change/define-project-conventions
```

If the user or repository already has a more specific convention, follow the existing convention.

## Commits

Before committing, present the intended diff/file scope and commit message, then
obtain explicit confirmation for that commit or a bounded batch including it.

Commits should be small, reviewable, and connected to the change objective. Prefer en-US messages unless instructed otherwise.

Suggested format:

```text
docs: define project conventions
```

Include only files related to the work in the commit. Do not mix temporary handoffs, environment adjustments, and durable content unless necessary.

## Push

A push MUST be explicitly confirmed on its own or as part of a confirmed bounded
batch. Before requesting confirmation, validate what is relevant to the change,
review the diff, and identify the remote, destination branch/tag and commits to
be published. Successful validation does not authorize the push.

## Pull Requests and Reviews

Before creating or editing a pull request, present its proposed title/body,
source branch, target branch and relevant diff. Before submitting an approval,
rejection/request for changes or another review action, present the exact pull
request and commit being reviewed, the proposed review and its effects. Obtain
explicit confirmation for each operation or a bounded batch that includes it.

Before merging, present the exact pull request and head commit, check results,
merge method and resulting effects, including any publication workflow it will
trigger. Obtain explicit confirmation for that merge or a bounded batch including
it. Creating a pull request and passing its checks never authorize its merge.

## Repository Git Hooks

Pre-push policies and agent response to hook failures and bypass decisions belong
in [conventions/git-hooks.md](git-hooks.md).

Confirmation under this convention MUST NOT be interpreted as authorization to
bypass hooks or repository protections. Hook bypass authorization remains a
separate, operation-specific requirement under the Git hook convention.
