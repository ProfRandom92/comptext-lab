#!/usr/bin/env python3
"""Build a deterministic local AI workflow evidence snapshot."""

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
from scripts.safe_pr_gate import GateState, collect_gate_state


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic local AI workflow evidence snapshot.")
    parser.add_argument(
        "--validation-command",
        action="append",
        default=[],
        help="Validation command executed for the snapshot evidence. May be repeated.",
    )
    parser.add_argument(
        "--validation-result",
        action="append",
        default=[],
        help="Validation result corresponding to each command. May be repeated.",
    )
    parser.add_argument(
        "--mcp-context-output-ref",
        help="Optional reference to a previously generated MCP context output.",
    )
    return parser.parse_args(argv)


def _error_response(exc: RuntimeError) -> dict[str, Any]:
    return {
        "error": {
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
        "ok": False,
        "result": "ERROR",
    }


def build_ai_workflow_snapshot(
    state: GateState,
    *,
    validation_commands: list[str],
    validation_results: list[str],
    mcp_context_output_ref: str | None = None,
) -> dict[str, Any]:
    agent_artifact_bundle = build_agent_artifact_bundle(
        state,
        allow_main=True,
        validation_commands=validation_commands,
        validation_results=validation_results,
        mcp_context_output_ref=mcp_context_output_ref,
    )
    snapshot: dict[str, Any] = {
        "agent_artifact_bundle": agent_artifact_bundle,
        "ok": agent_artifact_bundle["ok"],
        "result": agent_artifact_bundle["result"],
        "safe_pr_gate": agent_artifact_bundle["safe_pr_gate"],
        "validation_evidence": agent_artifact_bundle["validation_evidence"],
    }
    if mcp_context_output_ref is not None:
        snapshot["mcp_context_output_ref"] = mcp_context_output_ref
    return snapshot


def _emit_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        snapshot = build_ai_workflow_snapshot(
            collect_gate_state(),
            validation_commands=list(args.validation_command),
            validation_results=list(args.validation_result),
            mcp_context_output_ref=args.mcp_context_output_ref,
        )
        _emit_json(snapshot)
        return 0 if snapshot["ok"] else 1
    except RuntimeError as exc:
        _emit_json(_error_response(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
