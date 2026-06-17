#!/usr/bin/env python3
"""Build a deterministic local evidence bundle for AI-assisted work."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.safe_pr_gate import GateState, collect_gate_state, evaluate_gate


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic local evidence bundle for AI-assisted work.")
    parser.add_argument("--allow-main", action="store_true", help="Allow bundle generation on main.")
    parser.add_argument(
        "--validation-command",
        action="append",
        default=[],
        help="Validation command executed for the bundle evidence. May be repeated.",
    )
    parser.add_argument(
        "--validation-result",
        action="append",
        default=[],
        help="Validation result corresponding to each command. May be repeated.",
    )
    parser.add_argument(
        "--mcp-context-output-ref",
        help="Optional reference to a previously generated MCP context tool output.",
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


def _build_validation_evidence(commands: list[str], results: list[str]) -> list[dict[str, str]]:
    if len(commands) != len(results):
        raise RuntimeError(
            "validation command/result count mismatch: "
            f"{len(commands)} command(s), {len(results)} result(s)"
        )
    return [{"command": command, "result": result} for command, result in zip(commands, results)]


def build_agent_artifact_bundle(
    state: GateState,
    *,
    allow_main: bool,
    validation_commands: list[str],
    validation_results: list[str],
    mcp_context_output_ref: str | None = None,
) -> dict[str, Any]:
    if state.branch == "main" and not allow_main:
        raise RuntimeError("main branch is not allowed for agent artifact bundling")

    safe_pr_gate_result = evaluate_gate(state)
    bundle_ok = safe_pr_gate_result.ok
    bundle: dict[str, Any] = {
        "branch": state.branch,
        "changed_files": list(state.changed_paths),
        "ok": bundle_ok,
        "result": "PASS" if bundle_ok else "FAIL",
        "safe_pr_gate": safe_pr_gate_result.to_dict(),
        "validation_evidence": _build_validation_evidence(validation_commands, validation_results),
    }
    if mcp_context_output_ref is not None:
        bundle["mcp_context_output_ref"] = mcp_context_output_ref
    return bundle


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        state = collect_gate_state()
        bundle = build_agent_artifact_bundle(
            state,
            allow_main=args.allow_main,
            validation_commands=list(args.validation_command),
            validation_results=list(args.validation_result),
            mcp_context_output_ref=args.mcp_context_output_ref,
        )
        sys.stdout.write(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
        return 0 if bundle["ok"] else 1
    except RuntimeError as exc:
        sys.stdout.write(json.dumps(_error_response(exc), indent=2, sort_keys=True) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
