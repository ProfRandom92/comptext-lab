from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.comptext_v7.mcp import (
    ContextStore,
    build_replay_payload,
    load_context,
    render_prompt_context,
    save_context,
    validate_replay_payload,
)
from scripts.generate_mcp_context_layer_example_artifact import (
    ARTIFACT_ID,
    EXAMPLE_FIXTURE_ID,
    generate_mcp_context_layer_example_artifact,
)
from scripts.mcp_context_cli import REPO_ROOT, _load_json


FIXTURE_ROOT = Path("fixtures/mcp_trace_replay_v1/original")
ARTIFACT_PATH = Path("artifacts/mcp_context_layer_example.json")
CLI_PATH = Path("scripts/mcp_context_cli.py")
TOOL_PATH = Path("scripts/mcp_context_tool.py")


def _load_fixture_context() -> dict[str, object]:
    return {
        "task": "mcp_trace_replay_v1",
        "trace": json.loads((FIXTURE_ROOT / "trace.json").read_text(encoding="utf-8")),
        "state": json.loads((FIXTURE_ROOT / "state.json").read_text(encoding="utf-8")),
        "dependency_graph": json.loads((FIXTURE_ROOT / "dependency_graph.json").read_text(encoding="utf-8")),
    }


def test_build_replay_payload_extracts_ordered_operational_commitments() -> None:
    payload = build_replay_payload(_load_fixture_context())

    assert payload == {
        "task": "mcp_trace_replay_v1",
        "constraints": [
            "execute_external_action:requires_human_approval",
            "execute_external_action:requires_validation_passed",
        ],
        "required_order": [
            "user_request_received",
            "capability_scope_checked",
            "tool_schema_validated",
            "read_context",
            "validate_external_action",
            "execute_external_action",
            "verify_result",
            "recovery_path_registered",
        ],
        "blockers": [["capability_scope_checked", "execute_external_action"]],
        "dependency_chains": [
            ["capability_scope_checked", "execute_external_action"],
            ["capability_scope_checked", "tool_schema_validated"],
            ["capability_scope_checked", "validate_external_action"],
            ["execute_external_action", "recovery_path_registered"],
            ["execute_external_action", "verify_result"],
            ["read_context", "validate_external_action"],
            ["tool_schema_validated", "read_context"],
            ["user_request_received", "capability_scope_checked"],
            ["validate_external_action", "execute_external_action"],
        ],
        "recovery": [["execute_external_action", "recovery_path_registered"]],
    }


def test_validate_replay_payload_accepts_fixture_payload() -> None:
    payload = build_replay_payload(_load_fixture_context())

    result = validate_replay_payload(payload)

    assert result["admissible"] is True
    assert result["failure_labels"] == []
    assert result["issues"] == []


def test_validate_replay_payload_detects_deterministic_corruptions() -> None:
    payload = build_replay_payload(_load_fixture_context())
    payload["constraints"] = []
    payload["required_order"] = [
        "execute_external_action",
        "validate_external_action",
        "verify_result",
    ]
    payload["dependency_chains"] = [
        ["validate_external_action", "execute_external_action"],
        ["read_context", "validate_external_action"],
    ]
    payload["recovery"] = []

    result = validate_replay_payload(payload)

    assert result["admissible"] is False
    assert result["failure_labels"] == [
        "CONSTRAINT_DRIFT",
        "DEPENDENCY_CHAIN_BREAK",
        "RECOVERY_PATH_LOSS",
        "TOOL_ORDER_VIOLATION",
    ]
    assert result["issues"] == [
        {
            "field": "constraints",
            "failure_label": "CONSTRAINT_DRIFT",
            "message": "payload has no preserved constraints",
        },
        {
            "field": "required_order",
            "failure_label": "TOOL_ORDER_VIOLATION",
            "message": "required order violates dependency edges",
            "evidence": [["validate_external_action", "execute_external_action"]],
        },
        {
            "field": "dependency_chains",
            "failure_label": "DEPENDENCY_CHAIN_BREAK",
            "message": "dependency edges reference actions absent from required_order",
            "evidence": [["read_context", "validate_external_action"]],
        },
        {
            "field": "recovery",
            "failure_label": "RECOVERY_PATH_LOSS",
            "message": "payload has no preserved recovery paths",
        },
    ]


def test_context_store_persists_compact_payload_by_task(tmp_path: Path) -> None:
    store = ContextStore(tmp_path)
    saved = store.save_context(_load_fixture_context())

    assert saved.task == "mcp_trace_replay_v1"
    assert store.load_context("mcp_trace_replay_v1") == saved.payload


def test_module_level_save_load_requires_configured_store(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not configured"):
        load_context("missing")

    saved = save_context(_load_fixture_context(), store_dir=tmp_path)

    assert load_context("mcp_trace_replay_v1", store_dir=tmp_path) == saved.payload


def test_render_prompt_context_is_deterministic_and_token_light() -> None:
    payload = build_replay_payload(_load_fixture_context())
    payload["objective"] = "continue replay validation"
    payload["validation"] = validate_replay_payload(payload)

    rendered = render_prompt_context(payload)

    assert rendered == "\n".join(
        [
            "task: mcp_trace_replay_v1",
            "objective: continue replay validation",
            "admissible: true",
            "constraints:",
            "- execute_external_action:requires_human_approval",
            "- execute_external_action:requires_validation_passed",
            "required_order:",
            "- user_request_received",
            "- capability_scope_checked",
            "- tool_schema_validated",
            "- read_context",
            "- validate_external_action",
            "- execute_external_action",
            "- verify_result",
            "- recovery_path_registered",
            "dependencies:",
            "- capability_scope_checked -> execute_external_action",
            "- capability_scope_checked -> tool_schema_validated",
            "- capability_scope_checked -> validate_external_action",
            "- execute_external_action -> recovery_path_registered",
            "- execute_external_action -> verify_result",
            "- read_context -> validate_external_action",
            "- tool_schema_validated -> read_context",
            "- user_request_received -> capability_scope_checked",
            "- validate_external_action -> execute_external_action",
            "blockers:",
            "- capability_scope_checked -> execute_external_action",
            "recovery:",
            "- execute_external_action -> recovery_path_registered",
        ]
    )
    assert "events" not in rendered
    assert "dependency_graph" not in rendered
    assert "permission_scopes" not in rendered


def test_render_prompt_context_omits_empty_fields_consistently() -> None:
    rendered = render_prompt_context(
        {
            "task": "minimal_task",
            "constraints": [],
            "required_order": ["validate", "deploy"],
            "dependency_chains": [],
            "blockers": [],
            "recovery": [],
        }
    )

    assert rendered == "\n".join(
        [
            "task: minimal_task",
            "required_order:",
            "- validate",
            "- deploy",
        ]
    )


def test_render_prompt_context_includes_validation_status_only_when_present() -> None:
    payload = {
        "task": "failed_task",
        "required_order": ["deploy", "validate"],
        "dependency_chains": [["validate", "deploy"]],
        "validation": {
            "admissible": False,
            "failure_labels": ["TOOL_ORDER_VIOLATION"],
        },
    }

    rendered = render_prompt_context(payload)

    assert rendered.splitlines()[:3] == [
        "task: failed_task",
        "admissible: false",
        "failures: TOOL_ORDER_VIOLATION",
    ]
    assert "issues" not in rendered


def test_mcp_context_layer_artifact_matches_generator_output(tmp_path: Path) -> None:
    output_path = tmp_path / "mcp_context_layer_example.json"
    generate_mcp_context_layer_example_artifact(output_path)

    assert output_path.read_text(encoding="utf-8") == ARTIFACT_PATH.read_text(encoding="utf-8")


def test_mcp_context_layer_artifact_has_stable_schema_and_content() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert set(artifact.keys()) == {
        "artifact_id",
        "evaluation_mode",
        "example",
        "external_apis",
        "generated_by",
        "llm_judges",
        "schema_version",
        "version",
    }
    assert artifact["artifact_id"] == ARTIFACT_ID
    assert artifact["schema_version"] == "mcp_context_layer_example.v1"
    assert artifact["version"] == "1.0"
    assert artifact["evaluation_mode"] == "deterministic"
    assert artifact["llm_judges"] == "none"
    assert artifact["external_apis"] == "none"

    example = artifact["example"]
    assert example["fixture_id"] == EXAMPLE_FIXTURE_ID
    assert example["source_fixture_path"] == "fixtures/mcp_trace_replay_v1/original"
    assert example["validation"] == {
        "admissible": True,
        "failure_labels": [],
        "issues": [],
    }
    assert example["replay_payload"] == build_replay_payload(_load_fixture_context())
    assert example["prompt_context"] == render_prompt_context(
        {
            **example["replay_payload"],
            "validation": example["validation"],
        }
    )


def test_mcp_context_layer_artifact_excludes_raw_trace_state_and_graph() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")

    assert '"events"' not in artifact_text
    assert '"state_version"' not in artifact_text
    assert '"graph_version"' not in artifact_text
    assert '"dependency_graph"' not in artifact_text
    assert '"permission_scopes"' not in artifact_text


def _run_cli(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _run_tool(request: dict[str, object], *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *args],
        input=json.dumps(request, sort_keys=True),
        check=check,
        capture_output=True,
        text=True,
    )


def test_mcp_context_cli_json_output_is_deterministic() -> None:
    args = (
        "--fixture",
        str(FIXTURE_ROOT),
        "--json",
        "--render-prompt",
        "--validate",
    )

    first = _run_cli(*args)
    second = _run_cli(*args)

    assert first == second
    assert first.endswith("\n")
    payload = json.loads(first)
    assert set(payload.keys()) == {
        "prompt_context",
        "replay_payload",
        "source_fixture_path",
        "validation",
    }
    assert payload["source_fixture_path"] == "fixtures/mcp_trace_replay_v1/original"
    assert payload["replay_payload"] == build_replay_payload(_load_fixture_context())
    assert payload["validation"] == validate_replay_payload(payload["replay_payload"])
    assert payload["prompt_context"] == render_prompt_context(
        {
            **payload["replay_payload"],
            "validation": payload["validation"],
        }
    )


def test_mcp_context_cli_prompt_output_is_compact_and_deterministic() -> None:
    args = (
        "--fixture",
        str(FIXTURE_ROOT),
        "--render-prompt",
        "--validate",
    )

    first = _run_cli(*args)
    second = _run_cli(*args)

    assert first == second
    assert first == render_prompt_context(
        {
            **build_replay_payload(_load_fixture_context()),
            "validation": validate_replay_payload(build_replay_payload(_load_fixture_context())),
        }
    ) + "\n"
    assert "events" not in first
    assert "dependency_graph" not in first
    assert "permission_scopes" not in first


def test_mcp_context_cli_payload_json_excludes_raw_trace_state_and_graph() -> None:
    output = _run_cli("--fixture", str(FIXTURE_ROOT), "--json")

    assert '"events"' not in output
    assert '"state_version"' not in output
    assert '"graph_version"' not in output
    assert '"dependency_graph"' not in output
    assert '"permission_scopes"' not in output
    payload = json.loads(output)
    assert set(payload.keys()) == {"replay_payload", "source_fixture_path"}


def test_mcp_context_cli_load_json_reports_repo_relative_missing_path() -> None:
    missing_path = REPO_ROOT / "fixtures" / "mcp_trace_replay_v1" / "original" / "missing.json"

    with pytest.raises(RuntimeError) as excinfo:
        _load_json(missing_path)

    assert str(excinfo.value) == "missing required fixture file: fixtures/mcp_trace_replay_v1/original/missing.json"


def test_mcp_context_cli_load_json_reports_invalid_json(tmp_path: Path) -> None:
    invalid_path = tmp_path / "trace.json"
    invalid_path.write_text("{invalid-json", encoding="utf-8")

    with pytest.raises(RuntimeError) as excinfo:
        _load_json(invalid_path)

    assert str(excinfo.value).startswith(f"invalid JSON in fixture file: {invalid_path.as_posix()}:")


def test_mcp_context_cli_load_json_requires_json_object(tmp_path: Path) -> None:
    list_path = tmp_path / "trace.json"
    list_path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(RuntimeError) as excinfo:
        _load_json(list_path)

    assert str(excinfo.value) == f"fixture file must contain a JSON object: {list_path.as_posix()}"


def test_mcp_context_tool_build_request_is_deterministic() -> None:
    request = {
        "tool": "build_replay_payload",
        "params": {
            "fixture": str(FIXTURE_ROOT),
            "render_prompt": True,
            "validate": True,
        },
    }

    first = _run_tool(request).stdout
    second = _run_tool(request).stdout

    assert first == second
    assert first.endswith("\n")
    response = json.loads(first)
    assert set(response.keys()) == {"ok", "result", "tool"}
    assert response["ok"] is True
    assert response["tool"] == "build_replay_payload"

    result = response["result"]
    assert result["payload"] == build_replay_payload(_load_fixture_context())
    assert result["validation"] == validate_replay_payload(result["payload"])
    assert result["prompt_context"] == render_prompt_context(
        {
            **result["payload"],
            "validation": result["validation"],
        }
    )
    assert '"events"' not in first
    assert '"dependency_graph"' not in first
    assert '"permission_scopes"' not in first


def test_mcp_context_tool_request_file_validate_payload(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    payload = build_replay_payload(_load_fixture_context())
    request_path.write_text(
        json.dumps(
            {
                "tool": "validate_replay_payload",
                "params": {"payload": payload},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--request-file", str(request_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "ok": True,
        "result": {
            "validation": {
                "admissible": True,
                "failure_labels": [],
                "issues": [],
            }
        },
        "tool": "validate_replay_payload",
    }


def test_mcp_context_tool_invalid_request_returns_deterministic_error() -> None:
    request = {
        "tool": "build_replay_payload",
        "params": {"fixture": "fixtures/mcp_trace_replay_v1/original/missing"},
    }

    completed = _run_tool(request, check=False)

    assert completed.returncode == 1
    assert completed.stderr == ""
    assert json.loads(completed.stdout) == {
        "error": {
            "message": "missing required fixture file: fixtures/mcp_trace_replay_v1/original/missing/trace.json",
            "type": "RuntimeError",
        },
        "ok": False,
        "tool": "build_replay_payload",
    }
