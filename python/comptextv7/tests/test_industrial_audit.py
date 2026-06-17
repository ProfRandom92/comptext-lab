from __future__ import annotations

import pytest

from src.audit import run_industrial_economic_resilience_audit
from src.audit.industrial_resilience import (
    activation_verbalizer_rule,
    ecitaro_p1_fault_cases,
    senior_expert_rule,
)


def test_industrial_audit_covers_aei_business_resilience_categories() -> None:
    result = run_industrial_economic_resilience_audit(iterations=1)

    assert result.title == "Industrial Economic Resilience & Recursive Improvement"
    assert result.pass_rate == pytest.approx(1.0)
    assert {scenario.key for scenario in result.scenarios} == {
        "recursive_r_and_d",
        "expertise_pipeline",
        "industrial_reorganization",
        "economic_access",
    }
    assert {scenario.aei_category for scenario in result.scenarios} == {
        "Recursive R&D",
        "Expertise Pipeline",
        "Industrial Organization",
        "Economic Access",
    }


def test_industrial_audit_targets_match_requested_thresholds() -> None:
    by_key = {
        scenario.key: scenario
        for scenario in run_industrial_economic_resilience_audit(iterations=1).scenarios
    }

    assert by_key["recursive_r_and_d"].target_value == pytest.approx(0.80)
    assert by_key["recursive_r_and_d"].measured_value >= 0.80
    assert by_key["expertise_pipeline"].target_value == pytest.approx(0.90)
    assert by_key["expertise_pipeline"].measured_value >= 0.90
    assert by_key["industrial_reorganization"].target_value == pytest.approx(60.0)
    assert by_key["industrial_reorganization"].measured_value >= 60.0
    assert by_key["economic_access"].target_value == pytest.approx(0.78)
    assert by_key["economic_access"].measured_value > 0.78


def test_activation_verbalizer_aligns_with_senior_expert_reference() -> None:
    cases = ecitaro_p1_fault_cases()

    assert all(activation_verbalizer_rule(log_line) == senior_label for log_line, senior_label in cases)
    assert all(senior_expert_rule(log_line) == senior_label for log_line, senior_label in cases)
