from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_layered_admissibility_artifact import (
    CURVE_ID,
    generate_layered_admissibility_artifact,
)
from src.validation.degradation_curve_generator import DegradationCurveGenerator

ARTIFACT_PATH = Path("artifacts/layered_admissibility_results.json")
CANONICAL_FIXTURE_ID = "coding_workflow_pr_review_moderate_v1"
CANONICAL_MODERATE_SCORE = 0.8333333333333334


def test_generated_artifact_matches_committed_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "layered_admissibility_results.json"
    generate_layered_admissibility_artifact(output_path)

    generated = json.loads(output_path.read_text(encoding="utf-8"))
    committed = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert generated == committed


def test_generated_artifact_has_no_new_top_level_fields() -> None:
    generator = DegradationCurveGenerator()
    curve = generator.generate(generator.fixtures_for_layered_admissibility_curve(), curve_id=CURVE_ID)

    generated_top_level = set(generator.to_dict(curve).keys())
    committed_top_level = set(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")).keys())
    assert generated_top_level == committed_top_level


def test_moderate_fixture_score_remains_canonical() -> None:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    points = payload["points"]
    moderate_point = next(point for point in points if point["fixture_id"] == CANONICAL_FIXTURE_ID)
    assert moderate_point["overall_admissibility_score"] == CANONICAL_MODERATE_SCORE
