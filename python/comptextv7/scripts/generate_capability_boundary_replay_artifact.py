"""Generate deterministic capability-boundary replay artifact from manifest fixtures."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.comptext_v7.graph import compare_edges, nodes_from_edges, normalize_edges

MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "capability_boundary_replay_results.json"

SUPPORTED_RELATION_KEYS = (
    "capability_boundaries",
    "capability_boundary",
    "allowed_capabilities",
    "allowed_tools",
    "tool_capabilities",
    "resource_boundaries",
    "permission_scopes",
    "capability_scope",
)
NODE_ONLY_KEYS = {
    "allowed_capabilities",
    "allowed_tools",
    "permission_scopes",
    "capability_scope",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _discover_payload_files(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.glob("*.json") if path.is_file())


def _collect_relation_values(payload: object, relation_key: str) -> list[object]:
    collected: list[object] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == relation_key:
                collected.append(value)
            collected.extend(_collect_relation_values(value, relation_key))
    elif isinstance(payload, list):
        for item in payload:
            collected.extend(_collect_relation_values(item, relation_key))
    return collected


def _edge_pair(item: object) -> tuple[str, str] | None:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        return None
    left, right = item
    if isinstance(left, str) and isinstance(right, str) and left and right:
        return (left, right)
    return None


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if not value:
        return []
    if all(isinstance(item, str) and item for item in value):
        return [item for item in value if isinstance(item, str)]
    return None


def _extract_from_mapping(value: dict[object, object], node_only: bool) -> tuple[list[tuple[str, str]], list[str]]:
    edges: list[tuple[str, str]] = []
    nodes: list[str] = []
    for left, right in value.items():
        if not isinstance(left, str) or not left:
            continue
        if isinstance(right, str) and right:
            if node_only:
                nodes.extend([left, right])
            else:
                edges.append((left, right))
            continue
        right_list = _string_list(right)
        if right_list is None:
            continue
        if node_only:
            nodes.append(left)
            nodes.extend(right_list)
        else:
            edges.extend((left, node) for node in right_list)
    return edges, nodes


def _extract_relation_data(value: object, relation_key: str) -> tuple[list[tuple[str, str]], list[str]]:
    node_only = relation_key in NODE_ONLY_KEYS
    edges: list[tuple[str, str]] = []
    nodes: list[str] = []

    pair = _edge_pair(value)
    if pair is not None and not node_only:
        edges.append(pair)
        return edges, nodes

    if isinstance(value, dict):
        extracted_edges, extracted_nodes = _extract_from_mapping(value, node_only=node_only)
        edges.extend(extracted_edges)
        nodes.extend(extracted_nodes)
        return edges, nodes

    if isinstance(value, list):
        pair_list = [_edge_pair(item) for item in value]
        if value and all(item is not None for item in pair_list) and not node_only:
            edges.extend(item for item in pair_list if item is not None)
            return edges, nodes

        nodes_list = _string_list(value)
        if nodes_list is not None:
            nodes.extend(nodes_list)
            return edges, nodes

    return edges, nodes


def _extract_boundary_graph(payloads: list[dict[str, Any]]) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    edges: list[tuple[str, str]] = []
    nodes: set[str] = set()

    for relation_key in SUPPORTED_RELATION_KEYS:
        for payload in payloads:
            for relation_value in _collect_relation_values(payload, relation_key):
                rel_edges, rel_nodes = _extract_relation_data(relation_value, relation_key)
                edges.extend(rel_edges)
                nodes.update(rel_nodes)

    normalized_edges = normalize_edges(edges)
    nodes.update(nodes_from_edges(normalized_edges))
    return normalized_edges, tuple(sorted(nodes))


def generate_capability_boundary_replay_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    manifest = _load_json(MANIFEST_PATH)
    fixtures: list[dict[str, Any]] = manifest["fixtures"]

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in fixtures:
        by_family[str(fixture["family"])].append(fixture)

    families_payload: list[dict[str, Any]] = []
    fixture_count = 0
    fixtures_with_boundary_data = 0
    fixtures_with_boundary_drift = 0
    total_missing_boundary_edges = 0
    total_added_boundary_edges = 0

    for family in sorted(by_family):
        fixture_payloads: list[dict[str, Any]] = []
        for fixture in sorted(by_family[family], key=lambda item: str(item["fixture_id"])):
            fixture_root = REPO_ROOT / str(fixture["path"])
            original_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "original")]
            replay_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "reconstructed")]

            original_edges, original_nodes = _extract_boundary_graph(original_payloads)
            replay_edges, replay_nodes = _extract_boundary_graph(replay_payloads)
            diff = compare_edges(original_edges, replay_edges)

            missing_nodes = tuple(sorted(set(original_nodes) - set(replay_nodes)))
            added_nodes = tuple(sorted(set(replay_nodes) - set(original_nodes)))

            if original_edges or replay_edges or original_nodes or replay_nodes:
                fixtures_with_boundary_data += 1

            if diff.missing_edges or diff.added_edges or missing_nodes or added_nodes:
                fixtures_with_boundary_drift += 1

            total_missing_boundary_edges += len(diff.missing_edges)
            total_added_boundary_edges += len(diff.added_edges)

            fixture_payloads.append(
                {
                    "fixture_id": fixture["fixture_id"],
                    "degradation_level": fixture["degradation_level"],
                    "expected_admissible": fixture["expected_admissible"],
                    "expected_failure_labels": fixture["expected_failure_labels"],
                    "capability_boundary": {
                        "original_edge_count": len(original_edges),
                        "replay_edge_count": len(replay_edges),
                        "missing_edges": [list(edge) for edge in diff.missing_edges],
                        "added_edges": [list(edge) for edge in diff.added_edges],
                        "original_node_count": len(original_nodes),
                        "replay_node_count": len(replay_nodes),
                        "missing_nodes": list(missing_nodes),
                        "added_nodes": list(added_nodes),
                        "drift_detected": bool(diff.missing_edges or diff.added_edges or missing_nodes or added_nodes),
                    },
                }
            )
            fixture_count += 1

        families_payload.append({"family": family, "fixtures": fixture_payloads})

    artifact = {
        "artifact_id": "capability_boundary_replay_results_v1",
        "generated_by": "CapabilityBoundaryReplayArtifactGenerator",
        "version": "1.0",
        "evaluation_mode": "deterministic",
        "llm_judges": "none",
        "external_apis": "none",
        "families": families_payload,
        "global_summary": {
            "family_count": len(families_payload),
            "fixture_count": fixture_count,
            "fixtures_with_capability_boundary_data": fixtures_with_boundary_data,
            "fixtures_with_boundary_drift": fixtures_with_boundary_drift,
            "total_missing_boundary_edges": total_missing_boundary_edges,
            "total_added_boundary_edges": total_added_boundary_edges,
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = generate_capability_boundary_replay_artifact()
    print(path.relative_to(REPO_ROOT).as_posix())
