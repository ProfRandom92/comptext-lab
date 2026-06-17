# coding_workflow_pr_review_moderate_v1

Deterministic moderate degraded fixture for coding workflow replay-validation contracts.

## Intentional degradations

1. **Reachability degradation**: reconstructed dependency graph removes recovery edges from `test_failure` to `rollback` and `escalate_to_human`, violating `recovery_path_available`.
2. **Causality degradation**: reconstructed dependency graph removes `security_scan_failed -> deploy_blocked`, violating `security_causal_block`.

## Preserved properties

- Ordering sequence remains intact in reconstructed trace.
- No orphan dependency invariant is preserved.

## Expected failures

- `RECOVERY_PATH_INVALID`
- `CAUSAL_DEPENDENCY_LOSS`

This fixture is intentionally synthetic, deterministic, and scoped to this fixture family.
