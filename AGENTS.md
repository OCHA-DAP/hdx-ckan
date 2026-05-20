# Agent Instructions
These rules apply to all AI-assisted code changes in this repository.

Before working on any task in this repository, read all LLM context files located in [`ckanext-hdx_theme/llm_docs/`](ckanext-hdx_theme/llm_docs/).

These files contain essential context about the project's architecture, design system, templates, CSS/JS conventions, and other domain knowledge required to contribute correctly.

## Core Principles
- Understand existing logic before editing.
- Preserve current behavior unless a request explicitly requires a behavior change.
- Prefer the smallest possible diff that solves the request.
- Extend existing modules, helpers, and patterns before adding new abstractions.
- Avoid unrelated refactors, renames, or formatting-only edits.
- Keep public interfaces and config contracts stable unless change is required.
- If behavior must change, clearly explain what changed and why.

## How to use
1. Read every file in [`ckanext-hdx_theme/llm_docs/`](ckanext-hdx_theme/llm_docs/) at the start of each session.
2. Apply the conventions described there when generating or modifying code.
3. When new architectural decisions are made, update the relevant file in [`ckanext-hdx_theme/llm_docs/`](ckanext-hdx_theme/llm_docs/) so the context stays accurate.
4. When a task is marked `implemented`, update the requirement file: replace the **Open questions** section with a **Decisions Taken** table (one row per question, recording the actual resolution), and **remove** the Verification section — it has served its purpose.
