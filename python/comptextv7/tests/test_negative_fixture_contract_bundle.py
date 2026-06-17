from __future__ import annotations

import json
from pathlib import Path

from src.validation.contract_validator import ContractValidator


FIXTURE_ROOT = Path("fixtures/coding_workflow_pr_review_degraded_v1")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_coding_workflow_degraded_fixture_contract_bundle_fails_deterministically() -> None:
    original = {
        **_load_json(FIXTURE_ROOT / "original/trace.json"),
        **_load_json(FIXTURE_ROOT / "original/state.json"),
        "dependency_graph": _load_json(FIXTURE_ROOT / "original/dependency_graph.json"),
    }
    reconstructed = {
        **_load_json(FIXTURE_ROOT / "reconstructed/trace.json"),
        **_load_json(FIXTURE_ROOT / "reconstructed/state.json"),
        "dependency_graph": _load_json(FIXTURE_ROOT / "reconstructed/dependency_graph.json"),
    }

    contracts_dir = FIXTURE_ROOT / "original/contracts"
    contracts = [_load_json(path) for path in sorted(contracts_dir.glob("*.json"))]

    expected_admissibility = _load_json(FIXTURE_ROOT / "expected/admissibility.json")
    expected_failures = _load_json(FIXTURE_ROOT / "expected/failures.json")

    results = ContractValidator().validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)

    assert not expected_admissibility["expected_admissible"]
    assert all(not result.passed for result in results)

    observed_contract_ids = sorted(result.contract_id for result in results)
    assert observed_contract_ids == sorted(expected_admissibility["must_fail_contracts"])

    observed_failure_labels = {result.failure_label for result in results if result.failure_label is not None}
    for label in expected_failures["expected_failures"]:
        assert label in observed_failure_labels

    assert all(result.failure_label is not None for result in results)

    relational_types = {"reachability", "causality", "invariant"}
    relational_results = [result for result in results if result.contract_type.value in relational_types]
    assert relational_results

    observed_comparator_labels: set[str] = set()

    for result in relational_results:
        evidence = result.deterministic_evidence
        assert "comparator_metrics" in evidence
        assert set(evidence["comparator_metrics"].keys()) == {
            "reachability_preservation",
            "dependency_integrity_score",
            "causal_preservation_score",
            "temporal_order_violation_rate",
        }
        assert "comparator_failure_labels" in evidence
        assert isinstance(evidence["comparator_failure_labels"], list)
        observed_comparator_labels.update(evidence["comparator_failure_labels"])

    assert "ORPHAN_DEPENDENCY" in observed_comparator_labels
    assert ({"ORPHAN_DEPENDENCY", "DETACHED_DEPENDENCY"} & observed_comparator_labels)
    assert ({"ORPHAN_DEPENDENCY", "DETACHED_DEPENDENCY", "GRAPH_FRAGMENTATION", "TEMPORAL_ORDER_VIOLATION"} & observed_comparator_labels)

    disallowed_labels = set(expected_failures["disallowed_failures"])
    assert not (disallowed_labels & observed_failure_labels)
