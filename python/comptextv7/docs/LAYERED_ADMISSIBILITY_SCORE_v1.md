# Layered Admissibility Score v1

## Purpose

`layered-admissibility-score-v1` adds a deterministic scoring layer on top of `ContractValidator` results. It converts fixture-level pass/fail outcomes into explicit, serializable layer scores and an overall admissibility score.

## Score fields

The scorer emits:

- `structural_score`
- `relational_score`
- `operational_score`
- `governance_score`
- `overall_admissibility_score`
- `expected_admissible`
- `observed_admissible`
- `passed_contracts`
- `failed_contracts`
- `failure_labels`
- `layer_scores` (per-layer contract lists, labels, and score)

## Layer scoring rules

For each layer (`structural`, `relational`, `operational`, `governance`):

- Score is `passed_contract_count / total_contract_count` in that layer.
- If a layer has no contracts in the input result set, that layer score is `1.0`.
- Passed/failed contract IDs are sorted deterministically.
- Failure labels are sorted, unique, and derived from non-null `failure_label` values.

## Overall scoring rule

`overall_admissibility_score` is the unweighted arithmetic mean of the four layer scores:

- structural
- relational
- operational
- governance

`observed_admissible` is true only when every `ValidationResult.passed` is true.

`expected_admissible` defaults to `observed_admissible` unless an explicit override is provided.

## Determinism guarantees

- No randomness.
- No clock/time dependencies.
- No external API/network calls.
- Stable sorted outputs for contract IDs and failure labels.
- `to_dict` produces JSON-compatible structures with tuple fields serialized as lists.

## Non-goals

- No learned weighting.
- No LLM judges.
- No embeddings.
- No fuzzy matching.
- No semantic equivalence.

## How this connects

- **ContractValidator:** consumes `ValidationResult` objects produced by contract validation.
- **Positive/negative fixtures:** scores both `coding_workflow_pr_review_v1` and `coding_workflow_pr_review_degraded_v1` deterministically.
- **Future degradation curves:** provides stable primitives for trajectory/degradation analysis across fixture families.

## Prototype caveat

- v1 uses unweighted averages only.
- Future versions may add explicit configured weights, but not learned weights.


## Generated artifacts

- `artifacts/layered_admissibility_results.json`
- `docs/benchmarks/layered_admissibility.md`
