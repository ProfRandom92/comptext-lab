from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_mcp_trace_corruptions import (
    OPERATORS,
    generate_mcp_trace_corruption_manifest,
)
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
FORBIDDEN_TOKENS = (
    "generated_at",
    "timestamp",
    "host",
    "user",
    "env",
)


def _load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_exists() -> None:
    assert MANIFEST_PATH.exists()


def test_manifest_top_level_schema_is_stable() -> None:
    manifest = _load_manifest()
    assert list(manifest) == ["manifest_id", "version", "allowed_operators", "corruptions", "summary"]
    assert manifest["manifest_id"] == "mcp_trace_corruption_manifest_v1"
    assert manifest["version"] == "1.0"
    assert manifest["allowed_operators"] == list(OPERATORS)


def test_entries_are_deterministically_sorted_and_ids_unique() -> None:
    manifest = _load_manifest()
    corruptions = manifest["corruptions"]
    assert isinstance(corruptions, list)
    sort_keys = [
        (entry["source_fixture"], entry["operator"], entry["corruption_id"])
        for entry in corruptions
    ]
    assert sort_keys == sorted(sort_keys)

    ids = [entry["corruption_id"] for entry in corruptions]
    assert len(ids) == len(set(ids))


def test_entries_use_allowed_operators_and_registered_labels() -> None:
    manifest = _load_manifest()
    allowed_ops = set(OPERATORS)
    registered_labels = set(FAILURE_TAXONOMY)

    for entry in manifest["corruptions"]:
        assert entry["operator"] in allowed_ops
        assert entry["expected_failure_label"] in registered_labels
        assert entry["deterministic"] is True


def test_source_fixtures_exist_and_paths_are_relative() -> None:
    manifest = _load_manifest()

    for entry in manifest["corruptions"]:
        source_fixture = entry["source_fixture"]
        source_path = REPO_ROOT / source_fixture
        assert source_path.exists()
        assert not Path(source_fixture).is_absolute()


def test_manifest_summary_matches_actual_entries() -> None:
    manifest = _load_manifest()
    corruptions = manifest["corruptions"]
    summary = manifest["summary"]
    assert isinstance(corruptions, list)
    assert isinstance(summary, dict)

    assert summary["corruption_count"] == len(corruptions)
    assert summary["fixture_count"] == len(
        {entry["source_fixture"] for entry in corruptions}
    )


def test_manifest_has_no_time_or_environment_fields() -> None:
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    lower_text = manifest_text.lower()

    for token in FORBIDDEN_TOKENS:
        assert f'"{token}":' not in lower_text


def test_generator_reproduces_committed_manifest(tmp_path: Path) -> None:
    generated_path = tmp_path / "manifest.json"
    generate_mcp_trace_corruption_manifest(generated_path)
    assert generated_path.read_text(encoding="utf-8") == MANIFEST_PATH.read_text(encoding="utf-8")
