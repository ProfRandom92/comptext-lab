"""Generate deterministic evidence index for committed artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "evidence_index.json"

ARTIFACT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "path": "artifacts/capability_boundary_replay_results.json",
        "format": "json",
        "generator": "scripts/generate_capability_boundary_replay_artifact.py",
        "evidence_category": "capability_boundary_replay",
        "evidence_role": "capability boundary drift replay evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/graph_diff_results.json",
        "format": "json",
        "generator": "scripts/generate_graph_diff_artifact.py",
        "evidence_category": "graph_diff",
        "evidence_role": "relational replay graph evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/mcp_trace_corruption_manifest.json",
        "format": "json",
        "generator": "scripts/generate_mcp_trace_corruptions.py",
        "evidence_category": "corruption_manifest",
        "evidence_role": "deterministic MCP trace corruption manifest evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/mcp_trace_replay_results.json",
        "format": "json",
        "generator": "scripts/generate_mcp_trace_replay_artifact.py",
        "evidence_category": "mcp_trace_replay",
        "evidence_role": "single-family MCP trace replay evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/multi_family_admissibility_curves.svg",
        "format": "svg",
        "generator": "scripts/render_multi_family_admissibility_svg.py",
        "evidence_category": "multi_family_admissibility_visualization",
        "evidence_role": "visualization of admissibility outcomes",
        "evidence_bearing": False,
        "visualization_only": True,
    },
    {
        "path": "artifacts/multi_family_admissibility_results.json",
        "format": "json",
        "generator": "scripts/generate_multi_family_admissibility_artifact.py",
        "evidence_category": "multi_family_admissibility",
        "evidence_role": "cross-family admissibility evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/replay_semantic_integrity_results.json",
        "format": "json",
        "generator": "scripts/generate_replay_semantic_integrity_artifact.py",
        "evidence_category": "replay_semantic_integrity",
        "evidence_role": "semantic replay integrity evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
    {
        "path": "artifacts/tool_ordering_replay_results.json",
        "format": "json",
        "generator": "scripts/generate_tool_ordering_replay_artifact.py",
        "evidence_category": "tool_ordering_replay",
        "evidence_role": "tool-order replay drift evidence",
        "evidence_bearing": True,
        "visualization_only": False,
    },
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_families() -> set[str]:
    manifest = _load_json(MANIFEST_PATH)
    return {str(fixture["family"]) for fixture in manifest["fixtures"]}

def _family_from_fixture_slug(slug: str) -> str | None:
    match = re.match(r"^(?P<family>.+)_[^_]+_v\d+$", slug)
    if not match:
        return None
    return match.group("family")

def _extract_fixture_families(payload: dict[str, Any]) -> list[str]:
    families: set[str] = set()
    if isinstance(payload.get("families"), list):
        for family in payload["families"]:
            if isinstance(family, dict) and isinstance(family.get("family"), str):
                families.add(family["family"])
    if isinstance(payload.get("family"), str):
        families.add(payload["family"])

    if isinstance(payload.get("corruptions"), list):
        for corruption in payload["corruptions"]:
            if not isinstance(corruption, dict):
                continue
            source_fixture = corruption.get("source_fixture")
            if not isinstance(source_fixture, str):
                continue
            fixture_slug = source_fixture.rsplit("/", 1)[-1]
            family = _family_from_fixture_slug(fixture_slug)
            if family:
                families.add(family)
    return sorted(families)


def _build_artifact_entry(spec: dict[str, Any], manifest_families: set[str]) -> dict[str, Any] | None:
    artifact_path = REPO_ROOT / spec["path"]
    if not artifact_path.exists():
        return None

    entry = {
        "path": spec["path"],
        "format": spec["format"],
        "generator": spec["generator"],
        "evidence_category": spec["evidence_category"],
        "evidence_role": spec["evidence_role"],
        "fixture_families": [],
        "top_level_keys": [],
        "deterministic_evaluation": True,
        "llm_judges": "none",
        "external_apis": "none",
        "manifest_aligned": False,
        "evidence_bearing": spec["evidence_bearing"],
        "visualization_only": spec["visualization_only"],
    }

    if spec["format"] == "json":
        payload = _load_json(artifact_path)
        families = _extract_fixture_families(payload)
        entry["fixture_families"] = families
        entry["top_level_keys"] = sorted(payload.keys())
        entry["deterministic_evaluation"] = payload.get("evaluation_mode", "deterministic") == "deterministic"
        entry["llm_judges"] = payload.get("llm_judges", "none")
        entry["external_apis"] = payload.get("external_apis", "none")
        if families:
            entry["manifest_aligned"] = set(families) == manifest_families

    return entry


def generate_evidence_index(output_path: Path = OUTPUT_PATH) -> Path:
    manifest_families = _manifest_families()
    artifacts = [
        entry
        for spec in sorted(ARTIFACT_SPECS, key=lambda item: item["path"])
        for entry in [_build_artifact_entry(spec, manifest_families)]
        if entry is not None
    ]

    index = {
        "artifact_id": "evidence_index_v1",
        "generated_by": "EvidenceIndexGenerator",
        "version": "1.0",
        "evaluation_mode": "deterministic",
        "llm_judges": "none",
        "external_apis": "none",
        "artifacts": artifacts,
        "global_summary": {
            "artifact_count": len(artifacts),
            "json_artifact_count": sum(1 for item in artifacts if item["format"] == "json"),
            "svg_artifact_count": sum(1 for item in artifacts if item["format"] == "svg"),
            "evidence_bearing_count": sum(1 for item in artifacts if item["evidence_bearing"]),
            "visualization_only_count": sum(1 for item in artifacts if item["visualization_only"]),
            "deterministic_artifact_count": sum(1 for item in artifacts if item["deterministic_evaluation"]),
            "llm_free_artifact_count": sum(1 for item in artifacts if item["llm_judges"] == "none"),
            "external_api_free_artifact_count": sum(1 for item in artifacts if item["external_apis"] == "none"),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = generate_evidence_index()
    print(path.relative_to(REPO_ROOT).as_posix())
