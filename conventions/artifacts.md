---
id: artifacts
title: Artifacts Convention
when: Whenever you need to understand, create, use, move, version, reference, or distill artifacts, inputs, handoffs, drafts, `tmp/`, or sources of truth.
---

# Artifacts Convention

## Definition

Artifacts are inputs, documents, specs, conventions, decisions, handoffs, drafts, and deliverables used to carry project work.

This convention separates durable, versionable artifacts from transient artifacts. That separation prevents important decisions from depending on conversational memory, temporary files, or context outside the repository.

## Durable Artifacts

Durable artifacts are versioned sources of truth. They must contain the context needed for another person or agent to continue the work without depending on temporary files.

Examples:

- `README.md`;
- `AGENTS.md`;
- `conventions/`;
- `openspec/`;
- final documentation;
- consolidated decisions;
- OpenSpec specs, proposals, designs, and tasks.

## Transient Artifacts

Transient artifacts are supporting materials. They may guide exploration, review, and implementation, but they must not be treated as durable sources of truth.

Use `tmp/` for temporary inputs, such as:

- handoffs;
- drafts;
- exploration notes;
- dumps;
- support files;
- materials not yet distilled.

Content in `tmp/` must remain ignored by Git, except structural markers such as `tmp/.gitkeep`.

## Distilling Inputs

When a transient artifact is needed to understand scope, a decision, a requirement, a risk, or a task, distill the relevant content into a durable artifact.

References to transient files may remain as provenance, but the main understanding must live in the corresponding durable artifact.

## Use In OpenSpec Changes

Change artifacts must be self-sufficient. `proposal.md`, `design.md`, specs, and `tasks.md` must not depend on handoffs, drafts, or temporary files to be understood.

Before considering a change ready, review whether relevant transient inputs were incorporated into the applicable OpenSpec artifacts.
