from __future__ import annotations

import json
from pathlib import Path

from verified_experience.benchmark import run_benchmark
from verified_experience.canonical import canonical_bytes
from verified_experience.gate import evaluate_gate


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"


def render_markdown(result: dict) -> str:
    c = result["benchmark"]["strategies"]["C_verified_experience"]
    b = result["benchmark"]["strategies"]["B_ordinary_memory"]
    lines = [
        "# Verified Experience Phase-0 Gate Report",
        "",
        f"**Decision:** `{result['decision']}`",
        "",
        "## Hard Gates",
        "",
        "| Gate | Pass | Observed |",
        "|---|---:|---|",
    ]
    for name, item in result["hard_gates"].items():
        observed = item.get("observed")
        lines.append(f"| `{name}` | {'YES' if item['pass'] else 'NO'} | `{observed}` |")
    lines.extend(
        [
            "",
            "## A/B/C Summary",
            "",
            f"- B ordinary memory task success: `{b['correct_tasks']}/{b['total_tasks']}` ({b['task_success_rate']:.1%})",
            f"- C verified experience task success: `{c['correct_tasks']}/{c['total_tasks']}` ({c['task_success_rate']:.1%})",
            f"- C unauthorized promotions: `{c['unauthorized_promotions']}`",
            f"- C protected failures vs B: `{c['protected_failures_vs_b']}`",
            f"- C high-criticality evidence survival: `{c['high_criticality_evidence_survival']:.1%}`",
            "",
            "## Scope",
            "",
            "Fixture-bound deterministic Phase-0 research only. This report does not claim neural continual learning, production identity, or universal memory-system superiority.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    first = run_benchmark()
    second = run_benchmark()
    deterministic = canonical_bytes(first) == canonical_bytes(second)
    result = evaluate_gate(first, deterministic_replay=deterministic)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    json_path = ARTIFACTS / "gate-report.json"
    md_path = ARTIFACTS / "gate-report.md"
    json_path.write_text(
        json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(result), encoding="utf-8")

    print(f"VERIFIED_EXPERIENCE_PHASE0={result['decision']}")
    print(f"REPORT_JSON={json_path}")
    print(f"REPORT_MD={md_path}")
    return 0 if result["decision"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
