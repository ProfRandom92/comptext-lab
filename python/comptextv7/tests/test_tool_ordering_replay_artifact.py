from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_tool_ordering_replay_artifact import generate_tool_ordering_replay_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "tool_ordering_replay_results.json"
MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
ALLOWED_FAILURE_LABELS = {
    "INVARIANT_VIOLATION",
    "CAUSAL_DEPENDENCY_LOSS",
    "RECOVERY_PATH_INVALID",
    "POLICY_ORDER_BROKEN",
    "CAPABILITY_BOUNDARY_LOSS",
    "UNAUTHORIZED_CAPABILITY_PATH",
    "APPROVAL_GATE_LOSS",
    "POLICY_ENFORCEMENT_GAP",
    "DEPENDENCY_CHAIN_BREAK",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_artifact_exists() -> None:
    assert ARTIFACT_PATH.exists()


def test_generator_output_matches_committed_artifact(tmp_path: Path) -> None:
    output = tmp_path / "tool_ordering_replay_results.json"
    generate_tool_ordering_replay_artifact(output)
    assert output.read_text(encoding="utf-8") == ARTIFACT_PATH.read_text(encoding="utf-8")


def test_top_level_schema_is_stable() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    assert list(artifact) == [
        "artifact_id",
        "generated_by",
        "version",
        "evaluation_mode",
        "llm_judges",
        "external_apis",
        "families",
        "global_summary",
    ]


def test_determinism_and_sanitization(tmp_path: Path) -> None:
    a_path = tmp_path / "a.json"
    b_path = tmp_path / "b.json"
    generate_tool_ordering_replay_artifact(a_path)
    generate_tool_ordering_replay_artifact(b_path)

    a_text = a_path.read_text(encoding="utf-8")
    b_text = b_path.read_text(encoding="utf-8")
    assert a_text == b_text

    blob = a_text.lower()
    assert "timestamp" not in blob
    assert "generated_at" not in blob
    assert "environment" not in blob
    assert "hostname" not in blob
    assert "cwd" not in blob
    assert "score" not in blob
    assert "average" not in blob
    assert "/workspace/" not in a_text
    assert str(Path.home()) not in a_text


def test_manifest_alignment() -> None:
    manifest = _load_json(MANIFEST_PATH)
    artifact = _load_json(ARTIFACT_PATH)

    manifest_fixtures = manifest["fixtures"]
    manifest_family_count = len({item["family"] for item in manifest_fixtures})
    manifest_fixture_ids = sorted(item["fixture_id"] for item in manifest_fixtures)

    artifact_fixtures = [fixture for family in artifact["families"] for fixture in family["fixtures"]]
    artifact_fixture_ids = sorted(fixture["fixture_id"] for fixture in artifact_fixtures)

    assert artifact["global_summary"]["family_count"] == manifest_family_count
    assert artifact["global_summary"]["fixture_count"] == len(manifest_fixtures)
    assert artifact_fixture_ids == manifest_fixture_ids


def test_tool_ordering_evidence_behavior() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    fixtures = [fixture for family in artifact["families"] for fixture in family["fixtures"]]

    with_data = [
        fixture
        for fixture in fixtures
        if fixture["tool_ordering"]["original_edge_count"] > 0
        or fixture["tool_ordering"]["replay_edge_count"] > 0
    ]

    if with_data:
        assert artifact["global_summary"]["fixtures_with_tool_ordering_data"] > 0
    else:
        assert artifact["global_summary"]["fixtures_with_tool_ordering_data"] == 0

    drift_count = sum(1 for fixture in fixtures if fixture["tool_ordering"]["drift_detected"])
    assert artifact["global_summary"]["fixtures_with_tool_ordering_drift"] == drift_count

    if drift_count > 0:
        assert any(fixture["tool_ordering"]["drift_detected"] for fixture in fixtures)


def test_label_discipline() -> None:
    manifest = _load_json(MANIFEST_PATH)
    artifact = _load_json(ARTIFACT_PATH)

    expected_by_fixture = {fixture["fixture_id"]: fixture["expected_failure_labels"] for fixture in manifest["fixtures"]}

    for family in artifact["families"]:
        for fixture in family["fixtures"]:
            labels = fixture["expected_failure_labels"]
            assert labels == expected_by_fixture[fixture["fixture_id"]]
            for label in labels:
                assert label in ALLOWED_FAILURE_LABELS


def test_no_runtime_behavior_fields() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    assert artifact["evaluation_mode"] == "deterministic"
    assert artifact["llm_judges"] == "none"
    assert artifact["external_apis"] == "none"
    assert artifact["global_summary"]["deterministic_evaluation"] is True
    assert artifact["global_summary"]["llm_judges"] == "none"
    assert artifact["global_summary"]["external_apis"] == "none"
