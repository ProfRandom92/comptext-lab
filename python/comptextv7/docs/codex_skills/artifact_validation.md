# Artifact Validation Skill

## Purpose

Create or update deterministic artifact checks without changing benchmark meaning or unrelated generated outputs.

## When to use

Use for artifacts under `artifacts/`, generator scripts under `scripts/`, regeneration parity tests, stable JSON checks, and committed artifact reproducibility.
Use `scripts/agent_artifact_bundle.py` for deterministic evidence bundles that combine safe gate status with explicit validation evidence.

## Allowed actions

- Inspect existing artifact and generator patterns first.
- Use deterministic JSON with stable key ordering and stable list ordering.
- Prefer generator-to-committed-artifact parity tests.
- Compare byte-identical text when formatting and key order matter.
- Use fixture-bound inputs and explicit metadata such as `artifact_id`, `version`, `evaluation_mode`, `llm_judges`, and `external_apis` when consistent with nearby artifacts.

## Forbidden actions

- No timestamps, random IDs, environment-dependent fields, or network calls.
- No semantic scoring, embeddings, vector DB, external APIs, or LLM judging.
- No unrelated artifact rewrites.
- No benchmark semantic changes unless explicitly requested.
- No broad refactors.
- No commit or push unless explicitly requested.

## Required validation

- Run the focused artifact test.
- Run the exact generator into a temporary path when testing regeneration.
- Confirm `git diff --stat` only shows intended artifact, script, test, or doc files.

## Stop conditions

- Stop if generated output differs from the committed artifact and the reason is unclear.
- Stop if deterministic metadata cannot be defined without inventing claims.
- Stop if the task would require regenerating unrelated artifacts.

## Preferred prompt pattern

```text
Task: add or tighten one deterministic artifact validation.
Allowed files: one artifact, its generator, focused tests, optional docs.
Validation: generate to tmp, compare to committed artifact, run focused tests.
Done when: output is byte-identical or exact JSON-equivalent as specified.
```
