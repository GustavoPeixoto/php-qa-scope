---
id: git
title: Git Convention
when: Whenever working with versioned state, diffs, staging, branches, commits, pushes, history, or change review.
---

# Git Convention

## Working State

Before editing, check the repository state when the task involves commits, branches, pushes, or change review. Do not revert someone else's changes without an explicit request.

## Branches

When a branch is needed, use short descriptive names, preferably tied to an OpenSpec change:

```text
change/define-project-conventions
```

If the user or repository already has a more specific convention, follow the existing convention.

## Commits

Commits should be small, reviewable, and connected to the change objective. Prefer en-US messages unless instructed otherwise.

Suggested format:

```text
docs: define project conventions
```

Include only files related to the work in the commit. Do not mix temporary handoffs, environment adjustments, and durable content unless necessary.

## Push

Push only when the user explicitly asks or when the agreed workflow requires it. Before pushing, validate what is relevant to the change and review the diff.
