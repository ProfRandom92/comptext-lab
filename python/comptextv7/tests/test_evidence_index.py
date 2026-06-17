from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_evidence_index import generate_evidence_index

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "evidence_index.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_artifact_exists() -> None:
    assert ARTIFACT_PATH.exists()


def test_generator_output_matches_committed_artifact(tmp_path: Path) -> None:
    output = tmp_path / "evidence_index.json"
    generate_evidence_index(output)
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
        "artifacts",
        "global_summary",
    ]


def test_determinism_and_sanitization(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    generate_evidence_index(first)
    generate_evidence_index(second)

    first_text = first.read_text(encoding="utf-8")
    second_text = second.read_text(encoding="utf-8")
    assert first_text == second_text

    blob = first_text.lower()
    assert "timestamp" not in blob
    assert "generated_at" not in blob
    assert "environment" not in blob
    assert "user" not in blob
    assert "hostname" not in blob
    assert "hash" not in blob
    assert "digest" not in blob
    assert "/workspace/" not in first_text
    assert str(Path.home()) not in first_text


def test_entries_are_sorted_and_files_exist() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    paths = [entry["path"] for entry in artifact["artifacts"]]
    assert paths == sorted(paths)
    for path in paths:
        assert (REPO_ROOT / path).exists()


def test_json_artifacts_parse_and_list_top_level_keys() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    for entry in artifact["artifacts"]:
        if entry["format"] != "json":
            continue
        payload = _load_json(REPO_ROOT / entry["path"])
        assert entry["top_level_keys"] == sorted(payload.keys())
        assert entry["deterministic_evaluation"] is True
        assert entry["llm_judges"] == "none"
        assert entry["external_apis"] == "none"


def test_svg_artifacts_are_visualization_only() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    svg_entries = [entry for entry in artifact["artifacts"] if entry["format"] == "svg"]
    for entry in svg_entries:
        assert entry["visualization_only"] is True
        assert entry["evidence_bearing"] is False


def test_global_summary_counts_match_entries() -> None:
    artifact = _load_json(ARTIFACT_PATH)
    entries = artifact["artifacts"]
    summary = artifact["global_summary"]

    assert summary["artifact_count"] == len(entries)
    assert summary["json_artifact_count"] == sum(1 for item in entries if item["format"] == "json")
    assert summary["svg_artifact_count"] == sum(1 for item in entries if item["format"] == "svg")
    assert summary["evidence_bearing_count"] == sum(1 for item in entries if item["evidence_bearing"])
    assert summary["visualization_only_count"] == sum(1 for item in entries if item["visualization_only"])
    assert summary["deterministic_artifact_count"] == sum(1 for item in entries if item["deterministic_evaluation"])
    assert summary["llm_free_artifact_count"] == sum(1 for item in entries if item["llm_judges"] == "none")
    assert summary["external_api_free_artifact_count"] == sum(1 for item in entries if item["external_apis"] == "none")
