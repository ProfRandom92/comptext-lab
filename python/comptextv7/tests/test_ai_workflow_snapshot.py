from __future__ import annotations

import json

import pytest

import scripts.ai_workflow_snapshot as ai_workflow_snapshot
from scripts.safe_pr_gate import GateState


def test_build_ai_workflow_snapshot_is_deterministic_and_includes_requested_evidence() -> None:
    state = GateState(
        branch="feat/ai-workflow-snapshot",
        status_short=(),
        changed_paths=("scripts/ai_workflow_snapshot.py",),
    )

    snapshot = ai_workflow_snapshot.build_ai_workflow_snapshot(
        state,
        validation_commands=["python -m compileall -q scripts/ai_workflow_snapshot.py"],
        validation_results=["pass"],
        mcp_context_output_ref="artifacts/mcp_context_layer_example.json",
    )

    assert snapshot["ok"] is True
    assert snapshot["result"] == "PASS"
    assert snapshot["safe_pr_gate"] == snapshot["agent_artifact_bundle"]["safe_pr_gate"]
    assert snapshot["validation_evidence"] == snapshot["agent_artifact_bundle"]["validation_evidence"]
    assert snapshot["mcp_context_output_ref"] == "artifacts/mcp_context_layer_example.json"
    assert snapshot["agent_artifact_bundle"]["mcp_context_output_ref"] == "artifacts/mcp_context_layer_example.json"

    first = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
    second = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
    assert first == second


def test_build_ai_workflow_snapshot_reflects_safe_gate_failure_without_main_error() -> None:
    state = GateState(branch="main", status_short=(), changed_paths=())

    snapshot = ai_workflow_snapshot.build_ai_workflow_snapshot(
        state,
        validation_commands=[],
        validation_results=[],
    )

    assert snapshot["ok"] is False
    assert snapshot["result"] == "FAIL"
    assert snapshot["safe_pr_gate"]["ok"] is False
    assert snapshot["safe_pr_gate"]["result"] == "FAIL"
    assert snapshot["safe_pr_gate"]["problems"] == ["on_main_branch"]


def test_build_ai_workflow_snapshot_omits_optional_mcp_reference() -> None:
    state = GateState(branch="feat/ai-workflow-snapshot", status_short=(), changed_paths=())

    snapshot = ai_workflow_snapshot.build_ai_workflow_snapshot(
        state,
        validation_commands=[],
        validation_results=[],
    )

    assert "mcp_context_output_ref" not in snapshot
    assert "mcp_context_output_ref" not in snapshot["agent_artifact_bundle"]


def test_main_emits_compact_deterministic_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = GateState(
        branch="feat/ai-workflow-snapshot",
        status_short=(),
        changed_paths=("scripts/ai_workflow_snapshot.py",),
    )
    monkeypatch.setattr(ai_workflow_snapshot, "collect_gate_state", lambda: state)

    exit_code = ai_workflow_snapshot.main(
        [
            "--validation-command",
            "python -m compileall -q scripts/ai_workflow_snapshot.py",
            "--validation-result",
            "pass",
        ]
    )
    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == json.dumps(output, separators=(",", ":"), sort_keys=True) + "\n"
    assert output["ok"] is True
    assert output["result"] == "PASS"
    assert "mcp_context_output_ref" not in output


def test_main_returns_failure_exit_code_when_safe_gate_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = GateState(
        branch="feat/ai-workflow-snapshot",
        status_short=(" M docs/example.md",),
        changed_paths=("docs/example.md",),
    )
    monkeypatch.setattr(ai_workflow_snapshot, "collect_gate_state", lambda: state)

    exit_code = ai_workflow_snapshot.main([])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert output["result"] == "FAIL"
    assert output["safe_pr_gate"]["problems"] == ["dirty_working_tree"]


def test_main_reports_validation_mismatch_as_deterministic_error_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = GateState(branch="feat/ai-workflow-snapshot", status_short=(), changed_paths=())
    monkeypatch.setattr(ai_workflow_snapshot, "collect_gate_state", lambda: state)

    exit_code = ai_workflow_snapshot.main(["--validation-command", "pytest tests/test_ai_workflow_snapshot.py -q"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output == {
        "error": {
            "message": "validation command/result count mismatch: 1 command(s), 0 result(s)",
            "type": "RuntimeError",
        },
        "ok": False,
        "result": "ERROR",
    }
