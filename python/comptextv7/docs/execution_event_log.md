# Append-only Execution Event Log

## Purpose

The execution event log records compact, event-sourced execution telemetry for CompTextv7 without storing giant prompts repeatedly. It is the observable timeline behind replayable AI execution.

## Data shape

An `ExecutionEvent` contains `executionId`, `stepId`, `agentId`, timestamp, event type, input/output reference IDs, token counts, latency, status, and a small JSON-serializable `compactPayload`.

Supported event types include execution lifecycle events, context selection, memory injection, tool and file activity, generated diffs, commands, tests, quality evaluation, replay snapshot creation, completion, and failure.

Core primitives:

- `ExecutionEvent`
- `ExecutionEventLog`
- `InMemoryExecutionEventStore`
- `appendExecutionEvent`
- `getExecutionTimeline`
- `summarizeExecutionEvents`

## Why it supports token-efficient replay

Events link to semantic references instead of duplicating raw context. Timeline summaries provide deterministic totals for tokens, latency, event counts, and referenced artifacts, so later replay tooling can inspect what happened without reconstructing full prompts from logs.

## Compact JSON example

```json
{
  "executionId": "exec-123",
  "stepId": "step-2",
  "agentId": "agent-core",
  "timestamp": "2026-05-15T00:00:02.000Z",
  "eventType": "tool.called",
  "inputRefIds": ["ctx-fnv1a0abc1234"],
  "outputRefIds": ["tool-call-456"],
  "tokenIn": 42,
  "tokenOut": 8,
  "latencyMs": 25,
  "status": "succeeded",
  "compactPayload": { "toolName": "local-check" }
}
```

## Current limitations

The initial store is in-memory only. It enforces append-only behavior at the API level but does not yet provide durable persistence, cross-process ordering, signatures, or artifact export.
