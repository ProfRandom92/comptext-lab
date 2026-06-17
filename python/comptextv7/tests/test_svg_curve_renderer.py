from __future__ import annotations

import json
import re
from pathlib import Path

from src.visualization.svg_curve_renderer import SVGCurveRenderer

INPUT_PATH = Path("artifacts/layered_admissibility_results.json")
SVG_PATH = Path("docs/media/layered_admissibility_curve.svg")


def _render() -> str:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    return SVGCurveRenderer().render(payload)


def test_svg_render_is_deterministic() -> None:
    assert _render() == _render()


def test_svg_root_exists() -> None:
    output = _render()
    assert output.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert output.strip().endswith("</svg>")


def test_svg_contains_fixture_labels() -> None:
    output = _render()
    assert "coding_workflow_pr_review_v1" in output
    assert "coding_workflow_pr_review_mild_v1" in output
    assert "coding_workflow_pr_review_moderate_v1" in output
    assert "coding_workflow_pr_review_degraded_v1" in output


def test_svg_contains_expected_failure_annotations() -> None:
    output = _render()
    for label in [
        "RECOVERY_PATH_INVALID",
        "CAUSAL_DEPENDENCY_LOSS",
        "POLICY_ORDER_BROKEN",
        "INVARIANT_VIOLATION",
    ]:
        assert label in output


def test_svg_polyline_coordinates_monotonic_degradation() -> None:
    output = _render()
    match = re.search(r'<polyline points="([^"]+)"', output)
    assert match
    points = match.group(1).split(" ")
    y_values = [float(point.split(",")[1]) for point in points]
    assert y_values == sorted(y_values)


def test_svg_uses_stable_float_formatting() -> None:
    output = _render()
    assert "960.000,225.000" in output
    assert "380.000,95.833" in output
    assert "0.917" in output


def test_rendered_svg_matches_committed_artifact() -> None:
    generated = _render()
    committed = SVG_PATH.read_text(encoding="utf-8")
    assert generated == committed
