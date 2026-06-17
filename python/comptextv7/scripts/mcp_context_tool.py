"""One-shot JSON tool adapter for the deterministic MCP context layer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.mcp_context_cli import load_fixture_context
from src.comptext_v7.mcp import build_replay_payload, render_prompt_context, validate_replay_payload


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _load_request(path: Path | None) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8") if path is not None else sys.stdin.read()
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing request file: {path.as_posix() if path is not None else '<stdin>'}") from exc
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON request: {exc}") from exc
    if not isinstance(request, dict):
        raise RuntimeError("request must be a JSON object")
    return request


def _params(request: dict[str, Any]) -> dict[str, Any]:
    params = request.get("params", {})
    if not isinstance(params, dict):
        raise RuntimeError("request.params must be a JSON object")
    return params


def _tool_name(request: dict[str, Any]) -> str:
    tool = request.get("tool")
    if not isinstance(tool, str) or not tool:
        raise RuntimeError("request.tool must be a non-empty string")
    return tool


def _payload_from_params(params: dict[str, Any]) -> dict[str, Any]:
    payload = params.get("payload")
    if isinstance(payload, dict):
        return payload

    fixture = params.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise RuntimeError("request.params requires payload object or fixture path")
    return build_replay_payload(load_fixture_context(Path(fixture)))


def _handle_build_replay_payload(params: dict[str, Any]) -> dict[str, Any]:
    fixture = params.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise RuntimeError("build_replay_payload requires params.fixture")

    payload = build_replay_payload(load_fixture_context(Path(fixture)))
    result: dict[str, Any] = {"payload": payload}

    validation = validate_replay_payload(payload) if params.get("validate") is True else None
    if validation is not None:
        result["validation"] = validation
    if params.get("render_prompt") is True:
        prompt_payload = {**payload}
        if validation is not None:
            prompt_payload["validation"] = validation
        result["prompt_context"] = render_prompt_context(prompt_payload)
    return result


def _handle_render_prompt_context(params: dict[str, Any]) -> dict[str, Any]:
    payload = _payload_from_params(params)
    if params.get("validate") is True:
        payload = {**payload, "validation": validate_replay_payload(payload)}
    return {"prompt_context": render_prompt_context(payload)}


def _handle_validate_replay_payload(params: dict[str, Any]) -> dict[str, Any]:
    return {"validation": validate_replay_payload(_payload_from_params(params))}


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    tool = _tool_name(request)
    params = _params(request)

    if tool == "build_replay_payload":
        result = _handle_build_replay_payload(params)
    elif tool == "render_prompt_context":
        result = _handle_render_prompt_context(params)
    elif tool == "validate_replay_payload":
        result = _handle_validate_replay_payload(params)
    else:
        raise RuntimeError(f"unsupported tool: {tool}")

    return {"ok": True, "result": result, "tool": tool}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one deterministic MCP context-layer tool request.")
    parser.add_argument("--request-file", type=Path, help="JSON request file. Reads stdin when omitted.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    tool: str | None = None
    try:
        request = _load_request(args.request_file)
        request_tool = request.get("tool")
        tool = request_tool if isinstance(request_tool, str) else None
        response = handle_request(request)
        sys.stdout.write(_json_response(response))
        return 0
    except Exception as exc:
        sys.stdout.write(
            _json_response(
                {
                    "error": {
                        "message": str(exc),
                        "type": exc.__class__.__name__,
                    },
                    "ok": False,
                    "tool": tool,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
