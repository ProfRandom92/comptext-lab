"""Deterministic CLI for compact MCP context-layer outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.comptext_v7.mcp import build_replay_payload, render_prompt_context, validate_replay_payload

DEFAULT_FIXTURE = Path("fixtures/mcp_trace_replay_v1/original")


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    display_path = _repo_relative(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing required fixture file: {display_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in fixture file: {display_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"fixture file must contain a JSON object: {display_path}")
    return payload


def load_fixture_context(fixture: Path) -> dict[str, Any]:
    fixture_path = fixture if fixture.is_absolute() else REPO_ROOT / fixture
    return {
        "task": fixture_path.parent.name,
        "trace": _load_json(fixture_path / "trace.json"),
        "state": _load_json(fixture_path / "state.json"),
        "dependency_graph": _load_json(fixture_path / "dependency_graph.json"),
    }


def build_cli_output(fixture: Path, *, include_prompt: bool, include_validation: bool) -> dict[str, Any]:
    fixture_path = fixture if fixture.is_absolute() else REPO_ROOT / fixture
    replay_payload = build_replay_payload(load_fixture_context(fixture_path))
    output: dict[str, Any] = {
        "replay_payload": replay_payload,
        "source_fixture_path": _repo_relative(fixture_path),
    }

    validation = validate_replay_payload(replay_payload) if include_validation else None
    if validation is not None:
        output["validation"] = validation
    if include_prompt:
        prompt_payload = {**replay_payload}
        if validation is not None:
            prompt_payload["validation"] = validation
        output["prompt_context"] = render_prompt_context(prompt_payload)

    return output


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic MCP context-layer output from a fixture.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE, help="Fixture directory containing trace/state/dependency_graph JSON files.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output.")
    parser.add_argument("--render-prompt", action="store_true", help="Include or emit compact prompt context.")
    parser.add_argument("--validate", action="store_true", help="Include validation/admissibility result.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    output = build_cli_output(args.fixture, include_prompt=args.render_prompt, include_validation=args.validate)

    if args.json or not args.render_prompt:
        sys.stdout.write(json.dumps(output, indent=2, sort_keys=True) + "\n")
        return 0

    prompt_context = output.get("prompt_context")
    if not isinstance(prompt_context, str):
        prompt_context = render_prompt_context(output["replay_payload"])
    sys.stdout.write(prompt_context + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
