from __future__ import annotations

from benchmarks.industry_audit import (
    _cloud_triage_latency_ms,
    _pearson_correlation,
    run_industrial_audit,
)


def test_industrial_audit_covers_all_aei_gates_and_passes() -> None:
    report = run_industrial_audit()
    by_category = {gate.category: gate for gate in report.gates}

    assert report.title == "Industrial Economic Resilience & Recursive Improvement"
    assert report.passed
    assert set(by_category) == {
        "Recursive R&D",
        "Expertise Pipeline",
        "Industrial Organization",
        "Economic Access",
    }
    assert by_category["Recursive R&D"].observed >= 80.0
    assert by_category["Expertise Pipeline"].observed >= 0.90
    assert by_category["Industrial Organization"].passed
    assert by_category["Economic Access"].observed >= 0.78


def test_industrial_audit_json_is_dashboard_ready() -> None:
    payload = run_industrial_audit().as_dict()

    assert payload["passed"] is True
    assert len(payload["gates"]) == 4
    assert all("risk_note" in gate for gate in payload["gates"])
    assert all("evidence" in gate for gate in payload["gates"])


def test_audit_math_helpers_are_deterministic() -> None:
    assert _pearson_correlation([1.0, 2.0, 3.0], [1.1, 2.1, 3.1]) > 0.99
    assert _cloud_triage_latency_ms("abc", bandwidth_mbps=1.0, fixed_overhead_ms=10.0) == 10.024
