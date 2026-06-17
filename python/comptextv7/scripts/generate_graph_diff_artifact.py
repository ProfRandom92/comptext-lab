"""Generate deterministic graph-diff artifact from manifest fixtures."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.comptext_v7.graph import compare_edges, normalize_edges, nodes_from_edges
MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "graph_diff_results.json"

SUPPORTED_RELATION_KEYS = (
    "causal_dependencies",
    "dependencies",
    "dependency_chain",
    "policy_steps",
    "tool_calls",
    "tool_call_order",
    "recovery_paths",
    "capability_boundaries",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _discover_payload_files(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.glob("*.json") if path.is_file())


def _coerce_edge_pair(item: object) -> tuple[str, str] | None:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        return None
    left, right = item
    if not isinstance(left, str) or not isinstance(right, str):
        return None
    return (left, right)


def _coerce_node(item: object) -> str | None:
    return item if isinstance(item, str) and item else None


def _extract_edges_from_relation_value(value: object) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for nested in value.values():
            if isinstance(nested, list):
                edges.extend(_extract_edges_from_relation_value(nested))
        return edges

    if not isinstance(value, list):
        return edges

    pair_like = [_coerce_edge_pair(item) for item in value]
    if value and all(pair is not None for pair in pair_like):
        return [pair for pair in pair_like if pair is not None]

    node_list = [_coerce_node(item) for item in value]
    if value and all(node is not None for node in node_list):
        ordered = [node for node in node_list if node is not None]
        return [(ordered[idx], ordered[idx + 1]) for idx in range(len(ordered) - 1)]

    return edges


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




def _collect_dependency_graph_edges(payload: object) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        if isinstance(payload.get("edges"), list):
            for item in payload["edges"]:
                if isinstance(item, dict):
                    source = item.get("source")
                    target = item.get("target")
                    if isinstance(source, str) and isinstance(target, str):
                        edges.append((source, target))
        for value in payload.values():
            edges.extend(_collect_dependency_graph_edges(value))
    elif isinstance(payload, list):
        for item in payload:
            edges.extend(_collect_dependency_graph_edges(item))
    return edges

def _extract_edges_from_payloads(payloads: list[dict[str, Any]]) -> dict[str, tuple[tuple[str, str], ...]]:
    extracted: dict[str, tuple[tuple[str, str], ...]] = {}
    for relation_key in SUPPORTED_RELATION_KEYS:
        edges: list[tuple[str, str]] = []
        for payload in payloads:
            for relation_value in _collect_relation_values(payload, relation_key):
                edges.extend(_extract_edges_from_relation_value(relation_value))
        if relation_key == "dependencies":
            for payload in payloads:
                edges.extend(_collect_dependency_graph_edges(payload))
        extracted[relation_key] = normalize_edges(edges)
    return extracted


def generate_graph_diff_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    manifest = _load_json(MANIFEST_PATH)
    fixtures: list[dict[str, Any]] = manifest["fixtures"]

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in fixtures:
        by_family[str(fixture["family"])].append(fixture)

    families_payload: list[dict[str, Any]] = []
    fixture_count = 0
    total_missing_edges = 0
    total_added_edges = 0

    for family in sorted(by_family):
        fixture_payloads: list[dict[str, Any]] = []
        for fixture in sorted(by_family[family], key=lambda item: str(item["fixture_id"])):
            fixture_root = REPO_ROOT / str(fixture["path"])
            original_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "original")]
            replay_payloads = [_load_json(path) for path in _discover_payload_files(fixture_root / "reconstructed")]

            original_by_category = _extract_edges_from_payloads(original_payloads)
            replay_by_category = _extract_edges_from_payloads(replay_payloads)

            category_payload: dict[str, Any] = {}
            for category in sorted(SUPPORTED_RELATION_KEYS):
                original_edges = original_by_category[category]
                replay_edges = replay_by_category[category]
                diff = compare_edges(original_edges, replay_edges)
                total_missing_edges += len(diff.missing_edges)
                total_added_edges += len(diff.added_edges)
                category_payload[category] = {
                    "original_edge_count": len(original_edges),
                    "replay_edge_count": len(replay_edges),
                    "missing_edges": [list(edge) for edge in diff.missing_edges],
                    "added_edges": [list(edge) for edge in diff.added_edges],
                    "missing_nodes": list(diff.missing_nodes),
                    "added_nodes": list(diff.added_nodes),
                    "original_nodes": list(nodes_from_edges(original_edges)),
                    "replay_nodes": list(nodes_from_edges(replay_edges)),
                }

            fixture_payloads.append(
                {
                    "fixture_id": fixture["fixture_id"],
                    "degradation_level": fixture["degradation_level"],
                    "expected_admissible": fixture["expected_admissible"],
                    "expected_failure_labels": fixture["expected_failure_labels"],
                    "edge_categories": category_payload,
                }
            )
            fixture_count += 1

        families_payload.append({"family": family, "fixtures": fixture_payloads})

    artifact = {
        "artifact_id": "graph_diff_results_v1",
        "generated_by": "GraphDiffArtifactGenerator",
        "version": "1.0",
        "evaluation_mode": "deterministic",
        "llm_judges": "none",
        "external_apis": "none",
        "families": families_payload,
        "global_summary": {
            "family_count": len(families_payload),
            "fixture_count": fixture_count,
            "total_missing_edges": total_missing_edges,
            "total_added_edges": total_added_edges,
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = generate_graph_diff_artifact()
    print(path.relative_to(REPO_ROOT).as_posix())
