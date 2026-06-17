# Replay Snapshot Model

## Purpose

The replay snapshot model defines deterministic replay artifacts for CompTextv7. It captures the reference-level state at a step so a future runtime can branch, compare, or inspect executions without rerunning agents.

## Data shape

A `ReplaySnapshot` records snapshot ID, execution ID, step ID, timestamp, input/output references, memory references, tool-call references, token totals, optional quality score, artifact references, and a deterministic state hash. A `ReplayBranch` identifies a branch point from a snapshot. A `ReplayTimeline` is an ordered collection of snapshots for comparison.

Core primitives:

- `ReplaySnapshot`
- `ReplayBranch`
- `ReplayTimeline`
- `ReplayComparator`
- `createReplaySnapshot`
- `branchFromStep`
- `compareReplayRuns`

## Why it supports token-efficient replay

Snapshots retain reference IDs and compact counters rather than full prompts or generated artifacts. Comparisons show token-cost deltas, memory changes, tool-call changes, output reference differences, quality-score deltas, and changed artifact references.

## Compact JSON example

```json
{
  "snapshotId": "snapshot-1a2b3c4d",
  "executionId": "exec-123",
  "stepId": "step-3",
  "timestamp": "2026-05-15T00:00:03.000Z",
  "inputRefIds": ["ctx-fnv1a0abc1234"],
  "outputRefIds": ["artifact-diff-789"],
  "memoryRefIds": ["mem-policy-1"],
  "toolCallRefs": ["tool-call-456"],
  "tokenIn": 120,
  "tokenOut": 80,
  "qualityScore": 0.86,
  "artifactRefs": ["artifact-diff-789"],
  "stateHash": "fnv1a:1a2b3c4d"
}
```

## Current limitations

This is a model-only replay artifact. It does not execute agents, restore files, write durable replay bundles, or provide branching UI. State hashes are deterministic structural hashes, not cryptographic attestations.
