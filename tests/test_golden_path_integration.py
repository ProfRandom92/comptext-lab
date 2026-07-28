"""End-to-end integration test script for CompText P1 Golden Path execution."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
import pytest

def find_ctxt_bin() -> str | None:
    if "COMPTEXT_CLI_BIN" in os.environ:
        cand = Path(os.environ["COMPTEXT_CLI_BIN"])
        if cand.exists():
            return str(cand)

    base_dir = Path(__file__).resolve().parent.parent.parent
    candidates = [
        base_dir / "comptext-cli" / "target" / "debug" / "ctxt.exe",
        base_dir / "comptext-cli" / "target" / "debug" / "ctxt",
        base_dir / "comptext-cli" / "target" / "release" / "ctxt.exe",
        base_dir / "comptext-cli" / "target" / "release" / "ctxt",
    ]
    for cand in candidates:
        if cand.exists() and cand.is_file():
            return str(cand)

    path_bin = shutil.which("ctxt")
    if path_bin:
        return path_bin

    return None

def find_config_path() -> str | None:
    if "COMPTEXT_CONFIG_PATH" in os.environ:
        return os.environ["COMPTEXT_CONFIG_PATH"]

    base_dir = Path(__file__).resolve().parent.parent.parent
    config = base_dir / "comptext-cli" / "comptext.example.toml"
    if config.exists():
        return str(config)
    return None

def test_p1_golden_path_e2e(tmp_path: Path) -> None:
    bin_path = find_ctxt_bin()
    if not bin_path:
        pytest.skip("ctxt binary not available for end-to-end integration test.")

    config_path = find_config_path()
    base_cmd = [bin_path]
    if config_path:
        base_cmd.extend(["--config", config_path])
    base_cmd.append("--json")

    # 1. Paths
    spec_path = tmp_path / "spec.json"
    evidence_path = tmp_path / "evidence.jsonl"
    replay_path = tmp_path / "replay.json"

    # 2. AgentSpec
    spec_data = {
        "contract_name": "agent-spec",
        "schema_version": "v1",
        "agent_spec_id": "lab-e2e-agent",
        "intent": "validate",
        "goal": "Verify full Golden Path end-to-end in comptext-lab",
        "pipeline": ["echo-step"],
        "outputs": [{"kind": "json", "path": "evidence/run.json"}]
    }
    spec_path.write_text(json.dumps(spec_data), encoding="utf-8")

    # 3. Validate AgentSpec via CLI
    val_cmd = base_cmd + ["agent", "validate-spec", str(spec_path)]
    val_res = subprocess.run(val_cmd, capture_output=True, text=True, shell=False)
    assert val_res.returncode == 0, f"stdout={val_res.stdout}, stderr={val_res.stderr}"
    val_data = json.loads(val_res.stdout)
    assert val_data["ok"] is True
    assert val_data["contract_name"] == "agent-spec"

    # 4. Dry-run AgentSpec
    run_cmd = base_cmd + [
        "agent", "dry-run",
        "--spec", str(spec_path),
        "--out-evidence", str(evidence_path),
        "--out-replay", str(replay_path)
    ]
    run_res = subprocess.run(run_cmd, capture_output=True, text=True, shell=False)
    assert run_res.returncode == 0, f"stdout={run_res.stdout}, stderr={run_res.stderr}"
    run_data = json.loads(run_res.stdout)
    assert run_data["ok"] is True
    assert run_data["status"] == "success"
    assert "deterministic_root_hash" in run_data
    assert "execution_chain_hash" in run_data

    assert evidence_path.exists()
    assert replay_path.exists()

    # 5. Replay verification
    replay_cmd = base_cmd + [
        "agent", "replay",
        "--replay", str(replay_path),
        "--evidence", str(evidence_path)
    ]
    replay_res = subprocess.run(replay_cmd, capture_output=True, text=True, shell=False)
    assert replay_res.returncode == 0, f"stdout={replay_res.stdout}, stderr={replay_res.stderr}"
    replay_data = json.loads(replay_res.stdout)
    assert replay_data["ok"] is True
    assert replay_data["verified"] is True
