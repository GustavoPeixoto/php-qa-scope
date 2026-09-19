---
id: workflow
title: Workflow Convention
when: Whenever exploring, planning, proposing, or applying project changes.
---

# Workflow Convention

## General Rule

Before exploring, planning, proposing, or applying relevant project changes, suggest an OpenSpec-first flow. This includes changing durable documents, creating new documentation areas, changing conventions, revising brand decisions, or producing final artifacts that may become sources of truth.

## Lifecycle

1. Explore: understand context, risks, and alternatives before consolidating the direction.
2. Propose: create or update an OpenSpec change with a proposal, design when needed, specs, and tasks.
3. Apply: implement the change tasks in versioned files.
4. Archive: when the change is complete, sync specs and archive the change.
5. Commit: record the reviewed result in Git.

## Continuity Across Contexts

OpenSpec lifecycle steps often happen across different chats, sessions, or contexts. Change artifacts and handoffs should therefore be clear enough for another agent to continue the work without major inference or dependence on conversational memory.

When leaving a change ready for the next step, record the intent, scope, decisions made, known risks, pending items, and next steps in versioned artifacts or in the appropriate handoff.

## Change Artifact Self-Sufficiency

When creating, reviewing, updating, applying, or preparing to archive a change, validate that `proposal.md`, `design.md`, specs, and `tasks.md` remain understandable without depending on temporary, unversioned, or external files outside OpenSpec.

When a reference to a non-durable or unversioned input is necessary to understand scope, decisions, risks, requirements, or tasks, distill the relevant content and reproduce it in the change artifacts themselves. References to those files may remain only as provenance or contextual trail.

## When Proposing A Change

After running the propose step and generating or updating artifacts, validate parity between what was planned and what was produced. Check that `proposal.md`, `design.md`, specs, and `tasks.md` reflect the relevant scope, requirements, decisions, risks, tasks, and open questions.

Also validate references in generated artifacts. Check that links or mentions of temporary handoffs, unversioned files, or external context are only provenance; if they are needed to understand the change, reproduce the relevant content in the artifacts before considering the proposal ready.

Every `proposal.md` must end with `## Open Questions`. The section must list relevant open points before applying the change and include the priority, criticality, or importance of each item. When there are no relevant pending items, state that explicitly.

## OpenSpec Syntax

Even when content language changes, preserve syntax required by OpenSpec:

- headings such as `## Why`, `## What Changes`, `## ADDED Requirements`, `## MODIFIED Requirements`, and `## REMOVED Requirements`;
- normative words such as `MUST` and `SHALL`;
- scenario blocks starting with `#### Scenario`;
- scenario bullets with `WHEN`, `THEN`, `AND`, or other expected markers;
- capability names, change IDs, and file paths.

## When Applying A Change

- read the dynamic OpenSpec instructions before editing;
- read every indicated context file;
- implement tasks in order when that reduces ambiguity;
- mark each task complete as soon as it is finished;
- pause if a task is ambiguous or if implementation reveals a design issue;
- validate the change before considering the work ready.
