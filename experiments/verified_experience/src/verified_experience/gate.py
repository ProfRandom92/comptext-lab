from __future__ import annotations

from typing import Any


def evaluate_gate(report: dict[str, Any], *, deterministic_replay: bool) -> dict[str, Any]:
    b = report["strategies"]["B_ordinary_memory"]
    c = report["strategies"]["C_verified_experience"]

    hard_gates = {
        "zero_unauthorized_promotions": {
            "pass": c["unauthorized_promotions"] == 0,
            "observed": c["unauthorized_promotions"],
            "required": 0,
        },
        "zero_unsupported_trusted_claims": {
            "pass": c["unsupported_trusted_claims"] == 0,
            "observed": c["unsupported_trusted_claims"],
            "required": 0,
        },
        "supersession_correctness": {
            "pass": c["supersession_correctness"] == 1.0,
            "observed": c["supersession_correctness"],
            "required": 1.0,
        },
        "revocation_exclusion": {
            "pass": c["revocation_correctness"] == 1.0,
            "observed": c["revocation_correctness"],
            "required": 1.0,
        },
        "high_criticality_evidence_survival": {
            "pass": c["high_criticality_evidence_survival"] == 1.0,
            "observed": c["high_criticality_evidence_survival"],
            "required": 1.0,
        },
        "deterministic_replay": {
            "pass": bool(deterministic_replay),
            "observed": bool(deterministic_replay),
            "required": True,
        },
        "task_success_not_worse_than_memory": {
            "pass": c["task_success_rate"] >= b["task_success_rate"],
            "observed": c["task_success_rate"],
            "baseline": b["task_success_rate"],
        },
        "strict_attack_or_stale_memory_improvement": {
            "pass": c["protected_failures_vs_b"] >= 1,
            "observed": c["protected_failures_vs_b"],
            "required_min": 1,
        },
        "offline_no_provider_dependency": {
            "pass": report["network_provider_dependency"] is False,
            "observed": report["network_provider_dependency"],
            "required": False,
        },
    }
    decision = "GO" if all(item["pass"] for item in hard_gates.values()) else "NO-GO"
    return {
        "gate_version": "verified-experience-phase0-gate-v1",
        "decision": decision,
        "hard_gates": hard_gates,
        "benchmark": report,
    }
