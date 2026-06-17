from __future__ import annotations

import json
from pathlib import Path

from src.validation.contract_validator import ContractValidator


FIXTURE_ROOT = Path("fixtures/coding_workflow_pr_review_v1")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_coding_workflow_fixture_contract_bundle_passes_deterministically() -> None:
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

    assert all(result.passed for result in results)
    assert all(result.failure_label is None for result in results)

    observed_contract_ids = sorted(result.contract_id for result in results)
    assert observed_contract_ids == sorted(expected_admissibility["must_hold_contracts"])

    assert expected_failures["expected_failures"] == []

    relational_types = {"reachability", "causality", "invariant"}
    relational_results = [result for result in results if result.contract_type.value in relational_types]
    assert relational_results

    for result in relational_results:
        evidence = result.deterministic_evidence
        assert "comparator_metrics" in evidence
        assert set(evidence["comparator_metrics"].keys()) == {
            "reachability_preservation",
            "dependency_integrity_score",
            "causal_preservation_score",
            "temporal_order_violation_rate",
        }
