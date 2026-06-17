# MCP Context Layer Skill

## Purpose

Work on the lightweight MCP-compatible replay-aware context layer while preserving CompTextv7 replay-integrity boundaries.

## When to use

Use for changes involving `src/comptext_v7/mcp/`, `scripts/mcp_context_cli.py`, compact replay payloads, prompt-context rendering, validation, save/load helpers, or token-light replay-safe context.

## Allowed actions

- Inspect repository files before editing.
- Make the smallest safe patch.
- Reuse `build_replay_payload`, `render_prompt_context`, `validate_replay_payload`, `ContextStore`, `save_context`, and `load_context`.
- Keep examples fixture-bound, usually `fixtures/mcp_trace_replay_v1/original`.
- Add focused tests in `tests/test_mcp_context_layer.py`.
- Update `docs/mcp_context_layer.md` when public behavior changes.

## Forbidden actions

- No semantic scoring, embeddings, vector DB, external APIs, or LLM judging.
- No autonomous orchestration or runtime tool execution unless explicitly scoped.
- No broad refactors or changes to existing benchmark semantics.
- No ContractValidator behavior changes unless explicitly requested.
- No commit or push unless explicitly requested.

## Required validation

- `python -m compileall -q src/comptext_v7/mcp`
- `pytest tests/test_mcp_context_layer.py -q`
- If CLI behavior changes, run the affected `python scripts/mcp_context_cli.py ...` command.

## Stop conditions

- Stop if fixture shape is unclear.
- Stop if a change requires non-deterministic behavior.
- Stop if requested behavior would broaden MCP context into orchestration, policy enforcement, or tool execution.

## Preferred prompt pattern

```text
Task: make one deterministic MCP context-layer change.
Allowed files: exact MCP files, focused tests, and docs.
Validation: compile MCP package and run tests/test_mcp_context_layer.py.
Done when: replay-safe ordering, validation output, and no raw trace leakage are verified.
```
