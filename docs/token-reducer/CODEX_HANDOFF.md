# CODEX HANDOFF — CompText Token Reducer P0/P1

Status: PREP_ONLY
Prepared: 2026-08-26
Branch: `feature/token-reducer-prep`
Baseline: `main@b997f62503066a81ed8ec53b3b9b154c064e00a8`

## Authoritative Scope

Continue only in `ProfRandom92/comptext-lab` on branch:

```text
feature/token-reducer-prep
```

Do not touch `comptext-windows-agent` or any Stage 8 worktree/runtime paths.

Read first:

```text
docs/token-reducer/README.md
docs/token-reducer/TOKEN_TRAJECTORY_SCHEMA.md
docs/token-reducer/PLUGIN_TRACK.md
```

## Mission

Prepare and implement **P0 measurement only** before adding optimization logic.

Goal:

```text
trustworthy token trajectory measurement
before token reduction claims
```

This is actual token reduction work, not quota bypass and not a pricing-model exercise.

## P0 Required Outcome

Implement the smallest local deterministic measurement harness that can emit a machine-readable record compatible with:

```text
comptext.token_trajectory.v1
```

The harness must distinguish:

```text
input tokens
cached input tokens
uncached input tokens
output tokens
reasoning tokens
model turns
tool calls/tool batches
wait/poll-only turns
files loaded
raw tool-output bytes
model-visible tool-output bytes
retrieval/re-read counts
compactions/subagents
wall time
task success/evidence integrity
```

If a counter cannot be measured from available local evidence, emit `null` or explicit `unavailable`; do not invent it.

## Implementation Placement

Prefer existing monorepo boundaries:

```text
crates/comptext-core
  shared record/schema primitives if appropriate

crates/comptext-cli
  deterministic local CLI exposure if appropriate

python/comptextv7
  benchmark/replay analysis if this is the better existing fit
```

Do not create a new standalone product/repository.

Inspect current code before selecting placement.

## P0 Acceptance Criteria

```text
[ ] one fixture/run can emit token trajectory JSON
[ ] schema version is explicit
[ ] measured vs estimated vs unavailable fields are distinguishable
[ ] cached and uncached input remain separate
[ ] quality/task success is not inferred from model self-report
[ ] evidence freshness fields exist
[ ] raw evidence can be referenced by digest/id
[ ] two repeated fixture runs produce structurally stable records
[ ] tests cover missing counters and malformed input
[ ] existing workspace tests remain green
```

## P1 Is Specification-Only Until P0 Passes

Do not yet implement the full token reducer.

After P0 passes, prepare implementation tickets/specs for:

```text
P1.1 task-specific MCP enabled_tools planning
P1.2 task-routed repo instruction selection
P1.3 progressive skill disclosure
P1.4 independent read-only operation batching
P1.5 wait/poll avoidance
P1.6 bounded/reversible tool-output delivery
```

## Plugin Roles

Use existing roles; do not duplicate them:

```text
CompText Context   -> minimum task context contract
CompText Guard     -> pre-action local safety
CompText Evidence  -> post-mutation freshness/raw evidence
CompText Benchmark -> Raw vs CompText quality/efficiency comparison
Plugin Eval        -> independent plugin/skill token-budget + benchmark gate
Plugin Autopilot   -> packaging/release only after gates pass
stark AI Developer -> optional bounded implementation helper, no authority
```

## External Donors

Use as reference/code donors, not mandatory dependencies during P0:

```text
Save-The-Token
Open330/context-compress
Headroom
RTK
squeez
Aider / semantic code-map approaches
```

Important principles:

```text
select before load
compute before context
batch before repeated model re-entry
compress after selection, not instead of selection
preserve raw evidence
measure tokens_per_success
```

## Benchmark Arms For Later

```text
B0 normal baseline
B1 native tool/instruction slimming
B2 B1 + selective context
B3 B2 + batching
B4 B3 + reversible output reduction
B5 B4 + checkpoint handoff
H1 baseline + Headroom comparison
```

Hold model/reasoning/task/repo constant in matched experiments.

## Initial Engineering Gate

Do not turn this into a public savings claim.

Future `COMPTEXT_TOKEN_REDUCER_V1_PASS` target:

```text
success_rate >= baseline
median_total_input_tokens <= baseline * 0.80
median_model_turns_on_batchable_tasks <= baseline * 0.80
median_model_visible_noisy_tool_bytes <= baseline * 0.40
evidence_loss_regressions == 0
raw_evidence_retrievable == true
```

## Work Rules

- evidence before claims
- no unrelated cleanup
- no new provider proxy
- no automatic Codex/MCP config mutation
- no subagent fan-out for P0 unless strictly necessary
- no broad repository rereads when deterministic path discovery is sufficient
- batch independent read-only inspections
- keep tool output bounded
- tests before completion claim

## Final P0 Report

Return:

```text
P0_STATUS
PLACEMENT
FILES_CHANGED
SCHEMA_IMPLEMENTED
COUNTERS_MEASURED
COUNTERS_UNAVAILABLE
TESTS
WORKSPACE_VALIDATION
PLUGIN_EVAL_NEXT_STEP
P1_READY
BLOCKERS
```
