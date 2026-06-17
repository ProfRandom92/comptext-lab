# Agent Trace Replay Benchmark

`agent_trace_replay_bench` validates that Comptextv7 can preserve operational
workflow continuity under deterministic replay compression. The benchmark uses
checked-in multi-step coding-agent traces as source data, but it is **not** an
autonomous agent framework and does not execute plans or tools.

## Operational workflow replay

The benchmark pipeline is intentionally small and deterministic:

```text
agent_trace
→ operational state extraction
→ compact replay-safe representation
→ replay reconstruction
→ deterministic continuity validation
```

Each fixture contains realistic workflow material: tasks, decisions,
constraints, tool calls, failures, recovery actions, architecture references,
deployment requirements, unresolved blockers, and dependency relationships. The
runner extracts only the fields needed to continue the workflow:

- `active_task`
- `constraints`
- `architecture_nodes`
- `dependencies`
- `tool_sequence`
- `unresolved_blockers`
- `deployment_requirements`
- `recovery_actions`

## Why agent continuity differs from chat history

Chat history preserves what was said. Operational continuity preserves what must
remain actionable. A long transcript can include greetings, speculative wording,
cosmetic discussion, repeated status updates, and other text that is not needed
to resume a workflow safely.

Agent trace continuity requires preserving the concrete state that determines
what happens next: the active task, constraints, dependency edges, blocker list,
tool order, recovery path, and deployment expectations. If that state is lost,
a replayed workflow can drift even when the raw conversation still appears
readable.

## Operational state vs. transcript storage

This benchmark treats the transcript as source material, not as the replay unit.
The replay unit is a compact JSON representation of the operational fields. That
keeps replay data:

- reviewable in pull requests,
- safe to regenerate in cloud CI,
- independent of model tokenizers,
- free of external service calls, and
- focused on deterministic continuity rather than subjective transcript quality.

## Deterministic replay philosophy

The runner uses only deterministic extraction and validation methods:

- exact field matching,
- regex token counting,
- ordered sequence comparison,
- field-presence validation,
- stable sorting,
- deterministic JSON serialization, and
- fixed-precision metric rounding.

It deliberately avoids embeddings, vector databases, semantic similarity,
cosine similarity, LLM judging, subjective scores, probabilistic ranking,
external APIs, orchestration runtimes, planning engines, PDF ingestion, and heavy
dependencies.

## Replay-safe compression

Replay-safe compression means the compact representation removes transcript
noise while preserving the operational fields required for deterministic
reconstruction. The fixture may contain scenario prose and non-operational
conversation details, but the compact state contains only replay-relevant
workflow data.

The benchmark reports:

- `compression_ratio = original_token_count / compact_token_count`
- `replay_consistency = surviving_operational_fields / total_operational_fields`
- `operational_drift_rate = lost_operational_fields / total_operational_fields`

All metric values are deterministic, reproducible, and emitted with at most six
decimal places.

## Operational drift

Operational drift is the field-level loss between the extracted state and the
replayed state. A drifted replay might forget a blocker, reorder a tool sequence,
drop a dependency, or omit a deployment requirement. The benchmark makes that
loss visible with `operational_drift_rate` instead of relying on subjective
quality judgments.

## Why coding-agent continuity matters

Coding workflows are often multi-step and interruption-prone. A useful replay
state must remember which task is active, what constraints cannot be violated,
which commands already ran, which failures occurred, what recovery actions were
chosen, and which deployment requirements remain. Losing those details can cause
redundant work, unsafe changes, unstable artifacts, or failed CI recovery.

## Why Comptextv7 focuses on operational state preservation

Comptextv7 focuses on preserving compact, replayable operational state because
that is the part of long-context continuity that can be validated without
subjective model judgments. `agent_trace_replay_bench` extends the existing
replay benchmark family from paper-derived state to real multi-step agent
execution traces while staying deterministic, lightweight, typed, CI-friendly,
and reviewable.

The expected narrative is simple: **Comptextv7 preserves operational workflow
continuity under deterministic replay compression.**

## Running the benchmark

```bash
python tests/utils/agent_trace_replay_runner.py
pytest tests/test_agent_trace_replay.py
```

The generated artifact is written to:

```text
artifacts/agent_trace_replay_results.json
```
