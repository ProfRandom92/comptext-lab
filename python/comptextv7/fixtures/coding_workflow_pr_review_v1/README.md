# coding_workflow_pr_review_v1

## Purpose

This fixture is the first deterministic end-to-end contract bundle for a realistic coding workflow replay. It validates the merged `ContractValidator` + `DependencyGraphComparator` stack on a small, explicit, serializable scenario.

## Workflow represented

The fixture models a pull-request flow:

1. `generate_patch`
2. `run_tests`
3. `human_review`
4. `merge`

It also includes recovery and security semantics:

- recovery branch from `test_failure` to both `rollback` and `escalate_to_human`
- security causality edge from `security_scan_failed` to `deploy_blocked`

## Contracts in this bundle

- `pre_merge_review` (ordering): enforces `generate_patch -> run_tests -> human_review -> merge`
- `recovery_path_available` (reachability): requires at least one deterministic recovery path from `test_failure`
- `security_causal_block` (causality): requires `security_scan_failed -> deploy_blocked` causal edge
- `no_orphan_tool_calls` (invariant): enforces predefined `no_orphan_dependencies` rule

## Expected admissibility

`expected/admissibility.json` marks this fixture as `expected_admissible: true` with all listed contracts required to hold.

## Degraded reconstruction failures this fixture is designed to catch

If future reconstructed artifacts degrade, this fixture should surface deterministic failures such as:

- ordering regression (`POLICY_ORDER_BROKEN`)
- missing recovery reachability (`RECOVERY_PATH_INVALID`)
- missing security causality (`CAUSAL_DEPENDENCY_LOSS`)
- orphan or detached dependency regressions (`INVARIANT_VIOLATION`, `ORPHAN_DEPENDENCY`, `DETACHED_DEPENDENCY`)

This fixture is intentionally fixture-scoped and does not claim benchmark or production generality.
