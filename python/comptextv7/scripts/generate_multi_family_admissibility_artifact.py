"""Deterministic entrypoint for multi-family admissibility artifact regeneration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.degradation_curve_generator import (
    LAYERED_CURVE_LEVELS,
    MANIFEST_PATH,
    DegradationCurveGenerator,
)

ARTIFACT_ID = "multi_family_admissibility_results_v1"
OUTPUT_PATH = Path("artifacts/multi_family_admissibility_results.json")


def _families_with_standard_levels(
    manifest_path: Path = MANIFEST_PATH,
    levels: tuple[str, ...] = LAYERED_CURVE_LEVELS,
) -> tuple[str, ...]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"invalid fixture manifest format: {manifest_path}")

    family_to_levels: dict[str, set[str]] = {}
    for entry in fixtures:
        family = entry.get("family")
        level = entry.get("degradation_level")
        if not family or not level:
            continue
        family_to_levels.setdefault(str(family), set()).add(str(level))

    return tuple(sorted(family for family, family_levels in family_to_levels.items() if set(levels).issubset(family_levels)))


def generate_multi_family_admissibility_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    generator = DegradationCurveGenerator()
    families_payload: list[dict[str, Any]] = []

    for family in _families_with_standard_levels():
        fixtures = generator.fixtures_for_manifest_family(family)
        curve = generator.generate(fixtures, curve_id=f"{family}_curve_v1")
        families_payload.append({"family": family, "curve": generator.to_dict(curve)})

    payload = {
        "artifact_id": ARTIFACT_ID,
        "generated_by": DegradationCurveGenerator.__name__,
        "version": "1.0",
        "families": families_payload,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_multi_family_admissibility_artifact()
    print(output_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
