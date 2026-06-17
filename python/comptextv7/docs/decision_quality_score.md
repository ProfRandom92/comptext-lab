# Decision Quality Score

## Purpose

The decision quality engine provides deterministic, rubric-based scoring for CompTextv7 execution decisions. It is intentionally lightweight and does not use LLM judging.

## Data shape

A `QualityEvalRun` returns `overallScore`, per-metric scores, a compact explanation, linked replay step IDs, and linked reference IDs.

Metrics:

- `validity`
- `specificity`
- `correctness`
- `traceability`
- `rollbackSafety`
- `tokenEfficiency`

Core primitives:

- `DecisionQualityEngine`
- `QualityRubric`
- `QualityEvalRun`

## Why it supports token-efficient replay

Traceability rewards links to replay steps and references. Rollback safety rewards snapshot/artifact coverage. Token efficiency rewards staying under a token budget. This makes quality observable from replay metadata without embedding long context or invoking external evaluators.

## Compact JSON example

```json
{
  "overallScore": 0.82,
  "metrics": {
    "validity": 1,
    "specificity": 0.75,
    "correctness": 0.8,
    "traceability": 0.75,
    "rollbackSafety": 0.75,
    "tokenEfficiency": 0.87
  },
  "explanation": "Deterministic quality score 0.82: linked replay/reference evidence present; rollback evidence includes snapshots or artifacts; 520/4000 tokens used within budget.",
  "linkedReplayStepIds": ["step-3"],
  "linkedReferenceIds": ["ctx-fnv1a0abc1234"]
}
```

## Current limitations

The score is deterministic and rubric-based, not semantic LLM judging. It depends on explicit rubric inputs and does not yet infer correctness from source code, tests, or production telemetry.
