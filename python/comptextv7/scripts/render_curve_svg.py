from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.visualization.svg_curve_renderer import SVGCurveRenderer

INPUT_PATH = Path("artifacts/layered_admissibility_results.json")
OUTPUT_PATH = Path("docs/media/layered_admissibility_curve.svg")


if __name__ == "__main__":
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    svg = SVGCurveRenderer().render(payload)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
