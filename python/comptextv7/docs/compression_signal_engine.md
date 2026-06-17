# Compression Signal Engine

## Purpose

The Compression Signal Engine is a deterministic core telemetry layer for CompTextv7. It treats compression instability as an early warning signal that compacted context is no longer matching the known semantic family for the current execution window.

The engine does not run agents, call models, or make subjective judgments. It converts numeric telemetry into a compact prediction error score and a cognitive mode that downstream systems can use as a replanning gate.

## Core claim: Compression is perception

CompTextv7 uses compression behavior as a perception surface. When known work continues to compress like the stable baseline, the system can remain in `habit` or `monitor` mode. When compression becomes unstable across deterministic windows, the system has evidence that the current execution may be seeing a new pattern and should deliberate before continuing.

## Why this is not LLM judging

The engine is pure TypeScript and deterministic:

- no LLM-as-judge calls;
- no external API calls;
- no graph store dependency;
- no swarm orchestration;
- no active inference runtime;
- no MCP integration;
- no random sampling.

Every output is derived from caller-provided numeric input fields and fixed thresholds, weights, hysteresis, and debounce rules.

## Input data shape

Each telemetry window provides a `CompressionSignalInput`:

```ts
{
  executionId: string;
  windowId: string;
  timestamp: string;
  profileId: string;
  compressionRatio: number;
  baselineCompressionRatio: number;
  sparseFrameRate: number;
  baselineSparseFrameRate: number;
  unseenSignatureRate: number;
  tokenEstimate?: number;
  baselineTokenEstimate?: number;
  replayConsistency?: number;
  baselineReplayConsistency?: number;
  metadata?: Record<string, JsonValue>;
}
```

Optional token and replay consistency fields are computed as helper signals when present, but they do not affect the default MVP score unless their weights are explicitly configured.

## MVP formula

All component signals are clamped to the range `0.0` through `1.0`.

```text
prediction_error =
  0.35 * compression_ratio_drop
+ 0.35 * sparse_frame_spike
+ 0.30 * unseen_signature_rate
```

Where:

- `compression_ratio_drop` is the normalized drop from the baseline compression ratio.
- `sparse_frame_spike` is the normalized increase from the baseline sparse frame rate.
- `unseen_signature_rate` is already normalized telemetry and is clamped before scoring.

## Default thresholds

```json
{
  "habitMax": 0.30,
  "monitorMax": 0.55,
  "deliberationMin": 0.62,
  "rollbackRequiredMin": 0.85
}
```

## Hysteresis and debounce

Default hysteresis:

```json
{
  "enterDeliberation": 0.62,
  "exitDeliberation": 0.42
}
```

Default debounce:

```json
{
  "requiredWindows": 2,
  "ofLast": 3
}
```

Rules:

- A single noisy window does not enter `deliberation` unless it reaches `rollback_required` severity.
- The engine enters `deliberation` only when prediction error is at or above `0.62` in at least 2 of the last 3 windows.
- The engine exits `deliberation` only when prediction error is at or below `0.42`.
- `rollback_required` triggers immediately when prediction error is at or above `0.85`.

## Cognitive modes

- `habit`: prediction error is below `0.30`; known compression behavior is stable.
- `monitor`: prediction error is elevated but deliberation debounce has not been satisfied.
- `deliberation`: persistent compression instability has crossed the debounce rule.
- `rollback_required`: severe compression instability crossed the immediate rollback threshold.

## Examples

Stable known family:

```json
{
  "mode": "habit",
  "predictionError": 0.045,
  "triggered": false,
  "reasons": ["compression_ratio_drop exceeded baseline", "sparse_frame_rate increased", "unseen_signature_rate elevated", "prediction_error within habit band"]
}
```

Persistent sparse signature spike:

```json
{
  "mode": "deliberation",
  "predictionError": 0.725,
  "triggered": true,
  "reasons": [
    "compression_ratio_drop exceeded baseline",
    "sparse_frame_rate increased",
    "unseen_signature_rate remained elevated across debounce window",
    "deliberation debounce satisfied"
  ]
}
```

Severe unknown pattern:

```json
{
  "mode": "rollback_required",
  "predictionError": 0.95,
  "triggered": true,
  "reasons": ["prediction_error reached rollback threshold"]
}
```

## Limitations

- Thresholds are initial defaults and require calibration against real telemetry.
- The MVP score intentionally ignores optional token and replay helper signals unless weights are configured.
- The engine emits telemetry decisions only; it does not execute rollback or start an agent runtime.
- The engine assumes callers provide deterministic timestamps and stable window ordering.

## Next integration points

- Attach compression signal results to replay artifacts.
- Feed operational invariants with signal windows and compact reasons.
- Use the engine as a future IAIF planner gate without adding active inference runtime in this layer.
- Add a future dashboard panel after the core behavior is stable.
