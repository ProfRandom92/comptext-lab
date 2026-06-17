"""Generate deterministic MCP trace corruption manifest from checked-in fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = REPO_ROOT / "fixtures"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
REQUIRED_FIXTURE_FILES: tuple[str, ...] = ("trace.json", "dependency_graph.json", "state.json")

OPERATORS: tuple[str, ...] = (
    "DROP_APPROVAL_GATE",
    "SWAP_TOOL_ORDER",
    "TRUNCATE_RECOVERY_PATH",
    "REMOVE_DEPENDENCY_EDGE",
    "INSERT_UNVALIDATED_ACTION",
    "COLLAPSE_CAPABILITY_BOUNDARY",
)

OPERATOR_EXPECTATIONS: dict[str, dict[str, str]] = {
    "DROP_APPROVAL_GATE": {
        "expected_failure_label": "APPROVAL_GATE_LOSS",
        "expected_contract_violation": "validation_before_unsafe_action",
        "notes": "Remove explicit human approval gate from state capability boundaries.",
    },
    "SWAP_TOOL_ORDER": {
        "expected_failure_label": "TOOL_ORDER_VIOLATION",
        "expected_contract_violation": "tool_call_order_preserved",
        "notes": "Swap consecutive tool/validation steps in trace to violate deterministic order.",
    },
    "TRUNCATE_RECOVERY_PATH": {
        "expected_failure_label": "RECOVERY_PATH_INVALID",
        "expected_contract_violation": "recovery_path_available",
        "notes": "Drop the terminal recovery event from trace path.",
    },
    "REMOVE_DEPENDENCY_EDGE": {
        "expected_failure_label": "DEPENDENCY_CHAIN_BREAK",
        "expected_contract_violation": "dependency_chain_preserved",
        "notes": "Remove a required prerequisite edge in dependency graph.",
    },
    "INSERT_UNVALIDATED_ACTION": {
        "expected_failure_label": "POLICY_ENFORCEMENT_GAP",
        "expected_contract_violation": "validation_before_unsafe_action",
        "notes": "Insert execute action before validation step in trace ordering.",
    },
    "COLLAPSE_CAPABILITY_BOUNDARY": {
        "expected_failure_label": "CAPABILITY_BOUNDARY_LOSS",
        "expected_contract_violation": "capability_boundary_respected",
        "notes": "Collapse state capability boundary by removing enforcement link.",
    },
}


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


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


def _as_list(value: Any, *, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError(f"Expected list field: {field}")
    return value


def _mcp_fixtures() -> list[Path]:
    candidates = sorted(FIXTURES_ROOT.glob("mcp_trace_replay_*_v1/original"))

    for path in candidates:
        missing = [name for name in REQUIRED_FIXTURE_FILES if not (path / name).exists()]
        if missing:
            raise RuntimeError(
                f"Incomplete MCP fixture {_repo_relative(path)}; missing: {', '.join(missing)}"
            )

    return candidates


def _trace_actions(trace: dict[str, Any]) -> list[str]:
    events = _as_list(trace.get("events"), field="trace.events")
    return [str(event.get("action", "")) for event in events if isinstance(event, dict)]


def _supports_operator(operator: str, trace: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]) -> bool:
    actions = _trace_actions(trace)
    edges = _as_list(graph.get("edges"), field="dependency_graph.edges")
    boundaries = _as_list(state.get("capability_boundaries"), field="state.capability_boundaries")

    if operator == "DROP_APPROVAL_GATE":
        return ["human_approval", "execute_external_action"] in boundaries
    if operator == "SWAP_TOOL_ORDER":
        return "tool_schema_validated" in actions and "read_context" in actions
    if operator == "TRUNCATE_RECOVERY_PATH":
        return "recovery_path_registered" in actions
    if operator == "REMOVE_DEPENDENCY_EDGE":
        return any(
            isinstance(edge, dict)
            and edge.get("source") == "read_context"
            and edge.get("target") == "validate_external_action"
            for edge in edges
        )
    if operator == "INSERT_UNVALIDATED_ACTION":
        return "validate_external_action" in actions and "execute_external_action" in actions
    if operator == "COLLAPSE_CAPABILITY_BOUNDARY":
        return ["capability_scope_checked", "validate_external_action"] in boundaries
    return False


def generate_mcp_trace_corruption_manifest(output_path: Path = OUTPUT_PATH) -> Path:
    entries: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    fixtures = _mcp_fixtures()

    for original_dir in fixtures:
        fixture_root = original_dir.parent
        source_fixture = _repo_relative(fixture_root)
        trace = _load_json(original_dir / "trace.json")
        graph = _load_json(original_dir / "dependency_graph.json")
        state = _load_json(original_dir / "state.json")

        for operator in OPERATORS:
            if not _supports_operator(operator, trace, graph, state):
                skipped.append({"source_fixture": source_fixture, "operator": operator})
                continue

            expected = OPERATOR_EXPECTATIONS[operator]
            entries.append(
                {
                    "corruption_id": f"{fixture_root.name}::{operator.lower()}",
                    "source_fixture": source_fixture,
                    "operator": operator,
                    "expected_failure_label": expected["expected_failure_label"],
                    "expected_contract_violation": expected["expected_contract_violation"],
                    "deterministic": True,
                    "notes": expected["notes"],
                }
            )

    entries.sort(key=lambda item: (item["source_fixture"], item["operator"], item["corruption_id"]))
    skipped.sort(key=lambda item: (item["source_fixture"], item["operator"]))

    payload = {
        "manifest_id": "mcp_trace_corruption_manifest_v1",
        "version": "1.0",
        "allowed_operators": list(OPERATORS),
        "corruptions": entries,
        "summary": {
            "fixture_count": len(fixtures),
            "corruption_count": len(entries),
            "skipped_operator_count": len(skipped),
            "skipped_operators": skipped,
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    path = generate_mcp_trace_corruption_manifest()
    print(path.relative_to(REPO_ROOT).as_posix())
