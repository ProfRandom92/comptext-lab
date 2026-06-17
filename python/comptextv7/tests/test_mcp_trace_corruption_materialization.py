from __future__ import annotations

import filecmp
import json
from pathlib import Path

from scripts.materialize_mcp_trace_corruptions import (
    OUTPUT_ROOT,
    SELECTED_OPERATORS,
    materialize_mcp_trace_corruptions,
)
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
FORBIDDEN_TOKENS = ('"generated_at"', '"timestamp"', '"host"', '"user"', '"env"', "/workspace/")
REQUIRED_FILES = ("trace.json", "dependency_graph.json", "state.json")


def _load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _materialized_entries() -> list[dict[str, object]]:
    manifest = _load_manifest()
    return [
        entry
        for entry in manifest["corruptions"]
        if entry["operator"] in SELECTED_OPERATORS
    ]


def _split_corruption_id(corruption_id: str) -> tuple[str, str]:
    parts = corruption_id.split("::", maxsplit=1)
    assert len(parts) == 2
    assert parts[0]
    assert parts[1]
    return parts[0], parts[1]


def test_materialized_corruption_directories_exist() -> None:
    assert OUTPUT_ROOT.exists()
    for entry in _materialized_entries():
        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        assert (OUTPUT_ROOT / source_slug / operator_slug).exists()


def test_only_selected_operators_are_materialized() -> None:
    expected = {
        _split_corruption_id(entry["corruption_id"])
        for entry in _materialized_entries()
    }
    found: set[tuple[str, str]] = set()

    for source_dir in OUTPUT_ROOT.iterdir():
        if not source_dir.is_dir():
            continue
        for operator_dir in source_dir.iterdir():
            if not operator_dir.is_dir():
                continue
            found.add((source_dir.name, operator_dir.name))

    assert found == expected


def test_materialized_fixtures_preserve_file_shape() -> None:
    for entry in _materialized_entries():
        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        fixture_dir = OUTPUT_ROOT / source_slug / operator_slug
        assert sorted(p.name for p in fixture_dir.iterdir() if p.is_file()) == sorted(REQUIRED_FILES)


def test_source_fixtures_exist_for_materialized_entries() -> None:
    for entry in _materialized_entries():
        source_fixture = entry["source_fixture"]
        source_original = REPO_ROOT / source_fixture / "original"
        assert source_original.exists()
        for name in REQUIRED_FILES:
            assert (source_original / name).exists()


def test_materialized_entries_have_consistent_manifest_identity() -> None:
    for entry in _materialized_entries():
        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        assert source_slug == Path(entry["source_fixture"]).name
        assert operator_slug in {
            "drop_approval_gate",
            "remove_dependency_edge",
            "truncate_recovery_path",
            "swap_tool_order",
            "collapse_capability_boundary",
            "insert_unvalidated_action",
        }


def test_selected_operator_set_is_exact() -> None:
    assert SELECTED_OPERATORS == (
        "DROP_APPROVAL_GATE",
        "REMOVE_DEPENDENCY_EDGE",
        "TRUNCATE_RECOVERY_PATH",
        "SWAP_TOOL_ORDER",
        "COLLAPSE_CAPABILITY_BOUNDARY",
        "INSERT_UNVALIDATED_ACTION",
    )


def test_only_intended_file_surface_changes_per_operator() -> None:
    for entry in _materialized_entries():
        operator = entry["operator"]
        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized = OUTPUT_ROOT / source_slug / operator_slug

        trace_same = filecmp.cmp(source_original / "trace.json", materialized / "trace.json", shallow=False)
        graph_same = filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized / "dependency_graph.json",
            shallow=False,
        )
        state_same = filecmp.cmp(source_original / "state.json", materialized / "state.json", shallow=False)

        if operator == "DROP_APPROVAL_GATE":
            assert not state_same
            assert trace_same
            assert graph_same
        elif operator == "REMOVE_DEPENDENCY_EDGE":
            assert not graph_same
            assert trace_same
            assert state_same
        elif operator == "TRUNCATE_RECOVERY_PATH":
            assert not trace_same
            assert graph_same
            assert state_same
        elif operator == "SWAP_TOOL_ORDER":
            assert not trace_same
            assert graph_same
            assert state_same
        elif operator == "COLLAPSE_CAPABILITY_BOUNDARY":
            assert trace_same
            assert graph_same
            assert not state_same
        elif operator == "INSERT_UNVALIDATED_ACTION":
            assert not trace_same
            assert graph_same
            assert state_same


def test_insert_unvalidated_action_reorders_existing_trace_events_only() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "INSERT_UNVALIDATED_ACTION":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized = OUTPUT_ROOT / source_slug / operator_slug

        source_trace = json.loads((source_original / "trace.json").read_text(encoding="utf-8"))
        materialized_trace = json.loads((materialized / "trace.json").read_text(encoding="utf-8"))

        source_events = source_trace.get("events") or []
        materialized_events = materialized_trace.get("events") or []
        assert isinstance(source_events, list)
        assert isinstance(materialized_events, list)
        assert len(source_events) == len(materialized_events)

        source_validate_index = next(
            idx for idx, event in enumerate(source_events) if isinstance(event, dict) and event.get("action") == "validate_external_action"
        )
        source_execute_index = next(
            idx for idx, event in enumerate(source_events) if isinstance(event, dict) and event.get("action") == "execute_external_action"
        )
        assert source_validate_index < source_execute_index

        materialized_validate_index = next(
            idx
            for idx, event in enumerate(materialized_events)
            if isinstance(event, dict) and event.get("action") == "validate_external_action"
        )
        materialized_execute_index = next(
            idx
            for idx, event in enumerate(materialized_events)
            if isinstance(event, dict) and event.get("action") == "execute_external_action"
        )
        assert materialized_execute_index < materialized_validate_index


def test_materialized_fixtures_have_no_time_or_environment_fields() -> None:
    for path in OUTPUT_ROOT.glob("**/*.json"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_TOKENS:
            assert token not in text


def test_materialization_reproduces_committed_output(tmp_path: Path) -> None:
    generated_root = tmp_path / "generated_corruptions"
    materialize_mcp_trace_corruptions(generated_root)

    expected_files = sorted(p.relative_to(OUTPUT_ROOT) for p in OUTPUT_ROOT.glob("**/*.json"))
    generated_files = sorted(p.relative_to(generated_root) for p in generated_root.glob("**/*.json"))
    assert generated_files == expected_files

    for relative_path in expected_files:
        expected_text = (OUTPUT_ROOT / relative_path).read_text(encoding="utf-8")
        generated_text = (generated_root / relative_path).read_text(encoding="utf-8")
        assert generated_text == expected_text


def test_materialized_entries_match_manifest_operators_and_labels() -> None:
    registered_labels = set(FAILURE_TAXONOMY)
    for entry in _materialized_entries():
        assert entry["operator"] in SELECTED_OPERATORS
        assert entry["expected_failure_label"] in registered_labels
