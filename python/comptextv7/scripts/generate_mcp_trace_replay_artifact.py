"""Deterministic entrypoint for MCP trace replay artifact regeneration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.degradation_curve_generator import DegradationCurveGenerator

ARTIFACT_ID = "mcp_trace_replay_results_v1"
FAMILY = "mcp_trace_replay"
CURVE_LEVELS = ("baseline", "mild", "moderate", "severe")
OUTPUT_PATH = REPO_ROOT / "artifacts" / "mcp_trace_replay_results.json"
MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"


def _fixture_payload(point: dict[str, Any], degradation_level: str) -> dict[str, Any]:
    return {
        "fixture_id": point["fixture_id"],
        "degradation_level": degradation_level,
        "expected_admissible": point["expected_admissible"],
        "observed_admissible": point["observed_admissible"],
        "overall_admissibility_score": f"{point['overall_admissibility_score']:.6f}",
        "passed_contracts": point["passed_contracts"],
        "failed_contracts": point["failed_contracts"],
        "failure_labels": point["failure_labels"],
    }


def _repo_rooted_fixture_paths(fixtures: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(path if path.is_absolute() else REPO_ROOT / path for path in fixtures)


def generate_mcp_trace_replay_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    generator = DegradationCurveGenerator()
    fixtures = generator.fixtures_for_manifest_family(
        FAMILY,
        levels=CURVE_LEVELS,
        manifest_path=MANIFEST_PATH,
    )
    curve = generator.generate(_repo_rooted_fixture_paths(fixtures), curve_id=f"{FAMILY}_curve_v1")
    curve_dict = generator.to_dict(curve)

    fixture_payload = [
        _fixture_payload(point, level)
        for point, level in zip(curve_dict["points"], CURVE_LEVELS, strict=True)
    ]

    payload = {
        "artifact_id": ARTIFACT_ID,
        "generated_by": "McpTraceReplayArtifactGenerator",
        "version": "1.0",
        "family": FAMILY,
        "fixtures": fixture_payload,
        "summary": {
            "fixture_count": len(fixture_payload),
            "baseline_admissible": fixture_payload[0]["observed_admissible"],
            "severe_admissible": fixture_payload[-1]["observed_admissible"],
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_mcp_trace_replay_artifact()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
