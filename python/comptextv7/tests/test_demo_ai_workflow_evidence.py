from __future__ import annotations

import json

import scripts.demo_ai_workflow_evidence as demo_ai_workflow_evidence


def test_build_demo_summary_runs_committed_evidence_chain() -> None:
    summary = demo_ai_workflow_evidence.build_demo_summary()

    assert summary["ok"] is True
    assert summary["result"] == "PASS"
    assert summary["inputs"] == {
        "agent_artifact_bundle": "artifacts/mcp_context_bundle_ref_example.json",
        "mcp_context_output_ref": "artifacts/mcp_context_layer_example.json",
    }
    assert summary["chain"]["safe_pr_gate"] == {
        "ok": True,
        "problems": [],
        "result": "PASS",
    }
    assert summary["chain"]["validate_agent_artifact_bundle"] == {
        "issues": [],
        "ok": True,
        "result": "PASS",
    }
    assert summary["chain"]["agent_artifact_bundle"]["ok"] is True
    assert summary["chain"]["ai_workflow_snapshot"] == {
        "ok": True,
        "result": "PASS",
    }
    assert summary["chain"]["pr_body_from_agent_bundle"]["section_headings"] == [
        "Summary",
        "Scope",
        "Validation",
        "Safety Gate",
        "Evidence",
    ]


def test_build_demo_summary_is_deterministic_and_lightweight() -> None:
    first = demo_ai_workflow_evidence.build_demo_summary()
    second = demo_ai_workflow_evidence.build_demo_summary()

    first_json = json.dumps(first, separators=(",", ":"), sort_keys=True)
    second_json = json.dumps(second, separators=(",", ":"), sort_keys=True)

    assert first_json == second_json
    assert "prompt_context" not in first_json
    assert "replay_payload" not in first_json
    assert "BEGIN PRIVATE KEY" not in first_json


def test_main_emits_compact_deterministic_json(capsys) -> None:
    exit_code = demo_ai_workflow_evidence.main([])
    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == json.dumps(output, separators=(",", ":"), sort_keys=True) + "\n"
    assert output["ok"] is True
    assert output["result"] == "PASS"
