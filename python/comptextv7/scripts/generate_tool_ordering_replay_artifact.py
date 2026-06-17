"""Generate deterministic tool-ordering replay artifact from manifest fixtures."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.comptext_v7.graph import compare_edges, find_order_violations, nodes_from_edges, normalize_edges

MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "tool_ordering_replay_results.json"

ORDERING_KEYS = {
    "tool_calls",
    "tool_call_order",
    "tools",
    "actions",
    "action_sequence",
    "ordered_steps",
    "policy_steps",
}
REQUIRED_BEFORE_KEYS = {
    "required_before",
    "before",
    "must_precede",
    "validation_before_unsafe_action",
}
IDENTIFIER_KEYS = ("id", "name", "tool", "action", "step")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _discover_payload_files(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.glob("*.json") if path.is_file())


def _id_from_obj(item: object) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in IDENTIFIER_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _pair(item: object) -> tuple[str, str] | None:
    if isinstance(item, (list, tuple)) and len(item) == 2 and all(isinstance(v, str) and v for v in item):
        return (item[0], item[1])
    return None


def _edges_from_ordered_list(value: list[object]) -> list[tuple[str, str]]:
    ordered: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            ordered.append(item)
            continue
        obj_id = _id_from_obj(item)
        if obj_id is not None:
            ordered.append(obj_id)
            continue
        return []
    return [(ordered[i], ordered[i + 1]) for i in range(len(ordered) - 1)]


def _edges_from_required_before(value: object) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []

    one_pair = _pair(value)
    if one_pair is not None:
        return [one_pair]

    if isinstance(value, list):
        pair_list = [_pair(item) for item in value]
        if value and all(item is not None for item in pair_list):
            return [item for item in pair_list if item is not None]

    if isinstance(value, dict):
        for left, right in value.items():
            if not isinstance(left, str) or not left:
                continue
            if isinstance(right, str) and right:
                edges.append((left, right))
            elif isinstance(right, list) and all(isinstance(v, str) and v for v in right):
                edges.extend((left, v) for v in right)
    return edges


def _walk(payload: object, edges: list[tuple[str, str]], required_before: list[tuple[str, str]]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in ORDERING_KEYS and isinstance(value, list):
                edges.extend(_edges_from_ordered_list(value))
            if key in REQUIRED_BEFORE_KEYS:
                required_before.extend(_edges_from_required_before(value))
            _walk(value, edges, required_before)
    elif isinstance(payload, list):
        for item in payload:
            _walk(item, edges, required_before)


def _extract_tool_ordering(payloads: list[dict[str, Any]]) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    edges: list[tuple[str, str]] = []
    required_before: list[tuple[str, str]] = []
    for payload in payloads:
        _walk(payload, edges, required_before)
    return normalize_edges(edges), normalize_edges(required_before)


def _extract_sequence(payloads: list[dict[str, Any]]) -> tuple[str, ...]:
    sequence_values: set[str] = set()
    for payload in payloads:
        edges: list[tuple[str, str]] = []
        required: list[tuple[str, str]] = []
        _walk(payload, edges, required)
        for left, right in edges:
            sequence_values.add(left)
            sequence_values.add(right)
    return tuple(sorted(sequence_values))


def generate_tool_ordering_replay_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    manifest = _load_json(MANIFEST_PATH)
    fixtures: list[dict[str, Any]] = manifest["fixtures"]

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in fixtures:
        by_family[str(fixture["family"])].append(fixture)

    families_payload: list[dict[str, Any]] = []
    fixture_count = 0
    fixtures_with_tool_ordering_data = 0
    fixtures_with_tool_ordering_drift = 0
    total_missing_tool_order_edges = 0
    total_added_tool_order_edges = 0
    total_required_before_violations = 0

    for family in sorted(by_family):
        fixture_payloads: list[dict[str, Any]] = []
        for fixture in sorted(by_family[family], key=lambda item: str(item["fixture_id"])):
            fixture_root = REPO_ROOT / str(fixture["path"])
            original_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "original")]
            replay_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "reconstructed")]

            original_edges, original_required = _extract_tool_ordering(original_payloads)
            replay_edges, _ = _extract_tool_ordering(replay_payloads)
            replay_sequence = _extract_sequence(replay_payloads)

            diff = compare_edges(original_edges, replay_edges)
            original_nodes = nodes_from_edges(original_edges) if original_edges else tuple()
            replay_nodes = nodes_from_edges(replay_edges) if replay_edges else tuple()
            missing_nodes = tuple(sorted(set(original_nodes) - set(replay_nodes)))
            added_nodes = tuple(sorted(set(replay_nodes) - set(original_nodes)))
            violations = find_order_violations(replay_sequence, original_required)

            if original_edges or replay_edges or original_required:
                fixtures_with_tool_ordering_data += 1

            drift_detected = bool(diff.missing_edges or diff.added_edges or missing_nodes or added_nodes or violations)
            if drift_detected:
                fixtures_with_tool_ordering_drift += 1

            total_missing_tool_order_edges += len(diff.missing_edges)
            total_added_tool_order_edges += len(diff.added_edges)
            total_required_before_violations += len(violations)

            fixture_payloads.append({
                "fixture_id": fixture["fixture_id"],
                "degradation_level": fixture["degradation_level"],
                "expected_admissible": fixture["expected_admissible"],
                "expected_failure_labels": fixture["expected_failure_labels"],
                "tool_ordering": {
                    "original_edge_count": len(original_edges),
                    "replay_edge_count": len(replay_edges),
                    "missing_edges": [list(edge) for edge in diff.missing_edges],
                    "added_edges": [list(edge) for edge in diff.added_edges],
                    "original_node_count": len(original_nodes),
                    "replay_node_count": len(replay_nodes),
                    "missing_nodes": list(missing_nodes),
                    "added_nodes": list(added_nodes),
                    "required_before_violations": [list(edge) for edge in violations],
                    "drift_detected": drift_detected,
                },
            })
            fixture_count += 1

        families_payload.append({"family": family, "fixtures": fixture_payloads})

    artifact = {
        "artifact_id": "tool_ordering_replay_results_v1",
        "generated_by": "ToolOrderingReplayArtifactGenerator",
        "version": "1.0",
        "evaluation_mode": "deterministic",
        "llm_judges": "none",
        "external_apis": "none",
        "families": families_payload,
        "global_summary": {
            "family_count": len(families_payload),
            "fixture_count": fixture_count,
            "fixtures_with_tool_ordering_data": fixtures_with_tool_ordering_data,
            "fixtures_with_tool_ordering_drift": fixtures_with_tool_ordering_drift,
            "total_missing_tool_order_edges": total_missing_tool_order_edges,
            "total_added_tool_order_edges": total_added_tool_order_edges,
            "total_required_before_violations": total_required_before_violations,
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = generate_tool_ordering_replay_artifact()
    print(path.relative_to(REPO_ROOT).as_posix())
