from __future__ import annotations

import json
from pathlib import Path

import scripts.validate_agent_artifact_bundle as validator

ARTIFACT_PATH = Path("artifacts/agent_artifact_bundle_example.json")


def _valid_bundle() -> dict[str, object]:
    return {
        "branch": "feat/example",
        "changed_files": ["scripts/example.py"],
        "ok": True,
        "result": "PASS",
        "safe_pr_gate": {
            "allow_dirty": False,
            "allowed_prefixes": [],
            "branch": "feat/example",
            "changed_paths": ["scripts/example.py"],
            "ok": True,
            "problems": [],
            "result": "PASS",
            "status_short": [],
        },
        "validation_evidence": [
            {
                "command": "python -m compileall -q scripts/example.py",
                "result": "pass",
            }
        ],
    }


def test_committed_agent_artifact_bundle_example_is_valid() -> None:
    result = validator.validate_bundle_file(ARTIFACT_PATH)

    assert result == {
        "bundle": "artifacts/agent_artifact_bundle_example.json",
        "issues": [],
        "ok": True,
        "result": "PASS",
    }


def test_validator_accepts_raw_bundle_payload() -> None:
    result = validator.validate_bundle_payload(_valid_bundle())

    assert result == {"issues": [], "ok": True, "result": "PASS"}


def test_validator_rejects_result_that_does_not_match_ok() -> None:
    bundle = _valid_bundle()
    bundle["result"] = "FAIL"

    result = validator.validate_bundle_payload(bundle)

    assert result["ok"] is False
    assert result["result"] == "FAIL"
    assert result["issues"] == ["bundle.result must match bundle.ok"]


def test_validator_rejects_safe_gate_status_mismatch() -> None:
    bundle = _valid_bundle()
    safe_pr_gate = bundle["safe_pr_gate"]
    assert isinstance(safe_pr_gate, dict)
    safe_pr_gate["ok"] = False
    safe_pr_gate["result"] = "FAIL"

    result = validator.validate_bundle_payload(bundle)

    assert result["ok"] is False
    assert result["issues"] == ["bundle.ok must match bundle.safe_pr_gate.ok"]


def test_validator_rejects_timestamp_and_random_id_fields() -> None:
    bundle = _valid_bundle()
    bundle["generated_at"] = "2026-01-01T00:00:00Z"
    bundle["run_id"] = "gha:123"
    bundle["uuid"] = "123e4567-e89b-12d3-a456-426614174000"

    result = validator.validate_bundle_payload(bundle)

    assert result["ok"] is False
    assert result["issues"] == [
        "$.generated_at: timestamp-like field is not allowed",
        "$.run_id: random-looking generated id field is not allowed",
        "$.uuid: UUID-like value is not allowed",
        "$.uuid: random-looking generated id field is not allowed",
    ]


def test_validator_rejects_missing_safe_gate_deterministic_field() -> None:
    bundle = _valid_bundle()
    safe_pr_gate = bundle["safe_pr_gate"]
    assert isinstance(safe_pr_gate, dict)
    del safe_pr_gate["status_short"]

    result = validator.validate_bundle_payload(bundle)

    assert result["ok"] is False
    assert result["issues"] == [
        "bundle.safe_pr_gate missing required field: status_short",
        "bundle.safe_pr_gate.status_short must be a list of strings",
    ]


def test_cli_outputs_deterministic_json_for_invalid_bundle(tmp_path: Path, capsys) -> None:
    invalid_path = tmp_path / "invalid_bundle.json"
    invalid_path.write_text(json.dumps({"bundle": {"ok": True, "result": "FAIL"}}, sort_keys=True), encoding="utf-8")

    exit_code = validator.main(["--bundle", str(invalid_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["bundle"] == invalid_path.as_posix()
    assert output["ok"] is False
    assert output["result"] == "FAIL"
    assert output["issues"] == [
        "bundle missing required field: branch",
        "bundle missing required field: changed_files",
        "bundle missing required field: safe_pr_gate",
        "bundle missing required field: validation_evidence",
        "bundle.branch must be a string",
        "bundle.changed_files must be a list of strings",
        "bundle.result must match bundle.ok",
        "bundle.safe_pr_gate must be a JSON object",
        "bundle.validation_evidence must be a list",
    ]
