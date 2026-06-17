# Iterative Replay Degradation CI Summary

Severity: WARNING
Guidance: Review deterministic degradation labels or non-perfect final replay metrics before merging.

## Aggregate

| Metric | Value |
| --- | --- |
| total fixtures | 6 |
| collapsed fixtures | 0 |
| collapse rate | 0.000000 |
| average replay consistency | 0.895833 |
| average operational drift rate | 0.104167 |
| aggregated failure_mode_counts | EVIDENCE_LOSS=1, HIGH_CRITICAL_EVIDENCE_LOSS=0, CONSTRAINT_DRIFT=0, BLOCKER_DETACHMENT=0 |
| highest collapse cycle observed | N/A |


## Replay sensitivity analysis

Fixture-bound prototype sensitivity surface for deterministic replay/compression parameter changes.

| case_id | max_context_units | max_families | max_bursts | replay_window_seconds | replay_cycles | compression_budget_scale | replay_consistency | operational_drift_rate | evidence_survival_rate | collapse_rate | aggregated_failure_labels |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_budget | 96 | 24 | 24 | 900 | 3 | 1.000000 | 0.708333 | 0.291667 | 0.750000 | 0.000000 | EVIDENCE_LOSS |
| budget_scale_0_75 | 72 | 18 | 18 | 675 | 3 | 0.750000 | 0.500000 | 0.500000 | 0.500000 | 0.000000 | EVIDENCE_LOSS |
| budget_scale_0_50 | 48 | 12 | 12 | 450 | 3 | 0.500000 | 0.458333 | 0.541667 | 0.500000 | 0.000000 | EVIDENCE_LOSS |
| extended_replay_cycles | 96 | 24 | 24 | 900 | 5 | 1.000000 | 0.708333 | 0.291667 | 0.750000 | 0.000000 | EVIDENCE_LOSS |

## Per-fixture summary

| fixture_id | fixture_kind | collapsed | collapse_cycle | final_cycle | final_replay_consistency | final_operational_drift_rate | stop_reason | failure_labels |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ci_failure_trace | agent_trace | false | N/A | 3 | 1.000000 | 0.000000 | max_cycles | none |
| coding_agent_trace | agent_trace | false | N/A | 3 | 1.000000 | 0.000000 | max_cycles | none |
| workflow_recovery_trace | agent_trace | false | N/A | 3 | 1.000000 | 0.000000 | max_cycles | none |
| fate | paper | false | N/A | 3 | 0.875000 | 0.125000 | max_cycles | none |
| prefixguard | paper | false | N/A | 3 | 0.750000 | 0.250000 | max_cycles | EVIDENCE_LOSS |
| self_consolidating | paper | false | N/A | 3 | 0.750000 | 0.250000 | max_cycles | none |
