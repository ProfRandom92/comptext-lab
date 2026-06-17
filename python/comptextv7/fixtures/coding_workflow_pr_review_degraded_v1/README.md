# coding_workflow_pr_review_degraded_v1

Deterministic negative/degraded fixture for validating replay degradation detection in the ContractValidator + DependencyGraphComparator stack.

## Intentional degradations

1. **Ordering degradation**: reconstructed trace removes the `human_review` step and jumps from `run_tests`/`test_failure` to `merge`, breaking required ordering `generate_patch -> run_tests -> human_review -> merge`.
2. **Reachability degradation**: reconstructed dependency graph removes recovery edges from `test_failure` to both `rollback` and `escalate_to_human`, violating `min_paths = 1` recovery expectations.
3. **Causality degradation**: reconstructed dependency graph removes the causal edge `security_scan_failed -> deploy_blocked`.
4. **Invariant degradation**: reconstructed dependency graph keeps `human_review` but removes all incoming dependencies, producing an orphan dependency condition.

## Expected ContractValidator failures

The fixture is expected to be inadmissible and to fail with:

- `POLICY_ORDER_BROKEN`
- `RECOVERY_PATH_INVALID`
- `CAUSAL_DEPENDENCY_LOSS`
- `INVARIANT_VIOLATION`

## Comparator-level allowed failures

Relational checks may also emit comparator-level failure labels that are allowed for this degraded fixture:

- `ORPHAN_DEPENDENCY`
- `DETACHED_DEPENDENCY`
- `GRAPH_FRAGMENTATION`
- `TEMPORAL_ORDER_VIOLATION`

This fixture is intentionally synthetic, deterministic, and scoped to replay-validation prototype behavior.
