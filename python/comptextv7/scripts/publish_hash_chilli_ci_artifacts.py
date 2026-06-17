#!/usr/bin/env python3
"""Publish Hash/chilli Cloud CI handoff artifacts from GitHub Actions.

This script is intentionally a CI publisher, not a local validation runner. It
packages the outcomes already produced by the GitHub Actions validation job into
small JSON artifacts for display-only Hash/chilli consumers.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,96}")
TERMINAL_STEP_NAMES = ("checkout", "setup_python", "install", "pytest", "dashboard")


def utc_now() -> str:
    """Return a UTC RFC 3339 timestamp with second precision."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def env(name: str, default: str = "") -> str:
    """Read a GitHub Actions environment value."""

    return os.environ.get(name, default)


def sanitized_request_id(raw_request_id: str) -> str | None:
    """Return a contract-safe request identifier or null for publication."""

    if REQUEST_ID_PATTERN.fullmatch(raw_request_id):
        return raw_request_id
    return None


def step_outcomes() -> dict[str, str]:
    """Collect the cloud step outcomes passed by the workflow."""

    return {
        "checkout": env("CHECKOUT_OUTCOME", "skipped"),
        "setup_python": env("SETUP_PYTHON_OUTCOME", "skipped"),
        "install": env("INSTALL_OUTCOME", "skipped"),
        "pytest": env("PYTEST_OUTCOME", "skipped"),
        "dashboard": env("DASHBOARD_OUTCOME", "skipped"),
    }


def status_and_summary(outcomes: dict[str, str]) -> tuple[str, str]:
    """Map GitHub step outcomes to the compact CFI status and summary."""

    if any(value == "cancelled" for value in outcomes.values()):
        return "cancelled", "Cloud CI validation was cancelled before producing a pass/fail outcome."
    if all(outcomes.get(name) == "success" for name in TERMINAL_STEP_NAMES):
        return "passed", "Cloud CI validation passed for the requested commit."

    failed_or_skipped = ", ".join(name for name in TERMINAL_STEP_NAMES if outcomes.get(name) != "success")
    return "failed", f"Cloud CI validation failed or skipped: {failed_or_skipped}."[:240]


REQUIRED_ENV_VARS = ("CFI_RESULT_ID", "CFI_COMMIT_SHA", "CFI_BRANCH", "CFI_RUN_URL")


def required_env() -> dict[str, str]:
    """Return required CI metadata or fail before payload construction."""

    values = {name: env(name).strip() for name in REQUIRED_ENV_VARS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        missing_names = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s) for CFI-03 publication: {missing_names}")
    return values


def build_payload() -> dict[str, Any]:
    """Build the CFI-01 result payload for cloud publication."""

    required = required_env()
    outcomes = step_outcomes()
    status, summary = status_and_summary(outcomes)
    run_url = required["CFI_RUN_URL"]
    artifact_url = env("CFI_ARTIFACT_URL").strip() or f"{run_url}#artifacts"

    return {
        "contract": "hash_chilli_cloud_ci_result",
        "contract_version": 1,
        "result_id": required["CFI_RESULT_ID"],
        "request_id": sanitized_request_id(env("CFI_REQUEST_ID")),
        "runner": "validation_runner",
        "execution_target": "cloud_ci",
        "provider": "github_actions",
        "workflow": env("CFI_WORKFLOW_NAME", "hash-companion-validation"),
        "status": status,
        "commit_sha": required["CFI_COMMIT_SHA"],
        "branch": required["CFI_BRANCH"],
        "run_url": run_url,
        "artifact_url": artifact_url,
        "requested_at": env("REQUESTED_AT") or utc_now(),
        "completed_at": utc_now(),
        "summary": summary,
        "local_execution": "disabled",
    }


def write_json(path: Path, payload: dict[str, Any], *, compact: bool) -> None:
    """Write JSON in either compact or review-friendly form."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(f"{text}\n", encoding="utf-8")


def append_github_env(payload: dict[str, Any]) -> None:
    """Expose the authoritative status for the final workflow gate."""

    github_env = env("GITHUB_ENV")
    if not github_env:
        return
    with Path(github_env).open("a", encoding="utf-8") as env_file:
        env_file.write(f"CFI_VALIDATION_STATUS={payload['status']}\n")


def main() -> None:
    payload = build_payload()
    result_path = Path(env("CFI_RESULT_PATH", "reports/hash-chilli-cloud-ci-result.json"))
    compact_path = Path(env("CFI_COMPACT_SUMMARY_PATH", "reports/hash-chilli-cloud-ci-summary.json"))

    # Both files contain the same payload fields. The compact summary is the
    # preferred display handoff; the pretty result remains review-friendly.
    write_json(result_path, payload, compact=False)
    write_json(compact_path, payload, compact=True)
    append_github_env(payload)

    print(f"Published Hash/chilli CFI result: {result_path}")
    print(f"Published compact Hash/chilli CFI summary: {compact_path}")


if __name__ == "__main__":
    main()
