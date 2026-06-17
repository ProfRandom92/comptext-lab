# Docs Positioning Skill

## Purpose

Update CompTextv7 documentation while preserving conservative replay-integrity positioning and scope boundaries.

## When to use

Use for README, docs, reports, positioning, benchmark explanations, MCP docs, artifact narratives, and PR-facing summaries.

## Allowed actions

- Inspect existing docs and nearby wording before editing.
- Keep claims fixture-bound, deterministic, and artifact-backed.
- Prefer small docs-only patches for positioning changes.
- Separate core CompTextv7 documentation from showcase or brand/demo work.
- Use exact validation or artifact names when referencing evidence.
- State limitations and non-goals clearly.

## Forbidden actions

- No production-ready, clinical-grade, universal memory, or solved-memory claims.
- No semantic scoring, embeddings, vector DB, external APIs, or LLM judging claims.
- No autonomous agent framework, workflow orchestrator, runtime tool execution, or policy-engine positioning.
- No invented benchmark results or unrun validation claims.
- No Chilli/Hatch/Pet or showcase asset changes unless explicitly requested.
- No commit or push unless explicitly requested.

## Required validation

- Run `git diff --stat`.
- Confirm only intended docs files changed.
- Run no broad checks unless the docs change is tied to generated artifacts or explicitly requested.

## Stop conditions

- Stop if documentation would broaden project identity beyond deterministic replay-integrity validation.
- Stop if a metric lacks a committed artifact or exact source.
- Stop if requested copy conflicts with repository non-goals.

## Preferred prompt pattern

```text
Task: make one docs-only positioning update.
Allowed files: exact docs paths.
Constraints: fixture-bound claims, no overclaims, no showcase/core mixing.
Validation: git diff --stat and changed-file scope check.
Done when: wording matches existing CompTextv7 positioning and non-goals.
```
