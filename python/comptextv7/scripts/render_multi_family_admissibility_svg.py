from __future__ import annotations

import json
from pathlib import Path

INPUT_PATH = Path("artifacts/multi_family_admissibility_results.json")
OUTPUT_PATH = Path("artifacts/multi_family_admissibility_curves.svg")

WIDTH = 1000
HEIGHT = 560
MARGIN_LEFT = 90
MARGIN_RIGHT = 40
MARGIN_TOP = 70
MARGIN_BOTTOM = 120

TITLE = "Multi-Family Admissibility Degradation Curves"
X_LABEL = "degradation level"
Y_LABEL = "overall_admissibility_score"
LEVELS: tuple[str, ...] = ("baseline", "mild", "moderate", "severe")
PALETTE: tuple[str, ...] = (
    "#0055aa",
    "#aa5500",
    "#117733",
    "#882255",
    "#44aa99",
    "#cc6677",
)


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _level_from_fixture_id(fixture_id: str) -> str:
    if "_mild_" in fixture_id:
        return "mild"
    if "_moderate_" in fixture_id:
        return "moderate"
    if "_degraded_" in fixture_id:
        return "severe"
    return "baseline"


def render_svg(payload: dict) -> str:
    families = sorted(payload["families"], key=lambda family: family["family"])

    plot_width = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    plot_right = WIDTH - MARGIN_RIGHT
    plot_bottom = HEIGHT - MARGIN_BOTTOM

    x_by_level = {
        level: MARGIN_LEFT + (plot_width * idx / (len(LEVELS) - 1))
        for idx, level in enumerate(LEVELS)
    }

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        f'  <text x="{WIDTH/2:.1f}" y="36" text-anchor="middle" font-size="22" font-family="monospace" fill="#111111">{TITLE}</text>',
        f'  <line x1="{MARGIN_LEFT}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#222222" stroke-width="1"/>',
        f'  <line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP}" x2="{MARGIN_LEFT}" y2="{plot_bottom}" stroke="#222222" stroke-width="1"/>',
    ]

    for tick_score in (0.0, 0.5, 1.0):
        y = MARGIN_TOP + ((1.0 - tick_score) * plot_height)
        elements.append(
            f'  <line x1="{MARGIN_LEFT}" y1="{_fmt(y)}" x2="{plot_right}" y2="{_fmt(y)}" stroke="#e0e0e0" stroke-width="1"/>'
        )
        elements.append(
            f'  <text x="{MARGIN_LEFT-12}" y="{_fmt(y+4)}" text-anchor="end" font-size="12" font-family="monospace" fill="#333333">{_fmt(tick_score)}</text>'
        )

    for level in LEVELS:
        x = x_by_level[level]
        elements.append(
            f'  <text x="{_fmt(x)}" y="{plot_bottom+24}" text-anchor="middle" font-size="12" font-family="monospace" fill="#222222">{level}</text>'
        )

    elements.append(
        f'  <text x="{WIDTH/2:.1f}" y="{HEIGHT-20}" text-anchor="middle" font-size="13" font-family="monospace" fill="#111111">{X_LABEL}</text>'
    )
    elements.append(
        f'  <text x="20" y="{HEIGHT/2:.1f}" transform="rotate(-90 20 {HEIGHT/2:.1f})" text-anchor="middle" font-size="13" font-family="monospace" fill="#111111">{Y_LABEL}</text>'
    )

    legend_x = 690
    legend_y = 84
    legend_height = 30 + 18 * len(families)
    elements.append(f'  <rect x="{legend_x}" y="{legend_y}" width="270" height="{legend_height}" fill="#f8f8f8" stroke="#cccccc"/>')
    elements.append(f'  <text x="{legend_x+12}" y="{legend_y+20}" font-size="12" font-family="monospace" fill="#111111">Families</text>')

    for idx, family in enumerate(families):
        family_name = family["family"]
        color = PALETTE[idx % len(PALETTE)]
        points_by_level = {
            _level_from_fixture_id(point["fixture_id"]): point
            for point in family["curve"]["points"]
        }

        polyline = " ".join(
            f"{_fmt(x_by_level[level])},{_fmt(MARGIN_TOP + ((1.0 - float(points_by_level[level]['overall_admissibility_score'])) * plot_height))}"
            for level in LEVELS
        )
        elements.append(f'  <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="3"/>')

        for level in LEVELS:
            score = float(points_by_level[level]["overall_admissibility_score"])
            x = x_by_level[level]
            y = MARGIN_TOP + ((1.0 - score) * plot_height)
            elements.append(f'  <circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="4" fill="{color}"/>')

        ly = legend_y + 38 + idx * 18
        elements.append(f'  <line x1="{legend_x+12}" y1="{ly-4}" x2="{legend_x+36}" y2="{ly-4}" stroke="{color}" stroke-width="3"/>')
        elements.append(f'  <text x="{legend_x+44}" y="{ly}" font-size="11" font-family="monospace" fill="#222222">{family_name}</text>')

    elements.append("</svg>")
    return "\n".join(elements) + "\n"


if __name__ == "__main__":
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    svg = render_svg(payload)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
