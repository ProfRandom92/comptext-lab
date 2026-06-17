from __future__ import annotations

import json
import math

from tests.utils.paper_replay_runner import (
    BENCHMARK_NAME,
    OPERATIONAL_FIELDS,
    PAPER_SPECS,
    artifact_json,
    build_paper_replay_artifact,
    canonical_json,
    field_survived,
    normalize_float,
    run_paper_replay,
    stable_json_dump,
)

EXPECTED_PAPER_ORDER = [str(spec["paper"]) for spec in PAPER_SPECS]
PUBLIC_ROW_FIELDS = {
    "paper",
    "entity_retention_rate",
    "evidence_survival_rate",
    "evidence_survived",
    "evidence_total",
    "failure_labels",
    "has_evidence",
    "high_critical_evidence_survival_rate",
    "section_survival_rate",
    "limitation_survival_rate",
    "metric_survival_rate",
    "compression_ratio",
    "replay_consistency",
    "original_token_count",
    "compact_token_count",
    "replay_token_count",
}
AGGREGATE_FIELDS = {
    "avg_entity_retention_rate",
    "avg_evidence_survival_rate",
    "avg_high_critical_evidence_survival_rate",
    "failure_labels",
    "avg_metric_survival_rate",
    "avg_limitation_survival_rate",
    "avg_section_survival_rate",
    "avg_replay_consistency",
    "avg_compression_ratio",
    "paper_count",
}
NORMALIZED_RATE_FIELDS = (
    "entity_retention_rate",
    "evidence_survival_rate",
    "high_critical_evidence_survival_rate",
    "section_survival_rate",
    "limitation_survival_rate",
    "metric_survival_rate",
    "replay_consistency",
)
AGGREGATE_RATE_FIELDS = (
    "avg_entity_retention_rate",
    "avg_evidence_survival_rate",
    "avg_high_critical_evidence_survival_rate",
    "avg_metric_survival_rate",
    "avg_limitation_survival_rate",
    "avg_section_survival_rate",
    "avg_replay_consistency",
)


def _decimal_places(value: float) -> int:
    text = repr(value)
    if "e" in text.lower() or "." not in text:
        return 0
    return len(text.split(".", maxsplit=1)[1])


def test_paper_replay_outputs_are_deterministic_across_repeated_runs() -> None:
    first = build_paper_replay_artifact()
    second = build_paper_replay_artifact()
    assert first == second
    assert canonical_json(first) == canonical_json(second)


def test_paper_replay_artifact_schema_is_valid() -> None:
    artifact = build_paper_replay_artifact()
    assert set(artifact) == {"benchmark", "aggregate", "papers"}
    assert artifact["benchmark"] == BENCHMARK_NAME
    assert isinstance(artifact["papers"], list)
    assert len(artifact["papers"]) == 3

    aggregate = artifact["aggregate"]
    assert isinstance(aggregate, dict)
    assert set(aggregate) == AGGREGATE_FIELDS
    assert aggregate["paper_count"] == len(artifact["papers"])
    assert aggregate["paper_count"] > 0

    for row in artifact["papers"]:
        assert set(row) == PUBLIC_ROW_FIELDS
        assert isinstance(row["paper"], str)
        assert "replay_consistency" in row
        for field in NORMALIZED_RATE_FIELDS + ("compression_ratio",):
            assert isinstance(row[field], float)
            assert math.isfinite(row[field])
            assert _decimal_places(row[field]) <= 6
        for field in NORMALIZED_RATE_FIELDS:
            assert 0.0 <= row[field] <= 1.0
        assert row["compression_ratio"] > 1.0
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


def test_paper_replay_aggregate_matches_recomputed_values() -> None:
    artifact = build_paper_replay_artifact()
    papers = artifact["papers"]
    aggregate = artifact["aggregate"]
    assert isinstance(papers, list)
    assert isinstance(aggregate, dict)

    field_pairs = {
        "avg_compression_ratio": "compression_ratio",
        "avg_entity_retention_rate": "entity_retention_rate",
        "avg_evidence_survival_rate": "evidence_survival_rate",
        "avg_high_critical_evidence_survival_rate": "high_critical_evidence_survival_rate",
        "avg_limitation_survival_rate": "limitation_survival_rate",
        "avg_metric_survival_rate": "metric_survival_rate",
        "avg_replay_consistency": "replay_consistency",
        "avg_section_survival_rate": "section_survival_rate",
    }
    for aggregate_field, paper_field in field_pairs.items():
        recomputed = normalize_float(sum(float(row[paper_field]) for row in papers) / len(papers))
        assert aggregate[aggregate_field] == recomputed


def test_paper_replay_serialization_is_stable_pretty_sorted_and_newline_terminated() -> None:
    artifact = build_paper_replay_artifact()
    serialized = stable_json_dump(artifact)
    reparsed = json.loads(serialized)
    assert reparsed == artifact
    assert serialized == artifact_json(artifact)
    assert serialized == json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert serialized.endswith("\n")
    assert serialized.startswith('{\n  "aggregate"')
    assert '\n  "papers": [\n' in serialized


def test_paper_replay_meets_compression_and_retention_ranges() -> None:
    artifact = build_paper_replay_artifact()
    for row in artifact["papers"]:
        assert row["compact_token_count"] < row["original_token_count"]
        assert row["compression_ratio"] >= 1.2
        assert 0.84 <= row["entity_retention_rate"] <= 0.97
        assert 0.70 <= row["limitation_survival_rate"] <= 0.95
        assert 0.75 <= row["metric_survival_rate"] <= 0.95
        assert 0.70 <= row["replay_consistency"] < 1.0


def test_required_entities_are_preserved_while_optional_entities_degrade() -> None:
    for run in run_paper_replay():
        original_fields = run.original_state["operational_fields"]
        replayed_fields = run.replayed_state["operational_fields"]
        assert isinstance(original_fields, dict)
        assert isinstance(replayed_fields, dict)
        assert original_fields["required_entities"] == replayed_fields["required_entities"]
        assert set(replayed_fields["entities"]).issubset(set(original_fields["entities"]))
        assert replayed_fields["entities"] != original_fields["entities"]


def test_operational_fields_are_never_empty() -> None:
    for run in run_paper_replay():
        fields = run.original_state["operational_fields"]
        assert isinstance(fields, dict)
        for field in OPERATIONAL_FIELDS:
            value = fields[field]
            assert value
            if isinstance(value, str):
                assert value.strip()
            elif isinstance(value, list):
                assert all(isinstance(item, str) and item.strip() for item in value)


def test_replay_consistency_is_derived_from_field_survival() -> None:
    for run in run_paper_replay():
        original_fields = run.original_state["operational_fields"]
        replayed_fields = run.replayed_state["operational_fields"]
        assert isinstance(original_fields, dict)
        assert isinstance(replayed_fields, dict)
        survived = sum(
            1
            for field in OPERATIONAL_FIELDS
            if field_survived(field, original_fields[field], replayed_fields[field])
        )
        expected_consistency = normalize_float(survived / len(OPERATIONAL_FIELDS))
        assert run.artifact_row["replay_consistency"] == expected_consistency


def test_paper_replay_ordering_is_deterministic() -> None:
    artifact = build_paper_replay_artifact()
    assert [row["paper"] for row in artifact["papers"]] == EXPECTED_PAPER_ORDER


def test_repeated_detailed_runs_are_reproducible() -> None:
    first_runs = run_paper_replay()
    second_runs = run_paper_replay()
    assert [run.artifact_row for run in first_runs] == [run.artifact_row for run in second_runs]
    assert [run.original_state for run in first_runs] == [run.original_state for run in second_runs]
    assert [run.compact_representation for run in first_runs] == [run.compact_representation for run in second_runs]
    assert [run.replayed_state for run in first_runs] == [run.replayed_state for run in second_runs]
