from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.agent_artifact_bundle as agent_artifact_bundle
from scripts.generate_agent_artifact_bundle_example import (
    ARTIFACT_ID,
    generate_agent_artifact_bundle_example,
)
from scripts.generate_mcp_context_bundle_ref_example import (
    ARTIFACT_ID as MCP_REF_ARTIFACT_ID,
    MCP_CONTEXT_OUTPUT_REF,
    generate_mcp_context_bundle_ref_example,
)
from scripts.safe_pr_gate import GateState, evaluate_gate

ARTIFACT_PATH = Path("artifacts/agent_artifact_bundle_example.json")
MCP_REF_ARTIFACT_PATH = Path("artifacts/mcp_context_bundle_ref_example.json")


def test_build_agent_artifact_bundle_is_deterministic_and_includes_optional_metadata() -> None:
    state = GateState(
        branch="feat/agent-artifact-bundle",
        status_short=(),
        changed_paths=(),
    )

    bundle = agent_artifact_bundle.build_agent_artifact_bundle(
        state,
        allow_main=False,
        validation_commands=["python -m compileall -q scripts/agent_artifact_bundle.py", "pytest tests/test_agent_artifact_bundle.py -q"],
        validation_results=["pass", "pass"],
        mcp_context_output_ref="artifacts/mcp_context_layer_example.json",
    )

    assert bundle == {
        "branch": "feat/agent-artifact-bundle",
        "changed_files": [],
        "mcp_context_output_ref": "artifacts/mcp_context_layer_example.json",
        "ok": True,
        "result": "PASS",
        "safe_pr_gate": evaluate_gate(state).to_dict(),
        "validation_evidence": [
            {
                "command": "python -m compileall -q scripts/agent_artifact_bundle.py",
                "result": "pass",
            },
            {
                "command": "pytest tests/test_agent_artifact_bundle.py -q",
                "result": "pass",
            },
        ],
    }

    first = json.dumps(bundle, indent=2, sort_keys=True)
    second = json.dumps(bundle, indent=2, sort_keys=True)
    assert first == second


def test_build_agent_artifact_bundle_rejects_main_without_allow_main() -> None:
    state = GateState(branch="main", status_short=(), changed_paths=())

    with pytest.raises(RuntimeError, match="main branch is not allowed for agent artifact bundling"):
        agent_artifact_bundle.build_agent_artifact_bundle(
            state,
            allow_main=False,
            validation_commands=[],
            validation_results=[],
        )


def test_build_agent_artifact_bundle_reflects_safe_gate_failure() -> None:
    state = GateState(
        branch="feat/agent-artifact-bundle",
        status_short=(" M docs/example.md",),
        changed_paths=("docs/example.md",),
    )

    bundle = agent_artifact_bundle.build_agent_artifact_bundle(
        state,
        allow_main=False,
        validation_commands=["python -m compileall -q scripts/agent_artifact_bundle.py"],
        validation_results=["pass"],
    )

    assert bundle["ok"] is False
    assert bundle["result"] == "FAIL"
    assert bundle["safe_pr_gate"]["ok"] is False
    assert bundle["safe_pr_gate"]["result"] == "FAIL"


def test_main_emits_deterministic_json_and_omits_optional_reference(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    state = GateState(
        branch="feat/agent-artifact-bundle",
        status_short=(),
        changed_paths=("scripts/agent_artifact_bundle.py",),
    )
    monkeypatch.setattr(agent_artifact_bundle, "collect_gate_state", lambda: state)

    exit_code = agent_artifact_bundle.main(
        [
            "--validation-command",
            "python -m compileall -q scripts/agent_artifact_bundle.py",
            "--validation-result",
            "pass",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output == {
        "branch": "feat/agent-artifact-bundle",
        "changed_files": ["scripts/agent_artifact_bundle.py"],
        "ok": True,
        "result": "PASS",
        "safe_pr_gate": evaluate_gate(state).to_dict(),
        "validation_evidence": [
            {
                "command": "python -m compileall -q scripts/agent_artifact_bundle.py",
                "result": "pass",
            }
        ],
    }
    assert "mcp_context_output_ref" not in output


def test_main_returns_failure_exit_code_when_safe_gate_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = GateState(
        branch="feat/agent-artifact-bundle",
        status_short=(" M docs/example.md",),
        changed_paths=("docs/example.md",),
    )
    monkeypatch.setattr(agent_artifact_bundle, "collect_gate_state", lambda: state)

    exit_code = agent_artifact_bundle.main(
        [
            "--validation-command",
            "python -m compileall -q scripts/agent_artifact_bundle.py",
            "--validation-result",
            "pass",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert output["result"] == "FAIL"
    assert output["safe_pr_gate"]["ok"] is False
    assert output["safe_pr_gate"]["result"] == "FAIL"


def test_main_reports_main_branch_as_deterministic_error_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(agent_artifact_bundle, "collect_gate_state", lambda: GateState(branch="main", status_short=(), changed_paths=()))

    exit_code = agent_artifact_bundle.main([])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output == {
        "error": {
            "message": "main branch is not allowed for agent artifact bundling",
            "type": "RuntimeError",
        },
        "ok": False,
        "result": "ERROR",
    }


def test_agent_artifact_bundle_example_matches_generator_output(tmp_path: Path) -> None:
    output_path = tmp_path / "agent_artifact_bundle_example.json"
    generate_agent_artifact_bundle_example(output_path)

    assert output_path.read_text(encoding="utf-8") == ARTIFACT_PATH.read_text(encoding="utf-8")


def test_agent_artifact_bundle_example_has_stable_schema_and_content() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert set(artifact) == {
        "artifact_id",
        "bundle",
        "evaluation_mode",
        "external_apis",
        "generated_by",
        "llm_judges",
        "schema_version",
        "version",
    }
    assert artifact["artifact_id"] == ARTIFACT_ID
    assert artifact["schema_version"] == "agent_artifact_bundle_example.v1"
    assert artifact["version"] == "1.0"
    assert artifact["evaluation_mode"] == "deterministic"
    assert artifact["external_apis"] == "none"
    assert artifact["llm_judges"] == "none"

    bundle = artifact["bundle"]
    assert bundle["branch"] == "feat/agent-artifact-bundle-example"
    assert bundle["ok"] is True
    assert bundle["result"] == "PASS"
    assert bundle["changed_files"] == [
        "artifacts/agent_artifact_bundle_example.json",
        "scripts/generate_agent_artifact_bundle_example.py",
        "tests/test_agent_artifact_bundle.py",
    ]
    assert bundle["mcp_context_output_ref"] == "artifacts/mcp_context_layer_example.json"
    assert bundle["safe_pr_gate"]["ok"] is True
    assert bundle["safe_pr_gate"]["result"] == "PASS"


def test_mcp_context_bundle_ref_example_matches_generator_output(tmp_path: Path) -> None:
    output_path = tmp_path / "mcp_context_bundle_ref_example.json"
    generate_mcp_context_bundle_ref_example(output_path)

    assert output_path.read_text(encoding="utf-8") == MCP_REF_ARTIFACT_PATH.read_text(encoding="utf-8")


def test_mcp_context_bundle_ref_example_references_mcp_output_without_dumping_payload() -> None:
    artifact = json.loads(MCP_REF_ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert set(artifact) == {
        "artifact_id",
        "bundle",
        "evaluation_mode",
        "external_apis",
        "generated_by",
        "llm_judges",
        "schema_version",
        "version",
    }
    assert artifact["artifact_id"] == MCP_REF_ARTIFACT_ID
    assert artifact["schema_version"] == "mcp_context_bundle_ref_example.v1"
    assert artifact["evaluation_mode"] == "deterministic"
    assert artifact["external_apis"] == "none"
    assert artifact["llm_judges"] == "none"

    bundle = artifact["bundle"]
    assert bundle["branch"] == "feat/mcp-context-bundle-ref-example"
    assert bundle["mcp_context_output_ref"] == MCP_CONTEXT_OUTPUT_REF
    assert bundle["ok"] is True
    assert bundle["result"] == "PASS"
    assert bundle["safe_pr_gate"]["ok"] is True

    artifact_text = MCP_REF_ARTIFACT_PATH.read_text(encoding="utf-8")
    assert "prompt_context" not in artifact_text
    assert "replay_payload" not in artifact_text
    assert "dependency_chains" not in artifact_text
