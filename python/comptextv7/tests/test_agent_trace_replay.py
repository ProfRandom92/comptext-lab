from __future__ import annotations

import json
import math

from tests.utils.agent_trace_replay_runner import (
    BENCHMARK_NAME,
    OPERATIONAL_FIELDS,
    TRACE_SPECS,
    artifact_json,
    build_agent_trace_replay_artifact,
    canonical_json,
    normalize_float,
    run_agent_trace_replay,
    stable_json_dump,
)

EXPECTED_TRACE_ORDER = [str(spec["trace"]) for spec in TRACE_SPECS]

PUBLIC_ROW_FIELDS = {
    "blocker_survival_rate",
    "compact_token_count",
    "compression_ratio",
    "constraint_survival_rate",
    "dependency_survival_rate",
    "evidence_survival_rate",
    "evidence_survived",
    "evidence_total",
    "failure_labels",
    "has_evidence",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "original_token_count",
    "replay_consistency",
    "replay_token_count",
    "tool_sequence_survival_rate",
    "trace",
}
AGGREGATE_FIELDS = {
    "avg_blocker_survival_rate",
    "avg_compression_ratio",
    "avg_constraint_survival_rate",
    "avg_dependency_survival_rate",
    "avg_evidence_survival_rate",
    "avg_high_critical_evidence_survival_rate",
    "failure_labels",
    "avg_operational_drift_rate",
    "avg_replay_consistency",
    "avg_tool_sequence_survival_rate",
    "trace_count",
}
RATE_FIELDS = (
    "blocker_survival_rate",
    "constraint_survival_rate",
    "dependency_survival_rate",
    "evidence_survival_rate",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "replay_consistency",
    "tool_sequence_survival_rate",
)
AGGREGATE_RATE_FIELDS = (
    "avg_blocker_survival_rate",
    "avg_constraint_survival_rate",
    "avg_dependency_survival_rate",
    "avg_evidence_survival_rate",
    "avg_high_critical_evidence_survival_rate",
    "avg_operational_drift_rate",
    "avg_replay_consistency",
    "avg_tool_sequence_survival_rate",
)


def _decimal_places(value: float) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    return len(text.split(".", 1)[1]) if "." in text else 0


def test_agent_trace_replay_artifact_schema_is_valid() -> None:
    artifact = build_agent_trace_replay_artifact()
    assert set(artifact) == {"aggregate", "benchmark", "traces"}
    assert artifact["benchmark"] == BENCHMARK_NAME
    assert isinstance(artifact["traces"], list)
    assert len(artifact["traces"]) == 3

    aggregate = artifact["aggregate"]
    assert isinstance(aggregate, dict)
    assert set(aggregate) == AGGREGATE_FIELDS
    assert aggregate["trace_count"] == len(artifact["traces"])
    assert aggregate["trace_count"] > 0

    for row in artifact["traces"]:
        assert set(row) == PUBLIC_ROW_FIELDS
        assert isinstance(row["trace"], str)
        for field in RATE_FIELDS + ("compression_ratio",):
            assert isinstance(row[field], float)
            assert math.isfinite(row[field])
            assert _decimal_places(row[field]) <= 6
        for field in RATE_FIELDS:
            assert 0.0 <= row[field] <= 1.0
        assert row["compression_ratio"] > 1.0
        assert row["compact_token_count"] < row["original_token_count"]
        for field in ("original_token_count", "compact_token_count", "replay_token_count"):
            assert isinstance(row[field], int)
            assert row[field] > 0
        assert isinstance(row["evidence_total"], int)
        assert isinstance(row["evidence_survived"], int)
        assert isinstance(row["failure_labels"], list)
        assert all(isinstance(label, str) for label in row["failure_labels"])
        assert isinstance(row["has_evidence"], bool)
        assert row["has_evidence"] == (row["evidence_total"] > 0)
        assert 0 <= row["evidence_survived"] <= row["evidence_total"]

    for field in AGGREGATE_RATE_FIELDS + ("avg_compression_ratio",):
        assert isinstance(aggregate[field], float)
        assert math.isfinite(aggregate[field])
        assert _decimal_places(aggregate[field]) <= 6
    assert isinstance(aggregate["failure_labels"], list)
    assert all(isinstance(label, str) for label in aggregate["failure_labels"])
    for field in AGGREGATE_RATE_FIELDS:
        assert 0.0 <= aggregate[field] <= 1.0
    assert aggregate["avg_compression_ratio"] > 1.0


def test_agent_trace_replay_aggregate_matches_recomputed_values() -> None:
    artifact = build_agent_trace_replay_artifact()
    traces = artifact["traces"]
    aggregate = artifact["aggregate"]
    assert isinstance(traces, list)
    assert isinstance(aggregate, dict)

    field_pairs = {
        "avg_blocker_survival_rate": "blocker_survival_rate",
        "avg_compression_ratio": "compression_ratio",
        "avg_constraint_survival_rate": "constraint_survival_rate",
        "avg_dependency_survival_rate": "dependency_survival_rate",
        "avg_evidence_survival_rate": "evidence_survival_rate",
        "avg_high_critical_evidence_survival_rate": "high_critical_evidence_survival_rate",
        "avg_operational_drift_rate": "operational_drift_rate",
        "avg_replay_consistency": "replay_consistency",
        "avg_tool_sequence_survival_rate": "tool_sequence_survival_rate",
    }
    for aggregate_field, trace_field in field_pairs.items():
        recomputed = normalize_float(sum(float(row[trace_field]) for row in traces) / len(traces))
        assert aggregate[aggregate_field] == recomputed


def test_agent_trace_replay_serialization_is_stable_pretty_sorted_and_newline_terminated() -> None:
    artifact = build_agent_trace_replay_artifact()
    serialized = stable_json_dump(artifact)
    reparsed = json.loads(serialized)
    assert reparsed == artifact
    assert serialized == artifact_json(artifact)
    assert serialized == json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert serialized.endswith("\n")
    assert serialized.startswith('{\n  "aggregate"')
    assert '\n  "traces": [\n' in serialized


def test_repeated_artifacts_and_replay_metrics_are_reproducible() -> None:
    first = build_agent_trace_replay_artifact()
    second = build_agent_trace_replay_artifact()
    assert first == second
    assert canonical_json(first) == canonical_json(second)

    for first_row, second_row in zip(first["traces"], second["traces"], strict=True):
        assert first_row["replay_consistency"] == second_row["replay_consistency"]
        assert first_row["operational_drift_rate"] == second_row["operational_drift_rate"]


def test_no_empty_operational_fields_and_replay_matches_compact_state() -> None:
    for run in run_agent_trace_replay():
        original_fields = run.original_state["operational_fields"]
        replayed_fields = run.replayed_state["operational_fields"]
        assert isinstance(original_fields, dict)
        assert isinstance(replayed_fields, dict)
        assert set(original_fields) == set(OPERATIONAL_FIELDS)
        assert set(replayed_fields) == set(OPERATIONAL_FIELDS)
        for field in OPERATIONAL_FIELDS:
            value = original_fields[field]
            assert value
            if isinstance(value, str):
                assert value.strip()
            elif isinstance(value, list):
                assert all(item for item in value)
        assert replayed_fields == original_fields


def test_replay_consistency_and_operational_drift_are_mathematically_derived() -> None:
    for run in run_agent_trace_replay():
        original_fields = run.original_state["operational_fields"]
        replayed_fields = run.replayed_state["operational_fields"]
        assert isinstance(original_fields, dict)
        assert isinstance(replayed_fields, dict)

        survived = sum(1 for field in OPERATIONAL_FIELDS if original_fields[field] == replayed_fields[field])
        total = len(OPERATIONAL_FIELDS)
        lost = total - survived
        assert run.artifact_row["replay_consistency"] == normalize_float(survived / total)
        assert run.artifact_row["operational_drift_rate"] == normalize_float(lost / total)


def test_agent_trace_replay_ordering_is_deterministic() -> None:
    artifact = build_agent_trace_replay_artifact()
    assert [row["trace"] for row in artifact["traces"]] == EXPECTED_TRACE_ORDER


def test_repeated_detailed_runs_are_reproducible() -> None:
    first_runs = run_agent_trace_replay()
    second_runs = run_agent_trace_replay()
    assert [run.artifact_row for run in first_runs] == [run.artifact_row for run in second_runs]
    assert [run.original_state for run in first_runs] == [run.original_state for run in second_runs]
    assert [run.compact_representation for run in first_runs] == [run.compact_representation for run in second_runs]
    assert [run.replayed_state for run in first_runs] == [run.replayed_state for run in second_runs]
