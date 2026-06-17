#!/usr/bin/env python3
"""Render a deterministic pull-request body from an agent artifact bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_agent_artifact_bundle import DEFAULT_BUNDLE_PATH, _bundle_from_payload, _load_json_object, validate_bundle_payload


def _bullet_list(values: list[str], empty: str) -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- `{value}`" for value in values]


def _validation_lines(validation_evidence: object) -> list[str]:
    if not isinstance(validation_evidence, list) or not validation_evidence:
        return ["- No validation evidence provided in bundle."]

    lines: list[str] = []
    for entry in validation_evidence:
        if not isinstance(entry, dict):
            continue
        command = entry.get("command")
        result = entry.get("result")
        if isinstance(command, str) and isinstance(result, str):
            lines.append(f"- `{command}`: `{result}`")
    return lines or ["- No validation evidence provided in bundle."]


def _safe_gate_lines(safe_pr_gate: object) -> list[str]:
    if not isinstance(safe_pr_gate, dict):
        return ["- safe_pr_gate: `unavailable`"]

    lines = [
        f"- result: `{safe_pr_gate.get('result')}`",
        f"- ok: `{str(safe_pr_gate.get('ok')).lower()}`",
        f"- allow_dirty: `{str(safe_pr_gate.get('allow_dirty')).lower()}`",
    ]
    problems = safe_pr_gate.get("problems")
    if isinstance(problems, list) and problems:
        lines.append("- problems:")
        lines.extend(f"  - `{problem}`" for problem in problems if isinstance(problem, str))
    else:
        lines.append("- problems: `none`")
    return lines


def render_pr_body_from_bundle(bundle: dict[str, Any]) -> str:
    changed_files = bundle.get("changed_files")
    changed_file_lines = _bullet_list(changed_files if isinstance(changed_files, list) else [], "No changed files provided in bundle.")
    validation_lines = _validation_lines(bundle.get("validation_evidence"))
    safe_gate_lines = _safe_gate_lines(bundle.get("safe_pr_gate"))

    evidence_lines = [
        f"- branch: `{bundle.get('branch')}`",
        f"- bundle_result: `{bundle.get('result')}`",
    ]
    mcp_ref = bundle.get("mcp_context_output_ref")
    if isinstance(mcp_ref, str):
        evidence_lines.append(f"- mcp_context_output_ref: `{mcp_ref}`")

    lines = [
        "## Summary",
        "",
        "Deterministic agent artifact bundle evidence for this change.",
        "",
        "## Scope",
        "",
        *changed_file_lines,
        "",
        "## Validation",
        "",
        *validation_lines,
        "",
        "## Safety Gate",
        "",
        *safe_gate_lines,
        "",
        "## Evidence",
        "",
        *evidence_lines,
        "",
    ]
    return "\n".join(lines)


def render_pr_body_from_payload(payload: dict[str, Any]) -> str:
    validation = validate_bundle_payload(payload)
    if not validation["ok"]:
        issues = "\n".join(f"- {issue}" for issue in validation["issues"])
        raise RuntimeError(f"agent artifact bundle failed validation:\n{issues}")

    bundle, bundle_issues = _bundle_from_payload(payload)
    if bundle is None:
        raise RuntimeError("; ".join(bundle_issues))
    return render_pr_body_from_bundle(bundle)


def render_pr_body_from_file(path: Path) -> str:
    return render_pr_body_from_payload(_load_json_object(path))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render deterministic PR body Markdown from an agent artifact bundle.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE_PATH, help="Bundle JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.write(render_pr_body_from_file(args.bundle))
        return 0
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
