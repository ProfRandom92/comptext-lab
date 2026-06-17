"""Materialize deterministic MCP trace corruption fixtures from committed manifest."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
OUTPUT_ROOT = REPO_ROOT / "fixtures" / "mcp_trace_replay_corruptions"
REQUIRED_FIXTURE_FILES: tuple[str, ...] = ("trace.json", "dependency_graph.json", "state.json")
SELECTED_OPERATORS: tuple[str, ...] = (
    "DROP_APPROVAL_GATE",
    "REMOVE_DEPENDENCY_EDGE",
    "TRUNCATE_RECOVERY_PATH",
    "SWAP_TOOL_ORDER",
    "COLLAPSE_CAPABILITY_BOUNDARY",
    "INSERT_UNVALIDATED_ACTION",
)


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _source_slug(source_fixture: str) -> str:
    return source_fixture.rstrip("/").rsplit("/", maxsplit=1)[-1]


def _split_corruption_id(corruption_id: str) -> tuple[str, str]:
    parts = corruption_id.split("::", maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise RuntimeError(f"Invalid corruption_id format: {corruption_id}")
    return parts[0], parts[1]


def _as_list(value: Any, *, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError(f"Expected list field {field}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required JSON file is missing: {_repo_relative(path)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {_repo_relative(path)}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {_repo_relative(path)}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n", encoding="utf-8")


def _materialize_drop_approval_gate(state: dict[str, Any]) -> dict[str, Any]:
    boundaries = _as_list(state.get("capability_boundaries"), field="state.capability_boundaries")

    removed = False
    mutated_boundaries: list[Any] = []
    for boundary in boundaries:
        if boundary == ["human_approval", "execute_external_action"] and not removed:
            removed = True
            continue
        mutated_boundaries.append(boundary)

    if not removed:
        raise RuntimeError("Operator DROP_APPROVAL_GATE not applicable: missing human approval boundary")

    state["capability_boundaries"] = mutated_boundaries
    return state


def _materialize_remove_dependency_edge(graph: dict[str, Any]) -> dict[str, Any]:
    edges = _as_list(graph.get("edges"), field="dependency_graph.edges")

    removed = False
    mutated_edges: list[Any] = []
    for edge in edges:
        if (
            isinstance(edge, dict)
            and edge.get("source") == "read_context"
            and edge.get("target") == "validate_external_action"
            and not removed
        ):
            removed = True
            continue
        mutated_edges.append(edge)

    if not removed:
        raise RuntimeError(
            "Operator REMOVE_DEPENDENCY_EDGE not applicable: missing read_context->validate_external_action edge"
        )

    graph["edges"] = mutated_edges
    return graph


def _materialize_truncate_recovery_path(trace: dict[str, Any]) -> dict[str, Any]:
    events = _as_list(trace.get("events"), field="trace.events")
    if not events:
        raise RuntimeError("Operator TRUNCATE_RECOVERY_PATH not applicable: trace has no events")

    terminal = events[-1]
    if not isinstance(terminal, dict) or terminal.get("action") != "recovery_path_registered":
        raise RuntimeError(
            "Operator TRUNCATE_RECOVERY_PATH not applicable: terminal action is not recovery_path_registered"
        )

    trace["events"] = events[:-1]
    return trace


def _materialize_swap_tool_order(trace: dict[str, Any]) -> dict[str, Any]:
    events = _as_list(trace.get("events"), field="trace.events")
    validated_index: int | None = None
    read_context_index: int | None = None

    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        action = event.get("action")
        if action == "tool_schema_validated" and validated_index is None:
            validated_index = idx
        elif action == "read_context" and read_context_index is None:
            read_context_index = idx

    if validated_index is None or read_context_index is None:
        raise RuntimeError(
            "Operator SWAP_TOOL_ORDER not applicable: missing tool_schema_validated/read_context actions"
        )

    events[validated_index], events[read_context_index] = events[read_context_index], events[validated_index]
    trace["events"] = events
    return trace


def _materialize_collapse_capability_boundary(state: dict[str, Any]) -> dict[str, Any]:
    boundaries = _as_list(state.get("capability_boundaries"), field="state.capability_boundaries")

    removed = False
    mutated_boundaries: list[Any] = []
    for boundary in boundaries:
        if boundary == ["capability_scope_checked", "validate_external_action"] and not removed:
            removed = True
            continue
        mutated_boundaries.append(boundary)

    if not removed:
        raise RuntimeError(
            "Operator COLLAPSE_CAPABILITY_BOUNDARY not applicable: missing capability scope boundary"
        )

    state["capability_boundaries"] = mutated_boundaries
    return state


def _materialize_insert_unvalidated_action(trace: dict[str, Any]) -> dict[str, Any]:
    events = _as_list(trace.get("events"), field="trace.events")

    validate_index: int | None = None
    execute_index: int | None = None
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        action = event.get("action")
        if action == "validate_external_action" and validate_index is None:
            validate_index = idx
        elif action == "execute_external_action" and execute_index is None:
            execute_index = idx

    if validate_index is None or execute_index is None:
        raise RuntimeError(
            "Operator INSERT_UNVALIDATED_ACTION not applicable: missing validate_external_action/execute_external_action actions"
        )
    if validate_index >= execute_index:
        raise RuntimeError(
            "Operator INSERT_UNVALIDATED_ACTION not applicable: validate_external_action must occur before execute_external_action"
        )

    execute_event = events.pop(execute_index)
    events.insert(validate_index, execute_event)
    trace["events"] = events
    return trace


def materialize_mcp_trace_corruptions(output_root: Path = OUTPUT_ROOT) -> Path:
    manifest = _load_json(MANIFEST_PATH)
    entries = _as_list(manifest.get("corruptions"), field="manifest.corruptions")

    output_root.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError("Each manifest corruption entry must be an object")

        operator = entry.get("operator")
        if operator not in SELECTED_OPERATORS:
            continue

        source_fixture = entry.get("source_fixture")
        corruption_id = entry.get("corruption_id")
        if not isinstance(source_fixture, str) or not isinstance(corruption_id, str):
            raise RuntimeError("Manifest entry must include string source_fixture and corruption_id")

        source_slug, operator_slug = _split_corruption_id(corruption_id)
        if source_slug != _source_slug(source_fixture):
            raise RuntimeError(
                f"Manifest corruption_id/source_fixture mismatch: {corruption_id} vs {source_fixture}"
            )

        source_original = REPO_ROOT / source_fixture / "original"
        missing = [name for name in REQUIRED_FIXTURE_FILES if not (source_original / name).exists()]
        if missing:
            raise RuntimeError(
                f"Incomplete MCP fixture {_repo_relative(source_original)}; missing: {', '.join(missing)}"
            )

        target_dir = output_root / source_slug / operator_slug
        target_dir.mkdir(parents=True, exist_ok=True)

        for fixture_file in REQUIRED_FIXTURE_FILES:
            shutil.copyfile(source_original / fixture_file, target_dir / fixture_file)

        if operator == "DROP_APPROVAL_GATE":
            state = _load_json(target_dir / "state.json")
            _write_json(target_dir / "state.json", _materialize_drop_approval_gate(state))
        elif operator == "REMOVE_DEPENDENCY_EDGE":
            graph = _load_json(target_dir / "dependency_graph.json")
            _write_json(target_dir / "dependency_graph.json", _materialize_remove_dependency_edge(graph))
        elif operator == "TRUNCATE_RECOVERY_PATH":
            trace = _load_json(target_dir / "trace.json")
            _write_json(target_dir / "trace.json", _materialize_truncate_recovery_path(trace))
        elif operator == "SWAP_TOOL_ORDER":
            trace = _load_json(target_dir / "trace.json")
            _write_json(target_dir / "trace.json", _materialize_swap_tool_order(trace))
        elif operator == "COLLAPSE_CAPABILITY_BOUNDARY":
            state = _load_json(target_dir / "state.json")
            _write_json(target_dir / "state.json", _materialize_collapse_capability_boundary(state))
        elif operator == "INSERT_UNVALIDATED_ACTION":
            trace = _load_json(target_dir / "trace.json")
            _write_json(target_dir / "trace.json", _materialize_insert_unvalidated_action(trace))

    return output_root


if __name__ == "__main__":
    path = materialize_mcp_trace_corruptions()
    print(path.relative_to(REPO_ROOT).as_posix())
