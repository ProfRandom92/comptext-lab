#!/usr/bin/env python3
"""Generate deterministic dashboard release health summary artifacts.

The generator intentionally uses file-existence and small filesystem metadata
checks only. It does not read report bodies, contact network services, require a
live server, or inspect real experiment data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports"
SUMMARY_MD_PATH = REPORT_DIR / "dashboard-health-summary.md"
SUMMARY_JSON_PATH = REPORT_DIR / "dashboard-health-summary.json"

GENERATED_AT = "2026-01-01T00:00:00Z"
TARGET_REPO = "ProfRandom92/Comptextv7"
RELATED_EXPERIMENT_REPO = "ProfRandom92/Comptext-Daimler-Experiment-"
SUMMARY_TYPE = "dashboard_release_health"


@dataclass(frozen=True)
class Artifact:
    """A small release-readiness artifact checked by path only."""

    key: str
    path: str
    description: str
    required: bool


LOCAL_ARTIFACTS = [
    Artifact(
        "project_health_report",
        "docs/reports/project-health-report.md",
        "Generated project health and release status report.",
        True,
    ),
    Artifact(
        "contract_validation_report",
        "docs/reports/contract-validation-report.md",
        "Contract schema validation report.",
        True,
    ),
    Artifact(
        "api_export_validation_report",
        "docs/reports/api-export-validation-report.md",
        "Synthetic API/export contract validation report.",
        True,
    ),
    Artifact(
        "contract_fixture_generation_report",
        "docs/reports/contract-fixture-generation-report.md",
        "Synthetic API/dashboard fixture generation report.",
        True,
    ),
    Artifact(
        "cross_repo_release_checklist",
        "docs/CROSS_REPO_RELEASE_CHECKLIST.md",
        "Cross-repo release checklist for sanitized promotion evidence.",
        True,
    ),
]

OPTIONAL_CROSS_REPO_ARTIFACTS = [
    Artifact(
        "benchmark_summary",
        "benchmark-summary.json",
        "Optional sanitized benchmark promotion summary from the experiment repository.",
        False,
    ),
    Artifact(
        "regression_summary",
        "regression-summary.json",
        "Optional sanitized regression promotion summary from the experiment repository.",
        False,
    ),
    Artifact(
        "sanitization_summary",
        "sanitization-summary.json",
        "Optional sanitized data-handling summary from the experiment repository.",
        False,
    ),
    Artifact(
        "report_contract_validation_report",
        "report-contract-validation-report.md",
        "Optional report-contract validation evidence from the experiment repository.",
        False,
    ),
]

SAFETY_NOTES = [
    "Synthetic/static metadata only; generated_at is deterministic.",
    "No real Daimler data, customer payloads, secrets, cookies, tokens, raw production logs, or proprietary documents are included.",
    "No live server, network access, external dependencies, or experiment-repository checkout is required.",
    "The generator uses file-existence and small filesystem metadata checks only and does not read report bodies.",
]

NEXT_ACTIONS_READY = [
    "Render docs/reports/dashboard-health-summary.json in future dashboard/UI work as a static release-readiness widget.",
    "Attach optional sanitized cross-repo benchmark, regression, sanitization, and report-contract summaries when promotion evidence is available.",
    "Keep API/export contract validation and fixture generation in CI before release promotion.",
]

NEXT_ACTIONS_BLOCKED = [
    "Regenerate missing local validation artifacts before using this summary for release readiness.",
    "Run the agent workflow checks and commit the updated docs/reports artifacts.",
    *NEXT_ACTIONS_READY,
]


ArtifactRecord = dict[str, object]


def relative_path(path: Path) -> str:
    """Return a repository-relative POSIX path."""
    return path.relative_to(ROOT).as_posix()


def artifact_record(artifact: Artifact, base_dir: Path | None = None) -> ArtifactRecord:
    """Build a deterministic artifact status record without reading contents."""
    absolute_path = (base_dir / artifact.path) if base_dir else (ROOT / artifact.path)
    present = absolute_path.exists()
    record: ArtifactRecord = {
        "key": artifact.key,
        "path": artifact.path,
        "required": artifact.required,
        "present": present,
        "status": "present" if present else "missing",
        "description": artifact.description,
    }
    if present and absolute_path.is_file():
        record["size_bytes"] = absolute_path.stat().st_size
    return record


def determine_overall_status(local_records: Iterable[ArtifactRecord], optional_records: Iterable[ArtifactRecord]) -> str:
    """Return release-readiness status from local and optional artifacts."""
    local_records = list(local_records)
    optional_records = list(optional_records)
    required_missing = [record for record in local_records if record["required"] and not record["present"]]
    if required_missing:
        return "red"

    optional_missing = [record for record in optional_records if not record["present"]]
    if optional_missing:
        return "yellow"

    return "green"


def build_summary() -> dict[str, object]:
    """Build a deterministic dashboard health summary payload."""
    local_records = [artifact_record(artifact) for artifact in LOCAL_ARTIFACTS]
    optional_records = [artifact_record(artifact, REPORT_DIR) for artifact in OPTIONAL_CROSS_REPO_ARTIFACTS]
    missing_required = [record["path"] for record in local_records if not record["present"]]
    missing_optional = [record["path"] for record in optional_records if not record["present"]]
    overall_status = determine_overall_status(local_records, optional_records)

    return {
        "target_repo": TARGET_REPO,
        "related_experiment_repo": RELATED_EXPERIMENT_REPO,
        "summary_type": SUMMARY_TYPE,
        "synthetic": True,
        "generated_at": GENERATED_AT,
        "overall_status": overall_status,
        "checks": {record["key"]: record for record in local_records},
        "required_artifacts_present": [record["path"] for record in local_records if record["present"]],
        "missing_artifacts": {
            "required_local": missing_required,
            "optional_cross_repo": missing_optional,
        },
        "optional_cross_repo_artifacts": optional_records,
        "next_recommended_actions": NEXT_ACTIONS_READY if overall_status != "red" else NEXT_ACTIONS_BLOCKED,
        "safety_notes": SAFETY_NOTES,
    }


def status_label(present: object) -> str:
    """Return a compact Markdown status label."""
    return "present" if present else "missing"


def table_rows(records: Iterable[ArtifactRecord]) -> list[str]:
    """Render artifact records as Markdown table rows."""
    rows = []
    for record in records:
        rows.append(
            f"| `{record['path']}` | {status_label(record['present'])} | {record['description']} |"
        )
    return rows


def bullet_list(items: Iterable[object], empty: str) -> list[str]:
    """Render a deterministic Markdown bullet list."""
    values = [str(item) for item in items]
    if not values:
        return [f"- {empty}"]
    return [f"- `{value}`" for value in values]


def build_markdown(summary: dict[str, object]) -> str:
    """Build the dashboard-facing Markdown summary."""
    local_records = list(summary["checks"].values())  # type: ignore[union-attr]
    optional_records = list(summary["optional_cross_repo_artifacts"])  # type: ignore[arg-type]
    missing = summary["missing_artifacts"]  # type: ignore[assignment]

    lines = [
        "# Dashboard Release Health Summary",
        "",
        "This deterministic artifact converts local project health, contract validation, API/export validation, fixture generation, and cross-repo promotion signals into compact release-readiness metadata for future dashboard/UI rendering.",
        "",
        "## Repository overview",
        "",
        f"- target_repo: `{summary['target_repo']}`",
        f"- related_experiment_repo: `{summary['related_experiment_repo']}`",
        f"- summary_type: `{summary['summary_type']}`",
        f"- generated_at: `{summary['generated_at']}`",
        "- synthetic: `true`",
        "- live_server_required: `false`",
        "- network_required: `false`",
        "- real_daimler_data_required: `false`",
        "",
        "## Overall status",
        "",
        f"- overall_status: `{summary['overall_status']}`",
        "- status_basis: Missing required local Comptextv7 validation artifacts are red; complete local validation with missing optional cross-repo promotion artifacts is yellow; complete local and optional promotion artifacts are green.",
        "",
        "## Local validation artifacts",
        "",
        "| Artifact | Status | Notes |",
        "| --- | --- | --- |",
        *table_rows(local_records),
        "",
        "## Optional cross-repo promotion artifacts",
        "",
        "These sanitized promotion summaries may be copied into `docs/reports/` when available from `ProfRandom92/Comptext-Daimler-Experiment-`, but they are not required for this local dashboard summary.",
        "",
        "| Artifact | Status | Notes |",
        "| --- | --- | --- |",
        *table_rows(optional_records),
        "",
        "## Missing artifacts",
        "",
        "### Required local artifacts",
        "",
        *bullet_list(missing["required_local"], "None."),  # type: ignore[index]
        "",
        "### Optional cross-repo artifacts",
        "",
        *bullet_list(missing["optional_cross_repo"], "None."),  # type: ignore[index]
        "",
        "## Next recommended actions",
        "",
        *[f"- {item}" for item in summary["next_recommended_actions"]],  # type: ignore[index]
        "",
        "## Safety notes",
        "",
        *[f"- {item}" for item in summary["safety_notes"]],  # type: ignore[index]
        "",
    ]
    return "\n".join(lines)


def write_summary(summary: dict[str, object]) -> None:
    """Write Markdown and JSON summary artifacts."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_MD_PATH.write_text(build_markdown(summary), encoding="utf-8")


def main() -> int:
    summary = build_summary()
    write_summary(summary)
    print(f"Wrote {relative_path(SUMMARY_MD_PATH)}")
    print(f"Wrote {relative_path(SUMMARY_JSON_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
