#!/usr/bin/env python3
"""Generate deterministic synthetic API/dashboard/export contract fixtures.

The generated fixture is intentionally synthetic and does not require a live
server or any data from ProfRandom92/Comptext-Daimler-Experiment-.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "contracts" / "examples" / "api-dashboard.example.json"
REPORT_PATH = ROOT / "docs" / "reports" / "contract-fixture-generation-report.md"
GENERATED_AT = "2026-01-01T00:00:00Z"


def build_fixture() -> dict[str, Any]:
    """Return a deterministic synthetic API/dashboard/export fixture."""
    return {
        "target_repo": "ProfRandom92/Comptextv7",
        "contract_type": "api-dashboard-export",
        "synthetic": True,
        "generated_at": GENERATED_AT,
        "api_routes": [
            {
                "route": "GET /api/dashboard",
                "purpose": "Synthetic dashboard evidence payload for local review.",
                "requires_live_server": False,
            },
            {
                "route": "GET /export.json",
                "purpose": "Synthetic machine-readable export payload shape.",
                "requires_live_server": False,
            },
            {
                "route": "GET /export.csv",
                "purpose": "Synthetic spreadsheet-friendly export payload shape.",
                "requires_live_server": False,
            },
        ],
        "dashboard_views": [
            {
                "name": "operations_summary",
                "fields": ["latency_status", "replay_status", "validation_status"],
                "synthetic_records": 3,
            },
            {
                "name": "benchmark_evidence",
                "fields": ["p50_ms", "p95_ms", "p99_ms", "error_rate"],
                "synthetic_records": 2,
            },
        ],
        "export_formats": [
            {
                "format": "json",
                "route": "GET /export.json",
                "content_type": "application/json",
                "deterministic": True,
            },
            {
                "format": "csv",
                "route": "GET /export.csv",
                "content_type": "text/csv",
                "deterministic": True,
            },
        ],
        "report_integration_points": [
            {
                "name": "benchmark_summary",
                "input": "contracts/examples/benchmark-summary.example.json",
                "data_classification": "synthetic",
            },
            {
                "name": "regression_summary",
                "input": "contracts/examples/regression-summary.example.json",
                "data_classification": "synthetic",
            },
            {
                "name": "sanitization_summary",
                "input": "contracts/examples/sanitization-summary.example.json",
                "data_classification": "synthetic",
            },
        ],
        "security_notes": [
            "Synthetic fixture only; no real Daimler data is included.",
            "No secrets, tokens, cookies, customer data, raw production logs, or proprietary documents are included.",
            "Fixture generation does not require a live server or external dependencies.",
        ],
    }


def build_report(fixture: dict[str, Any]) -> str:
    """Return a Markdown report describing generated fixture artifacts."""
    return "\n".join(
        [
            "# Contract Fixture Generation Report",
            "",
            f"- generated_at: {GENERATED_AT}",
            "- status: pass",
            f"- fixture: `{FIXTURE_PATH.relative_to(ROOT).as_posix()}`",
            f"- target_repo: {fixture['target_repo']}",
            f"- contract_type: {fixture['contract_type']}",
            f"- synthetic: {str(fixture['synthetic']).lower()}",
            f"- api_route_count: {len(fixture['api_routes'])}",
            f"- dashboard_view_count: {len(fixture['dashboard_views'])}",
            f"- export_format_count: {len(fixture['export_formats'])}",
            f"- report_integration_point_count: {len(fixture['report_integration_points'])}",
            "",
            "## Safety",
            "",
            "The fixture is deterministic, synthetic, and generated from static values in this repository.",
            "It does not contact a live server, read experiment repository data, or include secrets, cookies, customer data, raw production logs, or proprietary documents.",
            "",
        ]
    )


def main() -> int:
    fixture = build_fixture()
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(fixture), encoding="utf-8")

    print(f"Generated synthetic API/dashboard fixture at {FIXTURE_PATH.relative_to(ROOT)}")
    print(f"Generated fixture report at {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
