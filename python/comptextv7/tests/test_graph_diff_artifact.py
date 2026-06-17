from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_graph_diff_artifact import generate_graph_diff_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "graph_diff_results.json"
MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_artifact_exists() -> None:
    assert ARTIFACT_PATH.exists()


def test_generator_output_matches_committed_artifact(tmp_path: Path) -> None:
    output = tmp_path / "graph_diff_results.json"
    generate_graph_diff_artifact(output)
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


def test_artifact_deterministic_and_sanitized(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    generate_graph_diff_artifact(first)
    generate_graph_diff_artifact(second)

    first_text = first.read_text(encoding="utf-8")
    second_text = second.read_text(encoding="utf-8")
    assert first_text == second_text

    payload = json.loads(first_text)
    text_blob = json.dumps(payload)
    assert "timestamp" not in text_blob.lower()
    assert str(Path.home()) not in text_blob
    assert "/workspace/" not in text_blob


def test_manifest_alignment_and_fixture_ids() -> None:
    manifest = _load_json(MANIFEST_PATH)
    artifact = _load_json(ARTIFACT_PATH)

    manifest_fixtures = manifest["fixtures"]
    manifest_families = {item["family"] for item in manifest_fixtures}
    manifest_ids = [item["fixture_id"] for item in manifest_fixtures]

    artifact_fixtures = [fixture for family in artifact["families"] for fixture in family["fixtures"]]
    artifact_ids = [fixture["fixture_id"] for fixture in artifact_fixtures]

    assert artifact["global_summary"]["family_count"] == len(manifest_families)
    assert artifact["global_summary"]["fixture_count"] == len(manifest_fixtures)
    assert sorted(artifact_ids) == sorted(manifest_ids)


def test_graph_diff_evidence_present_and_baseline_stable() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    fixtures = [fixture for family in artifact["families"] for fixture in family["fixtures"]]

    assert any(
        category["missing_edges"] or category["missing_nodes"]
        for fixture in fixtures
        for category in fixture["edge_categories"].values()
    )

    baseline = [fixture for fixture in fixtures if fixture["degradation_level"] == "baseline"]
    for fixture in baseline:
        for category in fixture["edge_categories"].values():
            assert category["missing_edges"] == []


def test_failure_labels_manifest_scoped() -> None:
    manifest = _load_json(MANIFEST_PATH)
    artifact = _load_json(ARTIFACT_PATH)

    expected_by_fixture = {
        fixture["fixture_id"]: fixture["expected_failure_labels"]
        for fixture in manifest["fixtures"]
    }

    for family in artifact["families"]:
        for fixture in family["fixtures"]:
            assert fixture["expected_failure_labels"] == expected_by_fixture[fixture["fixture_id"]]
