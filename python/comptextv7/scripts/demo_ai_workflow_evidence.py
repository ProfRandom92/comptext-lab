#!/usr/bin/env python3
"""Run a deterministic local demo of the AI workflow evidence chain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_artifact_bundle import build_agent_artifact_bundle
from scripts.ai_workflow_snapshot import build_ai_workflow_snapshot
from scripts.pr_body_from_agent_bundle import render_pr_body_from_payload
from scripts.safe_pr_gate import GateState, evaluate_gate
from scripts.validate_agent_artifact_bundle import _load_json_object, validate_bundle_file

DEFAULT_DEMO_BUNDLE = REPO_ROOT / "artifacts" / "mcp_context_bundle_ref_example.json"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a deterministic local AI workflow evidence demo.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_DEMO_BUNDLE, help="Agent artifact bundle JSON path.")
    return parser.parse_args(argv)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _error_response(exc: RuntimeError) -> dict[str, Any]:
    return {
        "error": {
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
        "ok": False,
        "result": "ERROR",
    }


def _bundle_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = payload.get("bundle", payload)
    if not isinstance(bundle, dict):
        raise RuntimeError("demo bundle must contain a JSON object bundle")
    return bundle


def _state_from_bundle(bundle: dict[str, Any]) -> GateState:
    safe_pr_gate = bundle.get("safe_pr_gate")
    if not isinstance(safe_pr_gate, dict):
        raise RuntimeError("demo bundle missing safe_pr_gate object")

    branch = safe_pr_gate.get("branch")
    status_short = safe_pr_gate.get("status_short")
    changed_paths = safe_pr_gate.get("changed_paths")
    if not isinstance(branch, str):
        raise RuntimeError("demo bundle safe_pr_gate.branch must be a string")
    if not isinstance(status_short, list) or not all(isinstance(item, str) for item in status_short):
        raise RuntimeError("demo bundle safe_pr_gate.status_short must be a list of strings")
    if not isinstance(changed_paths, list) or not all(isinstance(item, str) for item in changed_paths):
        raise RuntimeError("demo bundle safe_pr_gate.changed_paths must be a list of strings")

    return GateState(
        branch=branch,
        status_short=tuple(status_short),
        changed_paths=tuple(changed_paths),
    )


def _validation_pairs(bundle: dict[str, Any]) -> tuple[list[str], list[str]]:
    validation_evidence = bundle.get("validation_evidence")
    if not isinstance(validation_evidence, list):
        raise RuntimeError("demo bundle validation_evidence must be a list")

    commands: list[str] = []
    results: list[str] = []
    for index, entry in enumerate(validation_evidence):
        if not isinstance(entry, dict):
            raise RuntimeError(f"demo bundle validation_evidence[{index}] must be a JSON object")
        command = entry.get("command")
        result = entry.get("result")
        if not isinstance(command, str) or not isinstance(result, str):
            raise RuntimeError(f"demo bundle validation_evidence[{index}] must contain command and result strings")
        commands.append(command)
        results.append(result)
    return commands, results


def _pr_body_summary(pr_body: str) -> dict[str, Any]:
    headings = [line.removeprefix("## ") for line in pr_body.splitlines() if line.startswith("## ")]
    return {
        "line_count": len(pr_body.splitlines()),
        "ok": True,
        "result": "PASS",
        "section_headings": headings,
    }


def build_demo_summary(bundle_path: Path = DEFAULT_DEMO_BUNDLE) -> dict[str, Any]:
    payload = _load_json_object(bundle_path)
    bundle = _bundle_from_payload(payload)
    validation = validate_bundle_file(bundle_path)
    state = _state_from_bundle(bundle)
    commands, results = _validation_pairs(bundle)
    mcp_context_output_ref = bundle.get("mcp_context_output_ref")
    if mcp_context_output_ref is not None and not isinstance(mcp_context_output_ref, str):
        raise RuntimeError("demo bundle mcp_context_output_ref must be a string when present")

    safe_pr_gate = evaluate_gate(state).to_dict()
    agent_artifact_bundle = build_agent_artifact_bundle(
        state,
        allow_main=True,
        validation_commands=commands,
        validation_results=results,
        mcp_context_output_ref=mcp_context_output_ref,
    )
    ai_workflow_snapshot = build_ai_workflow_snapshot(
        state,
        validation_commands=commands,
        validation_results=results,
        mcp_context_output_ref=mcp_context_output_ref,
    )
    pr_body = render_pr_body_from_payload(payload)

    chain = {
        "agent_artifact_bundle": {
            "changed_files": agent_artifact_bundle["changed_files"],
            "ok": agent_artifact_bundle["ok"],
            "result": agent_artifact_bundle["result"],
        },
        "ai_workflow_snapshot": {
            "ok": ai_workflow_snapshot["ok"],
            "result": ai_workflow_snapshot["result"],
        },
        "pr_body_from_agent_bundle": _pr_body_summary(pr_body),
        "safe_pr_gate": {
            "ok": safe_pr_gate["ok"],
            "problems": safe_pr_gate["problems"],
            "result": safe_pr_gate["result"],
        },
        "validate_agent_artifact_bundle": {
            "issues": validation["issues"],
            "ok": validation["ok"],
            "result": validation["result"],
        },
    }
    ok = all(step["ok"] for step in chain.values())

    summary: dict[str, Any] = {
        "chain": chain,
        "inputs": {
            "agent_artifact_bundle": _relative(bundle_path),
        },
        "ok": ok,
        "result": "PASS" if ok else "FAIL",
        "validation_evidence": bundle["validation_evidence"],
    }
    if mcp_context_output_ref is not None:
        summary["inputs"]["mcp_context_output_ref"] = mcp_context_output_ref
    return summary


def _emit_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = build_demo_summary(args.bundle)
        _emit_json(summary)
        return 0 if summary["ok"] else 1
    except RuntimeError as exc:
        _emit_json(_error_response(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
