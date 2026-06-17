# MCP Context Layer

CompText V7 includes a lightweight replay-aware context layer for MCP-style
runtime systems. The layer preserves compact operational context for
deterministic replay validation; it does not execute tools, orchestrate agents,
call external APIs, or judge semantic quality.

## Scope

The context layer is additive to the existing replay fixtures and contracts. It
builds a compact payload from explicit trace, state, and dependency-graph fields:

```json
{
  "task": "mcp_trace_replay_v1",
  "constraints": [
    "execute_external_action:requires_human_approval",
    "execute_external_action:requires_validation_passed"
  ],
  "required_order": [
    "capability_scope_checked",
    "tool_schema_validated",
    "read_context",
    "validate_external_action",
    "execute_external_action"
  ],
  "blockers": [
    ["capability_scope_checked", "execute_external_action"]
  ],
  "dependency_chains": [
    ["validate_external_action", "execute_external_action"]
  ],
  "recovery": [
    ["execute_external_action", "recovery_path_registered"]
  ]
}
```

## Public API

- `build_replay_payload(trace)` extracts compact deterministic commitments.
- `render_prompt_context(payload)` renders a compact prompt-safe text view.
- `validate_replay_payload(payload)` validates replay admissibility from explicit
  payload fields.
- `ContextStore(root).save_context(trace)` writes a stable JSON payload.
- `ContextStore(root).load_context(task_id)` restores the compact payload.
- `save_context(trace, store_dir=...)` and `load_context(task_id, store_dir=...)`
  provide module-level convenience wrappers.

## Deterministic checks

`validate_replay_payload` detects:

- missing preserved constraints as `CONSTRAINT_DRIFT`
- dependency-order drift as `TOOL_ORDER_VIOLATION`
- dependency collapse as `DEPENDENCY_CHAIN_BREAK`
- missing recovery paths as `RECOVERY_PATH_LOSS`

The validator uses exact strings, ordered lists, and explicit dependency edges.
It performs no embedding lookup, fuzzy scoring, probabilistic reasoning, LLM
judging, runtime blocking, or policy enforcement.

## Prompt context rendering

`render_prompt_context(payload)` produces a token-light text form without dumping
raw trace, state, or dependency-graph documents:

```text
task: mcp_trace_replay_v1
admissible: true
constraints:
- execute_external_action:requires_validation_passed
required_order:
- validate_external_action
- execute_external_action
dependencies:
- validate_external_action -> execute_external_action
recovery:
- execute_external_action -> recovery_path_registered
```

## Example artifact

`artifacts/mcp_context_layer_example.json` is a fixture-bound deterministic
example generated from `fixtures/mcp_trace_replay_v1/original`. It contains the
compact replay payload, prompt-context rendering, and validation result for the
baseline MCP trace replay fixture.

## CLI usage

Generate compact prompt context with validation from the baseline MCP fixture:

```bash
python scripts/mcp_context_cli.py \
  --fixture fixtures/mcp_trace_replay_v1/original \
  --render-prompt \
  --validate
```

Add `--json` to emit deterministic JSON containing the compact replay payload,
optional prompt context, and optional validation result.

## Local tool adapter

`scripts/mcp_context_tool.py` accepts one JSON request from stdin or
`--request-file` and emits one deterministic JSON response. It is a local
adapter for later MCP wrapping, not a server or runtime tool executor.

```bash
printf '%s\n' '{"tool":"build_replay_payload","params":{"fixture":"fixtures/mcp_trace_replay_v1/original","render_prompt":true,"validate":true}}' \
  | python scripts/mcp_context_tool.py
```

## Relationship to MCP

This layer augments context integrity for MCP-compatible systems. It is not an
MCP implementation and does not replace MCP transport, runtime execution, or
tool semantics.
