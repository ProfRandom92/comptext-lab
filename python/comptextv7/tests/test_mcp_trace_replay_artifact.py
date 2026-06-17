from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_mcp_trace_replay_artifact import ARTIFACT_ID, FAMILY, generate_mcp_trace_replay_artifact

ARTIFACT_PATH = Path("artifacts/mcp_trace_replay_results.json")
MANIFEST_PATH = Path("fixtures/manifest.json")
EXPECTED_ORDER = [
    "mcp_trace_replay_v1",
    "mcp_trace_replay_mild_v1",
    "mcp_trace_replay_moderate_v1",
    "mcp_trace_replay_degraded_v1",
]


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_fixture_index() -> dict[str, dict[str, object]]:
    manifest = _load_json(MANIFEST_PATH)
    return {entry["fixture_id"]: entry for entry in manifest["fixtures"]}


def test_script_output_matches_committed_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "mcp_trace_replay_results.json"
    generate_mcp_trace_replay_artifact(output_path)

    assert _load_json(output_path) == _load_json(ARTIFACT_PATH)


def test_artifact_has_stable_schema_no_time_or_environment_fields() -> None:
    payload = _load_json(ARTIFACT_PATH)

    assert set(payload.keys()) == {"artifact_id", "generated_by", "version", "family", "fixtures", "summary"}
    assert payload["artifact_id"] == ARTIFACT_ID
    assert payload["family"] == FAMILY


def test_fixture_order_is_deterministic() -> None:
    payload = _load_json(ARTIFACT_PATH)
    fixture_ids = [entry["fixture_id"] for entry in payload["fixtures"]]
    assert fixture_ids == EXPECTED_ORDER


def test_labels_and_admissibility_align_with_manifest_expectations() -> None:
    payload = _load_json(ARTIFACT_PATH)
    manifest_index = _manifest_fixture_index()

    for fixture in payload["fixtures"]:
        fixture_id = fixture["fixture_id"]
        expected = manifest_index[fixture_id]
        assert fixture["expected_admissible"] == expected["expected_admissible"]
        assert fixture["failure_labels"] == expected["expected_failure_labels"]


def test_baseline_and_severe_admissibility_guarantee() -> None:
    payload = _load_json(ARTIFACT_PATH)
    fixtures = payload["fixtures"]
    summary = payload["summary"]

    assert fixtures[0]["degradation_level"] == "baseline"
    assert fixtures[0]["observed_admissible"] is True
    assert fixtures[-1]["degradation_level"] == "severe"
    assert fixtures[-1]["observed_admissible"] is False
    assert summary["baseline_admissible"] is True
    assert summary["severe_admissible"] is False
