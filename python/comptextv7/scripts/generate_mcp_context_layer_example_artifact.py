"""Generate a deterministic MCP context-layer example artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.comptext_v7.mcp import build_replay_payload, render_prompt_context, validate_replay_payload

ARTIFACT_ID = "mcp_context_layer_example_v1"
EXAMPLE_FIXTURE_ID = "mcp_trace_replay_v1"
EXAMPLE_FIXTURE_PATH = REPO_ROOT / "fixtures" / EXAMPLE_FIXTURE_ID / "original"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "mcp_context_layer_example.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_fixture_context() -> dict[str, Any]:
    return {
        "task": EXAMPLE_FIXTURE_ID,
        "trace": _load_json(EXAMPLE_FIXTURE_PATH / "trace.json"),
        "state": _load_json(EXAMPLE_FIXTURE_PATH / "state.json"),
        "dependency_graph": _load_json(EXAMPLE_FIXTURE_PATH / "dependency_graph.json"),
    }


def build_mcp_context_layer_example_artifact() -> dict[str, Any]:
    replay_payload = build_replay_payload(_load_fixture_context())
    validation = validate_replay_payload(replay_payload)
    prompt_context = render_prompt_context({**replay_payload, "validation": validation})

    return {
        "artifact_id": ARTIFACT_ID,
        "evaluation_mode": "deterministic",
        "example": {
            "fixture_id": EXAMPLE_FIXTURE_ID,
            "prompt_context": prompt_context,
            "replay_payload": replay_payload,
            "source_fixture_path": f"fixtures/{EXAMPLE_FIXTURE_ID}/original",
            "validation": validation,
        },
        "external_apis": "none",
        "generated_by": "McpContextLayerExampleArtifactGenerator",
        "llm_judges": "none",
        "schema_version": "mcp_context_layer_example.v1",
        "version": "1.0",
    }


def generate_mcp_context_layer_example_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    artifact = build_mcp_context_layer_example_artifact()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_mcp_context_layer_example_artifact()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
