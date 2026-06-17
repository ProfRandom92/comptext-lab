from __future__ import annotations

import filecmp
import json
from collections import Counter
from pathlib import Path

from src.validation.contract_validator import ContractValidator, ValidationResult
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
MATERIALIZED_ROOT = REPO_ROOT / "fixtures" / "mcp_trace_replay_corruptions"
REQUIRED_FILES = ("trace.json", "dependency_graph.json", "state.json")
TARGET_OPERATORS = {
    "DROP_APPROVAL_GATE": "drop_approval_gate",
    "REMOVE_DEPENDENCY_EDGE": "remove_dependency_edge",
    "TRUNCATE_RECOVERY_PATH": "truncate_recovery_path",
    "SWAP_TOOL_ORDER": "swap_tool_order",
    "COLLAPSE_CAPABILITY_BOUNDARY": "collapse_capability_boundary",
    "INSERT_UNVALIDATED_ACTION": "insert_unvalidated_action",
}


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _load_json(path: Path) -> dict[str, object]:
    repo_rel = _repo_relative(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required JSON file is missing: {repo_rel}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {repo_rel}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object at root: {repo_rel}")
    return data


def _as_list(value: object, *, field: str, path: Path) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    raise RuntimeError(f"expected list for '{field}' in {_repo_relative(path)}, got {type(value).__name__}")


def _split_corruption_id(corruption_id: str) -> tuple[str, str]:
    parts = corruption_id.split("::", maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise RuntimeError(f"invalid corruption_id: {corruption_id}")
    return parts[0], parts[1]


def _materialized_entries() -> list[dict[str, object]]:
    manifest = _load_json(MANIFEST_PATH)
    entries = _as_list(manifest.get("corruptions"), field="corruptions", path=MANIFEST_PATH)
    return [entry for entry in entries if isinstance(entry, dict) and entry.get("operator") in TARGET_OPERATORS]


def _has_boundary(state_doc: dict[str, object], source: str, target: str, *, path: Path) -> bool:
    boundaries = _as_list(state_doc.get("capability_boundaries"), field="capability_boundaries", path=path)
    return [source, target] in boundaries


def _has_edge(graph_doc: dict[str, object], source: str, target: str, *, path: Path) -> bool:
    edges = _as_list(graph_doc.get("edges"), field="edges", path=path)
    for edge in edges:
        if not isinstance(edge, dict):
            raise RuntimeError(f"expected object edge in {_repo_relative(path)}")
        if edge.get("source") == source and edge.get("target") == target:
            return True
    return False


def _event_actions(trace_doc: dict[str, object], *, path: Path) -> list[str]:
    events = _as_list(trace_doc.get("events"), field="events", path=path)
    actions: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            raise RuntimeError(f"expected object event in {_repo_relative(path)}")
        action = event.get("action")
        if not isinstance(action, str):
            raise RuntimeError(f"expected event action string in {_repo_relative(path)}")
        actions.append(action)
    return actions


def _action_index(actions: list[str], action: str, *, path: Path) -> int:
    try:
        return actions.index(action)
    except ValueError as exc:
        raise RuntimeError(f"missing action {action!r} in {_repo_relative(path)}") from exc


def _terminal_action(trace_doc: dict[str, object], *, path: Path) -> str | None:
    actions = _event_actions(trace_doc, path=path)
    if not actions:
        return None
    return actions[-1]


ADAPTER_GAP_CORRUPTIONS: set[str] = set()


def _failed_labels(results: list[ValidationResult]) -> set[str]:
    return {result.failure_label for result in results if not result.passed and result.failure_label is not None}


def test_materialized_manifest_identity_and_required_files() -> None:
    entries = _materialized_entries()
    assert entries, "no target operator entries found in manifest"
    expected_entries = len(TARGET_OPERATORS) * 3
    assert len(entries) == expected_entries

    for entry in entries:
        corruption_id = entry["corruption_id"]
        source_fixture = entry["source_fixture"]
        operator = entry["operator"]
        expected_label = entry["expected_failure_label"]

        source_slug, operator_slug = _split_corruption_id(corruption_id)
        assert source_slug == Path(source_fixture).name
        assert operator_slug == TARGET_OPERATORS[operator]

        source_original = REPO_ROOT / source_fixture / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug
        assert source_original.exists(), f"missing source fixture: {_repo_relative(source_original)}"
        assert materialized_dir.exists(), f"missing materialized fixture: {_repo_relative(materialized_dir)}"

        for name in REQUIRED_FILES:
            assert (source_original / name).exists(), f"missing source file: {_repo_relative(source_original / name)}"
            assert (materialized_dir / name).exists(), f"missing materialized file: {_repo_relative(materialized_dir / name)}"

        assert expected_label in FAILURE_TAXONOMY


def test_drop_approval_gate_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "DROP_APPROVAL_GATE":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_state_path = source_original / "state.json"
        materialized_state_path = materialized_dir / "state.json"
        source_state = _load_json(source_state_path)
        materialized_state = _load_json(materialized_state_path)

        assert _has_boundary(source_state, "human_approval", "execute_external_action", path=source_state_path)
        assert not _has_boundary(
            materialized_state,
            "human_approval",
            "execute_external_action",
            path=materialized_state_path,
        )

        assert filecmp.cmp(source_original / "trace.json", materialized_dir / "trace.json", shallow=False)
        assert filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized_dir / "dependency_graph.json",
            shallow=False,
        )


def test_remove_dependency_edge_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "REMOVE_DEPENDENCY_EDGE":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_graph_path = source_original / "dependency_graph.json"
        materialized_graph_path = materialized_dir / "dependency_graph.json"
        source_graph = _load_json(source_graph_path)
        materialized_graph = _load_json(materialized_graph_path)

        assert _has_edge(source_graph, "read_context", "validate_external_action", path=source_graph_path)
        assert not _has_edge(
            materialized_graph,
            "read_context",
            "validate_external_action",
            path=materialized_graph_path,
        )

        assert filecmp.cmp(source_original / "trace.json", materialized_dir / "trace.json", shallow=False)
        assert filecmp.cmp(source_original / "state.json", materialized_dir / "state.json", shallow=False)


def test_truncate_recovery_path_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "TRUNCATE_RECOVERY_PATH":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_trace_path = source_original / "trace.json"
        materialized_trace_path = materialized_dir / "trace.json"
        source_trace = _load_json(source_trace_path)
        materialized_trace = _load_json(materialized_trace_path)

        assert _terminal_action(source_trace, path=source_trace_path) == "recovery_path_registered"
        assert _terminal_action(materialized_trace, path=materialized_trace_path) != "recovery_path_registered"

        source_events = _as_list(source_trace.get("events"), field="events", path=source_trace_path)
        materialized_events = _as_list(
            materialized_trace.get("events"),
            field="events",
            path=materialized_trace_path,
        )
        assert len(materialized_events) == len(source_events) - 1

        assert filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized_dir / "dependency_graph.json",
            shallow=False,
        )
        assert filecmp.cmp(source_original / "state.json", materialized_dir / "state.json", shallow=False)


def test_swap_tool_order_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "SWAP_TOOL_ORDER":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_trace_path = source_original / "trace.json"
        materialized_trace_path = materialized_dir / "trace.json"
        source_actions = _event_actions(_load_json(source_trace_path), path=source_trace_path)
        materialized_actions = _event_actions(_load_json(materialized_trace_path), path=materialized_trace_path)

        assert _action_index(source_actions, "tool_schema_validated", path=source_trace_path) < _action_index(
            source_actions,
            "read_context",
            path=source_trace_path,
        )
        assert _action_index(materialized_actions, "read_context", path=materialized_trace_path) < _action_index(
            materialized_actions,
            "tool_schema_validated",
            path=materialized_trace_path,
        )
        assert len(materialized_actions) == len(source_actions)
        assert Counter(materialized_actions) == Counter(source_actions)

        assert filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized_dir / "dependency_graph.json",
            shallow=False,
        )
        assert filecmp.cmp(source_original / "state.json", materialized_dir / "state.json", shallow=False)


def test_collapse_capability_boundary_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "COLLAPSE_CAPABILITY_BOUNDARY":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_state_path = source_original / "state.json"
        materialized_state_path = materialized_dir / "state.json"
        source_state = _load_json(source_state_path)
        materialized_state = _load_json(materialized_state_path)

        assert _has_boundary(
            source_state,
            "capability_scope_checked",
            "validate_external_action",
            path=source_state_path,
        )
        assert not _has_boundary(
            materialized_state,
            "capability_scope_checked",
            "validate_external_action",
            path=materialized_state_path,
        )

        assert filecmp.cmp(source_original / "trace.json", materialized_dir / "trace.json", shallow=False)
        assert filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized_dir / "dependency_graph.json",
            shallow=False,
        )


def test_insert_unvalidated_action_structural_violation_and_unchanged_non_targets() -> None:
    for entry in _materialized_entries():
        if entry["operator"] != "INSERT_UNVALIDATED_ACTION":
            continue

        source_slug, operator_slug = _split_corruption_id(entry["corruption_id"])
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        source_trace_path = source_original / "trace.json"
        materialized_trace_path = materialized_dir / "trace.json"
        source_actions = _event_actions(_load_json(source_trace_path), path=source_trace_path)
        materialized_actions = _event_actions(_load_json(materialized_trace_path), path=materialized_trace_path)

        assert _action_index(source_actions, "validate_external_action", path=source_trace_path) < _action_index(
            source_actions,
            "execute_external_action",
            path=source_trace_path,
        )
        assert _action_index(
            materialized_actions,
            "execute_external_action",
            path=materialized_trace_path,
        ) < _action_index(
            materialized_actions,
            "validate_external_action",
            path=materialized_trace_path,
        )
        assert len(materialized_actions) == len(source_actions)
        assert Counter(materialized_actions) == Counter(source_actions)

        assert filecmp.cmp(
            source_original / "dependency_graph.json",
            materialized_dir / "dependency_graph.json",
            shallow=False,
        )
        assert filecmp.cmp(source_original / "state.json", materialized_dir / "state.json", shallow=False)


def test_materialized_corruptions_map_into_contract_validator_with_expected_failure_labels() -> None:
    validator = ContractValidator()
    entries = _materialized_entries()
    all_corruption_ids = {str(entry["corruption_id"]) for entry in entries}

    native_contract_covered_corruptions = all_corruption_ids - ADAPTER_GAP_CORRUPTIONS
    assert native_contract_covered_corruptions == all_corruption_ids

    for entry in entries:
        corruption_id = str(entry["corruption_id"])
        source_slug, operator_slug = _split_corruption_id(corruption_id)
        source_original = REPO_ROOT / entry["source_fixture"] / "original"
        materialized_dir = MATERIALIZED_ROOT / source_slug / operator_slug

        original = {
            **_load_json(source_original / "trace.json"),
            **_load_json(source_original / "state.json"),
            "dependency_graph": _load_json(source_original / "dependency_graph.json"),
        }
        reconstructed = {
            **_load_json(materialized_dir / "trace.json"),
            **_load_json(materialized_dir / "state.json"),
            "dependency_graph": _load_json(materialized_dir / "dependency_graph.json"),
        }

        contracts_dir = source_original / "contracts"
        contracts = [_load_json(path) for path in sorted(contracts_dir.glob("*.json"))]
        assert contracts, f"missing contracts for source fixture: {_repo_relative(contracts_dir)}"
        assert materialized_dir.exists(), f"missing materialized fixture: {_repo_relative(materialized_dir)}"

        results = validator.validate_contracts(
            original=original,
            reconstructed=reconstructed,
            contracts=contracts,
        )
        expected_label = entry["expected_failure_label"]
        failed_labels = _failed_labels(results)

        assert corruption_id not in ADAPTER_GAP_CORRUPTIONS
        assert expected_label in failed_labels, (
            f"native-covered corruption missing expected label emission: {corruption_id}; "
            f"expected {expected_label!r}; observed {sorted(failed_labels)}"
        )
