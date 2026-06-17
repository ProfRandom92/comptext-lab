import json
import math

import pytest

from src.validation.replay_failure_classifier import EVIDENCE_LOSS, REPLAY_FAILURE_LABELS
from tests.utils.iterative_replay_degradation_runner import (
    BENCHMARK_NAME,
    DEFAULT_MAX_CYCLES,
    IterativeReplayConfig,
    ReplaySensitivityCase,
    artifact_json,
    build_iterative_replay_degradation_artifact,
    build_replay_sensitivity_analysis_artifact,
    run_iterative_replay_degradation,
    stable_json_dump,
)

REQUIRED_CYCLE_FIELDS = {
    "blocker_survival_rate",
    "constraint_survival_rate",
    "cycle",
    "evidence_survival_rate",
    "failure_labels",
    "failure_mode_counts",
    "has_high_critical_evidence",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "replay_consistency",
}

RATE_FIELDS = {
    "blocker_survival_rate",
    "constraint_survival_rate",
    "evidence_survival_rate",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "replay_consistency",
}


def _decimal_places(value: float) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    return len(text.split(".", 1)[1]) if "." in text else 0


def _assert_cycle_rates_are_bounded(cycle: dict[str, object]) -> None:
    for field in RATE_FIELDS:
        value = cycle[field]
        assert isinstance(value, float)
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0


def _boundary_sensitivity_case(
    *,
    case_id: str = "zero_boundary",
    max_context_units: int = 0,
    max_families: int = 0,
    max_bursts: int = 0,
    replay_window_seconds: int = 0,
    replay_cycles: int = 1,
    compression_budget_scale: float = 1.0,
) -> ReplaySensitivityCase:
    return ReplaySensitivityCase(
        case_id=case_id,
        max_context_units=max_context_units,
        max_families=max_families,
        max_bursts=max_bursts,
        replay_window_seconds=replay_window_seconds,
        replay_cycles=replay_cycles,
        compression_budget_scale=compression_budget_scale,
        trend_expectation="deterministic boundary fixture for severe replay truncation",
    )


def test_iterative_replay_artifact_shape_is_stable() -> None:
    artifact = build_iterative_replay_degradation_artifact()
    assert artifact["benchmark"] == BENCHMARK_NAME
    assert artifact["config"]["max_cycles"] == DEFAULT_MAX_CYCLES
    assert isinstance(artifact["runs"], list)
    assert artifact["runs"]

    for run in artifact["runs"]:
        assert set(run) == {"collapse_cycle", "collapsed", "cycles", "fixture_id", "fixture_kind", "stop_reason"}
        assert run["fixture_kind"] in {"agent_trace", "paper"}
        assert isinstance(run["fixture_id"], str)
        assert isinstance(run["collapsed"], bool)
        assert run["stop_reason"]
        assert isinstance(run["cycles"], list)
        assert run["cycles"]
        if run["collapsed"]:
            assert isinstance(run["collapse_cycle"], int)
        else:
            assert run["collapse_cycle"] is None

        for expected_cycle, cycle in enumerate(run["cycles"], start=1):
            assert set(cycle) == REQUIRED_CYCLE_FIELDS
            assert cycle["cycle"] == expected_cycle
            assert isinstance(cycle["failure_labels"], list)
            assert set(cycle["failure_mode_counts"]) == set(REPLAY_FAILURE_LABELS)
            assert isinstance(cycle["has_high_critical_evidence"], bool)
            for field in RATE_FIELDS:
                assert isinstance(cycle[field], float)
                assert math.isfinite(cycle[field])
                assert 0.0 <= cycle[field] <= 1.0
                assert _decimal_places(cycle[field]) <= 6


def test_iterative_replay_max_cycles_is_respected() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=2),
        fixture_kinds=("agent_trace",),
    )
    assert runs
    assert all(len(run["cycles"]) <= 2 for run in runs)
    assert all(run["stop_reason"] == "max_cycles" for run in runs)
    assert all(run["collapsed"] is False for run in runs)


def test_iterative_replay_collapse_criteria_can_trigger() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=3, min_replay_consistency=0.9),
        fixture_kinds=("paper",),
    )
    collapsed = [run for run in runs if run["collapsed"]]
    assert collapsed
    first = collapsed[0]
    assert first["collapse_cycle"] == 1
    assert first["stop_reason"] == "min_replay_consistency"
    assert len(first["cycles"]) == 1


def test_iterative_replay_does_not_collapse_stable_agent_fixture() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=3),
        fixture_kinds=("agent_trace",),
    )
    assert runs
    for run in runs:
        assert run["collapsed"] is False
        assert run["collapse_cycle"] is None
        assert run["stop_reason"] == "max_cycles"
        assert len(run["cycles"]) == 3
        assert all(cycle["replay_consistency"] == 1.0 for cycle in run["cycles"])
        assert all(cycle["operational_drift_rate"] == 0.0 for cycle in run["cycles"])


def test_iterative_replay_output_is_deterministic_across_runs() -> None:
    first = build_iterative_replay_degradation_artifact()
    second = build_iterative_replay_degradation_artifact()
    assert first == second
    assert stable_json_dump(first) == stable_json_dump(second)
    assert json.loads(stable_json_dump(first)) == first
    assert artifact_json(first) == stable_json_dump(first)


def test_iterative_replay_failure_mode_counts_use_classifier_labels() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=1, fatal_failure_modes=(EVIDENCE_LOSS,)),
        fixture_kinds=("paper",),
    )
    evidence_loss_runs = [run for run in runs if EVIDENCE_LOSS in run["cycles"][0]["failure_labels"]]
    assert evidence_loss_runs
    for run in evidence_loss_runs:
        cycle = run["cycles"][0]
        assert cycle["failure_mode_counts"][EVIDENCE_LOSS] == 1
        assert run["collapsed"] is True
        assert run["stop_reason"] == f"fatal_failure_mode:{EVIDENCE_LOSS}"


def test_iterative_replay_rejects_unbounded_or_invalid_config() -> None:
    with pytest.raises(ValueError, match="max_cycles"):
        build_iterative_replay_degradation_artifact(config=IterativeReplayConfig(max_cycles=0))
    with pytest.raises(ValueError, match="min_replay_consistency"):
        build_iterative_replay_degradation_artifact(
            config=IterativeReplayConfig(min_replay_consistency=1.1)
        )


def test_comparative_replay_profiles_cover_expected_profiles() -> None:
    from tests.utils.iterative_replay_degradation_runner import (
        COMPARATIVE_PROFILES,
        build_comparative_replay_degradation_artifact,
    )

    artifact = build_comparative_replay_degradation_artifact()
    profiles = artifact["profiles"]

    assert [profile["profile"] for profile in profiles] == list(COMPARATIVE_PROFILES)
    assert [profile["profile"] for profile in profiles] == ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]
    for profile in profiles:
        aggregate = profile["aggregate"]
        assert set(aggregate) == {
            "aggregated_failure_labels",
            "average_evidence_survival_rate",
            "average_operational_drift_rate",
            "average_replay_consistency",
            "collapse_rate",
        }
        assert isinstance(profile["runs"], list)
        assert profile["runs"]


def test_comparative_replay_output_is_stable_and_ordered() -> None:
    from tests.utils.iterative_replay_degradation_runner import (
        build_comparative_replay_degradation_artifact,
        stable_json_dump,
    )

    first = build_comparative_replay_degradation_artifact()
    second = build_comparative_replay_degradation_artifact()

    assert first == second
    assert stable_json_dump(first) == stable_json_dump(second)
    assert [profile["profile"] for profile in first["profiles"]] == [
        "CONSERVATIVE",
        "BALANCED",
        "AGGRESSIVE",
    ]
    consistency = [profile["aggregate"]["average_replay_consistency"] for profile in first["profiles"]]
    drift = [profile["aggregate"]["average_operational_drift_rate"] for profile in first["profiles"]]
    evidence = [profile["aggregate"]["average_evidence_survival_rate"] for profile in first["profiles"]]
    assert consistency == sorted(consistency, reverse=True)
    assert drift == sorted(drift)
    assert evidence == sorted(evidence, reverse=True)


def test_replay_sensitivity_analysis_surface_is_stable_and_ordered() -> None:
    from tests.utils.iterative_replay_degradation_runner import (
        SENSITIVITY_CASES,
        build_replay_sensitivity_analysis_artifact,
    )

    first = build_replay_sensitivity_analysis_artifact()
    second = build_replay_sensitivity_analysis_artifact()

    assert first == second
    assert stable_json_dump(first) == stable_json_dump(second)
    assert first["scope"] == "fixture-bound deterministic replay sensitivity analysis"
    assert [case["parameters"]["case_id"] for case in first["cases"]] == [
        case.case_id for case in SENSITIVITY_CASES
    ]
    for expected_order, case in enumerate(first["cases"], start=1):
        assert set(case) == {
            "aggregate",
            "case_order",
            "final_failure_labels_by_fixture",
            "fixture_count",
            "parameters",
        }
        assert case["case_order"] == expected_order
        assert case["fixture_count"] == len(case["final_failure_labels_by_fixture"])
        assert "runs" not in case
        assert "cycles" not in case
        assert set(case["aggregate"]) == {
            "aggregated_failure_labels",
            "collapse_rate",
            "evidence_survival_rate",
            "operational_drift_rate",
            "replay_consistency",
        }
        assert set(case["final_failure_labels_by_fixture"]) == {
            "ci_failure_trace",
            "coding_agent_trace",
            "fate",
            "prefixguard",
            "self_consolidating",
            "workflow_recovery_trace",
        }


def test_replay_sensitivity_budget_pressure_has_monotonic_degradation() -> None:
    from tests.utils.iterative_replay_degradation_runner import build_replay_sensitivity_analysis_artifact

    artifact = build_replay_sensitivity_analysis_artifact()
    budget_cases = [
        case
        for case in artifact["cases"]
        if str(case["parameters"]["case_id"]).startswith("budget")
        or case["parameters"]["case_id"] == "baseline_budget"
    ]

    consistency = [case["aggregate"]["replay_consistency"] for case in budget_cases]
    drift = [case["aggregate"]["operational_drift_rate"] for case in budget_cases]
    evidence = [case["aggregate"]["evidence_survival_rate"] for case in budget_cases]
    assert consistency == sorted(consistency, reverse=True)
    assert drift == sorted(drift)
    assert evidence == sorted(evidence, reverse=True)


def test_iterative_artifact_exposes_additive_sensitivity_analysis() -> None:
    artifact = build_iterative_replay_degradation_artifact()
    sensitivity = artifact["sensitivity_analysis"]

    assert sensitivity["benchmark"] == f"{BENCHMARK_NAME}_sensitivity_analysis"
    assert sensitivity["cases"]
    assert "runs" in artifact
    assert all("runs" not in case for case in sensitivity["cases"])


def test_iterative_replay_cycle_boundaries_remain_deterministic() -> None:
    observed_by_cycle_count = {}
    for replay_cycles in (1, 2, 5):
        runs = run_iterative_replay_degradation(
            config=IterativeReplayConfig(max_cycles=replay_cycles),
            fixture_kinds=("agent_trace",),
        )
        observed_by_cycle_count[replay_cycles] = stable_json_dump(runs)

        assert [run["fixture_id"] for run in runs] == [
            "coding_agent_trace",
            "ci_failure_trace",
            "workflow_recovery_trace",
        ]
        assert all(len(run["cycles"]) == replay_cycles for run in runs)
        for run in runs:
            assert [cycle["cycle"] for cycle in run["cycles"]] == list(range(1, replay_cycles + 1))
            assert run["stop_reason"] == "max_cycles"
            for cycle in run["cycles"]:
                _assert_cycle_rates_are_bounded(cycle)

    assert observed_by_cycle_count == {
        replay_cycles: stable_json_dump(
            run_iterative_replay_degradation(
                config=IterativeReplayConfig(max_cycles=replay_cycles),
                fixture_kinds=("agent_trace",),
            )
        )
        for replay_cycles in (1, 2, 5)
    }


def test_replay_sensitivity_zero_budget_truncation_is_bounded_and_ordered() -> None:
    sensitivity_case = _boundary_sensitivity_case()
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=sensitivity_case.replay_cycles),
        fixture_kinds=("paper",),
        sensitivity_case=sensitivity_case,
    )

    assert [run["fixture_id"] for run in runs] == ["prefixguard", "fate", "self_consolidating"]
    assert stable_json_dump(runs) == stable_json_dump(
        run_iterative_replay_degradation(
            config=IterativeReplayConfig(max_cycles=sensitivity_case.replay_cycles),
            fixture_kinds=("paper",),
            sensitivity_case=sensitivity_case,
        )
    )
    for run in runs:
        assert run["collapsed"] is False
        assert run["stop_reason"] == "max_cycles"
        assert len(run["cycles"]) == 1
        cycle = run["cycles"][0]
        _assert_cycle_rates_are_bounded(cycle)
        assert cycle["replay_consistency"] == 0.0
        assert cycle["operational_drift_rate"] == 1.0
        assert cycle["evidence_survival_rate"] == 0.0
        assert cycle["failure_labels"] == [EVIDENCE_LOSS]
        assert cycle["failure_mode_counts"][EVIDENCE_LOSS] == 1


def test_replay_sensitivity_zero_budget_schema_stays_additive_and_compact() -> None:
    sensitivity_case = _boundary_sensitivity_case()
    artifact = build_replay_sensitivity_analysis_artifact(
        fixture_kinds=("paper",),
        sensitivity_cases=(sensitivity_case,),
    )

    assert artifact == build_replay_sensitivity_analysis_artifact(
        fixture_kinds=("paper",),
        sensitivity_cases=(sensitivity_case,),
    )
    assert artifact["benchmark"] == f"{BENCHMARK_NAME}_sensitivity_analysis"
    assert artifact["scope"] == "fixture-bound deterministic replay sensitivity analysis"
    assert len(artifact["cases"]) == 1
    case = artifact["cases"][0]
    assert set(case) == {
        "aggregate",
        "case_order",
        "final_failure_labels_by_fixture",
        "fixture_count",
        "parameters",
    }
    assert case["case_order"] == 1
    assert case["fixture_count"] == 3
    assert case["parameters"] == sensitivity_case.as_dict()
    assert case["aggregate"] == {
        "aggregated_failure_labels": [EVIDENCE_LOSS],
        "collapse_rate": 0.0,
        "evidence_survival_rate": 0.0,
        "operational_drift_rate": 1.0,
        "replay_consistency": 0.0,
    }
    assert case["final_failure_labels_by_fixture"] == {
        "fate": [EVIDENCE_LOSS],
        "prefixguard": [EVIDENCE_LOSS],
        "self_consolidating": [EVIDENCE_LOSS],
    }
    assert "runs" not in case
    assert "cycles" not in case


def test_replay_sensitivity_near_zero_individual_budgets_do_not_crash() -> None:
    cases = (
        _boundary_sensitivity_case(
            case_id="near_zero_context",
            max_context_units=1,
            max_families=24,
            max_bursts=24,
            replay_window_seconds=900,
        ),
        _boundary_sensitivity_case(
            case_id="near_zero_families",
            max_context_units=96,
            max_families=0,
            max_bursts=24,
            replay_window_seconds=900,
        ),
        _boundary_sensitivity_case(
            case_id="near_zero_bursts",
            max_context_units=96,
            max_families=24,
            max_bursts=0,
            replay_window_seconds=900,
        ),
        _boundary_sensitivity_case(
            case_id="near_zero_window",
            max_context_units=96,
            max_families=24,
            max_bursts=24,
            replay_window_seconds=0,
        ),
    )

    artifact = build_replay_sensitivity_analysis_artifact(
        fixture_kinds=("agent_trace", "paper"),
        sensitivity_cases=cases,
    )

    assert [case["parameters"]["case_id"] for case in artifact["cases"]] == [
        case.case_id for case in cases
    ]
    for expected_order, case in enumerate(artifact["cases"], start=1):
        assert case["case_order"] == expected_order
        assert case["fixture_count"] == 6
        assert set(case["aggregate"]) == {
            "aggregated_failure_labels",
            "collapse_rate",
            "evidence_survival_rate",
            "operational_drift_rate",
            "replay_consistency",
        }
        for field in (
            "collapse_rate",
            "evidence_survival_rate",
            "operational_drift_rate",
            "replay_consistency",
        ):
            value = case["aggregate"][field]
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


@pytest.mark.parametrize("compression_budget_scale", [0.0, -1.0, math.nan, math.inf])
def test_replay_sensitivity_rejects_invalid_compression_budget_scale(
    compression_budget_scale: float,
) -> None:
    with pytest.raises(ValueError, match="compression_budget_scale"):
        build_replay_sensitivity_analysis_artifact(
            fixture_kinds=("paper",),
            sensitivity_cases=(
                _boundary_sensitivity_case(compression_budget_scale=compression_budget_scale),
            ),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("replay_cycles", 0, "replay_cycles"),
        ("max_context_units", -1, "max_context_units"),
        ("max_families", -1, "max_families"),
        ("max_bursts", -1, "max_bursts"),
        ("replay_window_seconds", -1, "replay_window_seconds"),
    ),
)
def test_replay_sensitivity_rejects_unbounded_or_negative_parameters(
    field: str,
    value: int,
    message: str,
) -> None:
    kwargs = {field: value}
    with pytest.raises(ValueError, match=message):
        build_replay_sensitivity_analysis_artifact(
            fixture_kinds=("paper",),
            sensitivity_cases=(_boundary_sensitivity_case(**kwargs),),
        )


def test_severe_degradation_failure_label_collapse_is_stable() -> None:
    sensitivity_case = _boundary_sensitivity_case(replay_cycles=3)
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(
            max_cycles=sensitivity_case.replay_cycles,
            fatal_failure_modes=(EVIDENCE_LOSS,),
        ),
        fixture_kinds=("paper",),
        sensitivity_case=sensitivity_case,
    )

    assert [run["fixture_id"] for run in runs] == ["prefixguard", "fate", "self_consolidating"]
    for run in runs:
        assert run["collapsed"] is True
        assert run["collapse_cycle"] == 1
        assert run["stop_reason"] == f"fatal_failure_mode:{EVIDENCE_LOSS}"
        assert len(run["cycles"]) == 1
        assert run["cycles"][0]["failure_labels"] == [EVIDENCE_LOSS]
