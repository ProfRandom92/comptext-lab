from __future__ import annotations

import json
from pathlib import Path

from scripts.render_multi_family_admissibility_svg import render_svg

INPUT_PATH = Path("artifacts/multi_family_admissibility_results.json")
SVG_PATH = Path("artifacts/multi_family_admissibility_curves.svg")



def _render() -> str:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    return render_svg(payload)



def test_multi_family_svg_render_is_deterministic() -> None:
    assert _render() == _render()



def test_rendered_svg_matches_committed_artifact() -> None:
    assert _render() == SVG_PATH.read_text(encoding="utf-8")



def test_svg_contains_current_families() -> None:
    output = _render()
    assert "coding_workflow_pr_review" in output
    assert "incident_response_page_triage" in output



def test_svg_contains_degradation_levels() -> None:
    output = _render()
    for level in ("baseline", "mild", "moderate", "severe"):
        assert f">{level}<" in output



def test_svg_has_no_nondeterministic_fields() -> None:
    output = _render().lower()
    banned_tokens = ("timestamp", "date", "time", "random", "uuid", "id=")
    for token in banned_tokens:
        assert token not in output
