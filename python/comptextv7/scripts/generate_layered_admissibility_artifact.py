"""Deterministic entrypoint for layered admissibility artifact regeneration."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.degradation_curve_generator import DegradationCurveGenerator

CURVE_ID = "coding_workflow_pr_review_curve_v1"
OUTPUT_PATH = Path("artifacts/layered_admissibility_results.json")


def generate_layered_admissibility_artifact(
    output_path: Path = OUTPUT_PATH,
    *,
    curve_id: str = CURVE_ID,
) -> Path:
    """Regenerate layered admissibility artifact from manifest-ordered fixtures."""

    generator = DegradationCurveGenerator()
    fixtures = generator.fixtures_for_layered_admissibility_curve()
    curve = generator.generate(fixtures, curve_id=curve_id)
    generator.write_json(curve, output_path)
    return output_path


def main() -> int:
    output_path = generate_layered_admissibility_artifact()
    print(output_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
