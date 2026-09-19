---
id: language
title: Language Convention
when: Whenever working in this repository; this convention defines the default language for conversation, project context, and artifacts.
---

# Language Convention

## Default Rule

Use en-US as the default language for:

- OpenSpec change artifacts;
- handoffs;
- project documents;
- versioned prompts and internal notes;
- drafts of professional content, unless the declared goal is another language.

## Exceptions

Use another language when:

- the user explicitly asks for it;
- the OpenSpec change defines that the final artifact must use another language;
- the content is a localized version;
- proper nouns, technical terms, APIs, commands, or tool syntax require the original language.

The exception applies to the specific requested artifact. It does not change the repository default language.

## Content And Tool Syntax

Content language and required syntax are different things. Explanatory text should use en-US, but tool-required structure must stay in the expected format.

In OpenSpec:

- preserve structural headings such as `## Why`, `## What Changes`, `## ADDED Requirements`, and `#### Scenario`;
- preserve required normative words such as `MUST` and `SHALL`;
- preserve scenario markers, code blocks, paths, commands, and identifiers;
- do not translate file names, commands, flags, schemas, or IDs.

When in doubt, keep tool syntax intact and write only the human-facing content in en-US.
