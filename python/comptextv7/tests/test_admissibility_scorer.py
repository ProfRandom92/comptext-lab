from __future__ import annotations

import json
from pathlib import Path

from src.validation.admissibility_scorer import AdmissibilityScorer
from src.validation.contract_validator import ContractType, ContractValidator, Layer, ValidationResult


def _result(contract_id: str, layer: Layer, passed: bool, failure_label: str | None = None) -> ValidationResult:
    return ValidationResult(
        contract_id=contract_id,
        layer=layer,
        contract_type=ContractType.ORDERING,
        passed=passed,
        severity="high",
        failure_label=failure_label,
        deterministic_evidence={},
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_validation_results(fixture_root: Path) -> list[ValidationResult]:
    original = {
        **_load_json(fixture_root / "original/trace.json"),
        **_load_json(fixture_root / "original/state.json"),
        "dependency_graph": _load_json(fixture_root / "original/dependency_graph.json"),
    }
    reconstructed = {
        **_load_json(fixture_root / "reconstructed/trace.json"),
        **_load_json(fixture_root / "reconstructed/state.json"),
        "dependency_graph": _load_json(fixture_root / "reconstructed/dependency_graph.json"),
    }
    contracts = [_load_json(path) for path in sorted((fixture_root / "original/contracts").glob("*.json"))]
    return ContractValidator().validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)


def test_all_contracts_pass_score_is_one() -> None:
    score = AdmissibilityScorer().score(
        [
            _result("op_a", Layer.OPERATIONAL, True),
            _result("rel_a", Layer.RELATIONAL, True),
        ]
    )

    assert score.overall_admissibility_score == 1.0
    assert score.observed_admissible is True
    assert score.failed_contracts == ()


def test_failed_relational_contract_reduces_relational_and_overall_score() -> None:
    score = AdmissibilityScorer().score(
        [
            _result("rel_a", Layer.RELATIONAL, True),
            _result("rel_b", Layer.RELATIONAL, False, "REL_FAIL"),
        ]
    )

    assert score.relational_score == 0.5
    assert score.overall_admissibility_score == 0.875
    assert score.observed_admissible is False


def test_failed_operational_contract_reduces_operational_score() -> None:
    score = AdmissibilityScorer().score([_result("op_a", Layer.OPERATIONAL, False, "OP_FAIL")])

    assert score.operational_score == 0.0
    assert score.overall_admissibility_score == 0.75


def test_empty_results_are_admissible_with_all_scores_one() -> None:
    score = AdmissibilityScorer().score([])

    assert score.structural_score == 1.0
    assert score.relational_score == 1.0
    assert score.operational_score == 1.0
    assert score.governance_score == 1.0
    assert score.overall_admissibility_score == 1.0
    assert score.observed_admissible is True


def test_failure_labels_are_sorted_unique() -> None:
    score = AdmissibilityScorer().score(
        [
            _result("a", Layer.RELATIONAL, False, "Z_LABEL"),
            _result("b", Layer.OPERATIONAL, False, "A_LABEL"),
            _result("c", Layer.GOVERNANCE, False, "A_LABEL"),
        ]
    )

    assert score.failure_labels == ("A_LABEL", "Z_LABEL")


def test_passed_and_failed_contracts_are_sorted() -> None:
    score = AdmissibilityScorer().score(
        [
            _result("c", Layer.RELATIONAL, True),
            _result("a", Layer.RELATIONAL, False, "X"),
            _result("b", Layer.OPERATIONAL, True),
        ]
    )

    assert score.passed_contracts == ("b", "c")
    assert score.failed_contracts == ("a",)


def test_to_dict_is_stable_and_json_compatible() -> None:
    scorer = AdmissibilityScorer()
    score = scorer.score([_result("b", Layer.OPERATIONAL, True), _result("a", Layer.RELATIONAL, False, "REL_FAIL")])

    as_dict_first = scorer.to_dict(score)
    as_dict_second = scorer.to_dict(score)

    assert as_dict_first == as_dict_second
    assert isinstance(as_dict_first["passed_contracts"], list)
    assert isinstance(as_dict_first["failed_contracts"], list)
    assert isinstance(as_dict_first["failure_labels"], list)
    assert isinstance(as_dict_first["layer_scores"], list)


def test_expected_admissible_override() -> None:
    score = AdmissibilityScorer().score([_result("rel_a", Layer.RELATIONAL, True)], expected_admissible=False)

    assert score.expected_admissible is False
    assert score.observed_admissible is True


def test_scores_positive_fixture_contract_results() -> None:
    results = _fixture_validation_results(Path("fixtures/coding_workflow_pr_review_v1"))
    score = AdmissibilityScorer().score(results)

    assert score.observed_admissible is True
    assert score.overall_admissibility_score == 1.0


def test_scores_negative_fixture_contract_results() -> None:
    results = _fixture_validation_results(Path("fixtures/coding_workflow_pr_review_degraded_v1"))
    score = AdmissibilityScorer().score(results)

    assert score.observed_admissible is False
    assert score.relational_score < 1.0
    assert score.operational_score < 1.0
    assert "POLICY_ORDER_BROKEN" in score.failure_labels
    assert "RECOVERY_PATH_INVALID" in score.failure_labels
    assert "CAUSAL_DEPENDENCY_LOSS" in score.failure_labels
    assert "INVARIANT_VIOLATION" in score.failure_labels
