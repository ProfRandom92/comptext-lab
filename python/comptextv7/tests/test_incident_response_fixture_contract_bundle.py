from __future__ import annotations

import json
from pathlib import Path

from src.validation.contract_validator import ContractValidator


BASELINE_ROOT = Path("fixtures/incident_response_page_triage_v1")
SEVERE_ROOT = Path("fixtures/incident_response_page_triage_degraded_v1")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _payload(root: Path) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    original = {
        **_load_json(root / "original/trace.json"),
        **_load_json(root / "original/state.json"),
        "dependency_graph": _load_json(root / "original/dependency_graph.json"),
    }
    reconstructed = {
        **_load_json(root / "reconstructed/trace.json"),
        **_load_json(root / "reconstructed/state.json"),
        "dependency_graph": _load_json(root / "reconstructed/dependency_graph.json"),
    }
    contracts = [_load_json(path) for path in sorted((root / "original/contracts").glob("*.json"))]
    return original, reconstructed, contracts


def test_incident_response_baseline_contracts_pass_deterministically() -> None:
    original, reconstructed, contracts = _payload(BASELINE_ROOT)
    expected = _load_json(BASELINE_ROOT / "expected/admissibility.json")

    results = ContractValidator().validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)

    assert expected["expected_admissible"] is True
    assert all(result.passed for result in results)
    assert sorted(result.contract_id for result in results) == sorted(expected["must_hold_contracts"])


def test_incident_response_severe_emits_only_expected_failure_labels() -> None:
    original, reconstructed, contracts = _payload(SEVERE_ROOT)
    expected_admissibility = _load_json(SEVERE_ROOT / "expected/admissibility.json")
    expected_failures = _load_json(SEVERE_ROOT / "expected/failures.json")

    results = ContractValidator().validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)

    assert expected_admissibility["expected_admissible"] is False
    assert all(not result.passed for result in results)

    observed_contracts = sorted(result.contract_id for result in results)
    assert observed_contracts == sorted(expected_admissibility["must_fail_contracts"])

    observed_labels = sorted({result.failure_label for result in results if result.failure_label is not None})
    assert observed_labels == sorted(expected_failures["expected_failures"])
