# CompText V7

CompText V7 is a deterministic replay-validation prototype for compact operational agent/MCP traces, with a KVTC-V7 technical-log compression prototype. The repository checks whether fixture-defined operational commitments survive compaction and replay using local code, committed fixtures, deterministic metrics, and reproducible artifacts.

## What this repo implements

- Deterministic replay validation for compact operational trace state.
- Curated agent trace fixtures under `tests/fixtures/agent_traces/`.
- A deterministic agent trace replay runner in `tests/utils/agent_trace_replay_runner.py`.
- An MCP replay payload layer in `src/comptext_v7/mcp/`.
- Evidence survival helpers in `src/validation/evidence.py`.
- Stable replay failure labels in `src/validation/replay_failure_classifier.py`.
- Committed replay artifacts, including `artifacts/agent_trace_replay_results.json` and `artifacts/mcp_trace_replay_results.json`.
- A KVTC-V7 technical-log compression prototype in `src/core/kvtc_v7.py`.

## What it does not claim

- No embeddings.
- No vector database.
- No LLM judges.
- No external APIs in validation.
- No autonomous agent framework or workflow orchestrator.
- No production-readiness, enterprise-readiness, certification, or compliance claim.
- No universal AI-memory or solved-memory claim.

## Implemented surfaces

| Surface | Source |
| --- | --- |
| Curated agent traces | `tests/fixtures/agent_traces/` |
| Agent trace replay runner | `tests/utils/agent_trace_replay_runner.py` |
| MCP replay payload extraction, rendering, and validation | `src/comptext_v7/mcp/` |
| Evidence survival checks | `src/validation/evidence.py` |
| Replay failure labels | `src/validation/replay_failure_classifier.py` |
| Agent trace replay artifact | `artifacts/agent_trace_replay_results.json` |
| MCP trace replay artifact | `artifacts/mcp_trace_replay_results.json` |
| KVTC-V7 technical-log compression prototype | `src/core/kvtc_v7.py` |

## Committed artifact snapshot

These fixture-bound values are checked against committed deterministic artifacts.

| Signal | Current fixture-bound result |
| --- | ---: |
| Agent trace replay consistency | `1.000000` |
| Paper replay consistency | `0.791667` |
| `CONSERVATIVE` replay consistency | `0.895833` |
| `BALANCED` replay consistency | `0.250000` |
| `AGGRESSIVE` replay consistency | `0.125000` |
| Paper avg compression | `1.347063` |
| Agent avg compression | `1.773954` |
| Agent replay consistency | `1.000000` |
| Agent operational drift | `0.000000` |

The committed comparative replay artifact includes BALANCED failure labels `EVIDENCE_LOSS` and `CONSTRAINT_DRIFT`.

## Validation commands

```bash
npm run layout
pytest -q
npm run check
```

## Limitations

- Results are fixture-bound and based on checked-in data.
- Curated fixtures are not live production traces.
- Replay validation is deterministic and local; it does not use semantic scoring, embeddings, vector search, LLM judges, or external APIs.
- The KVTC-V7 compressor is a prototype for structured technical logs, not a production telemetry platform.
