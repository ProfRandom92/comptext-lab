from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

import scripts.safe_pr_gate as safe_pr_gate
from scripts.safe_pr_gate import GateState, _parse_porcelain_paths, evaluate_gate


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_gate(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/safe_pr_gate.py", *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


@contextmanager
def _temporary_git_repo(branch: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir()
        shutil.copy2(REPO_ROOT / "scripts" / "safe_pr_gate.py", scripts_dir / "safe_pr_gate.py")
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "-b", branch], cwd=repo_root, check=True, capture_output=True, text=True)
        yield repo_root


def test_evaluate_gate_passes_on_clean_feature_branch_state() -> None:
    result = evaluate_gate(
        GateState(branch="feat/safe-pr-gate", status_short=(), changed_paths=()),
        allowed_prefixes=("scripts/",),
    )

    assert result.ok is True
    assert result.problems == ()
    assert result.to_dict() == {
        "allowed_prefixes": ["scripts/"],
        "allow_dirty": False,
        "branch": "feat/safe-pr-gate",
        "changed_paths": [],
        "ok": True,
        "problems": [],
        "result": "PASS",
        "status_short": [],
    }


def test_evaluate_gate_fails_on_main_branch() -> None:
    result = evaluate_gate(GateState(branch="main", status_short=(), changed_paths=()))

    assert result.ok is False
    assert result.problems == ("on_main_branch",)


def test_evaluate_gate_allows_detached_head_state() -> None:
    result = evaluate_gate(GateState(branch="", status_short=(), changed_paths=()))

    assert result.ok is True
    assert result.problems == ()


def test_evaluate_gate_fails_on_dirty_tree_without_allow_dirty() -> None:
    result = evaluate_gate(
        GateState(branch="feat/safe-pr-gate", status_short=(" M scripts/example.py",), changed_paths=("scripts/example.py",))
    )

    assert result.ok is False
    assert result.problems == ("dirty_working_tree",)


def test_evaluate_gate_flags_paths_outside_allowed_prefixes() -> None:
    result = evaluate_gate(
        GateState(branch="feat/safe-pr-gate", status_short=(" M docs/example.md",), changed_paths=("docs/example.md",)),
        allow_dirty=True,
        allowed_prefixes=("scripts/",),
    )

    assert result.ok is False
    assert result.problems == ("changed_files_outside_allowed_prefixes", "outside_prefix:docs/example.md")


def test_evaluate_gate_flags_risky_privacy_paths_in_stable_order() -> None:
    result = evaluate_gate(
        GateState(
            branch="feat/safe-pr-gate",
            status_short=(),
            changed_paths=(
                "secrets/id_rsa",
                "config/.env",
                "keys/service.key",
                "certs/client.pem",
            ),
        )
    )

    assert result.ok is False
    assert result.problems == (
        "privacy_risky_path:certs/client.pem",
        "privacy_risky_path:config/.env",
        "privacy_risky_path:keys/service.key",
        "privacy_risky_path:secrets/id_rsa",
    )


def test_evaluate_gate_flags_private_markers_in_changed_text_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "docs" / "example.md"
    binary_path = tmp_path / "docs" / "binary.bin"
    text_path.parent.mkdir()
    text_path.write_text("GITHUB_TOKEN=example\nOPENAI_API_KEY=example\n", encoding="utf-8")
    binary_path.write_bytes(b"\0OPENAI_API_KEY=example")
    monkeypatch.setattr(safe_pr_gate, "REPO_ROOT", tmp_path)

    result = safe_pr_gate.evaluate_gate(
        GateState(
            branch="feat/safe-pr-gate",
            status_short=(),
            changed_paths=("docs/example.md", "docs/binary.bin"),
        )
    )

    assert result.ok is False
    assert result.problems == (
        "privacy_marker:GITHUB_TOKEN=:docs/example.md",
        "privacy_marker:OPENAI_API_KEY=:docs/example.md",
    )


def test_parse_porcelain_paths_handles_rename_status_in_second_position() -> None:
    assert _parse_porcelain_paths(" R old-name.txt\0new-name.txt\0") == ("new-name.txt",)


@pytest.mark.parametrize(
    ("raised", "expected_message"),
    [
        (subprocess.CalledProcessError(1, ["git", "status", "--short"]), "git command failed with exit code 1: git status --short"),
        (FileNotFoundError(), "git executable not found while running: git status --short"),
    ],
)
def test_run_git_wraps_git_subprocess_failures(monkeypatch: pytest.MonkeyPatch, raised: BaseException, expected_message: str) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise raised

    monkeypatch.setattr(safe_pr_gate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match=expected_message):
        safe_pr_gate._run_git(["status", "--short"])


def test_main_reports_deterministic_error_json_on_git_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(safe_pr_gate, "collect_gate_state", lambda: (_ for _ in ()).throw(RuntimeError("git command failed with exit code 1: git status --short")))

    exit_code = safe_pr_gate.main([])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output == {
        "error": {
            "message": "git command failed with exit code 1: git status --short",
            "type": "RuntimeError",
        },
        "ok": False,
        "result": "ERROR",
    }


def test_cli_pass_and_fail_outputs_are_deterministic() -> None:
    with _temporary_git_repo("feat/safe-pr-gate") as repo_root:
        passing = _run_gate(
            "--allow-dirty",
            "--allowed-prefix",
            "docs/",
            "--allowed-prefix",
            "scripts/",
            "--allowed-prefix",
            "tests/",
            cwd=repo_root,
        )
        dirty_path = repo_root / "_safe_pr_gate_dirty_test.tmp"
        dirty_path.write_text("dirty\n", encoding="utf-8")
        try:
            failing = _run_gate(
                "--allow-dirty",
                "--allowed-prefix",
                "docs/",
                "--allowed-prefix",
                "scripts/",
                "--allowed-prefix",
                "tests/",
                cwd=repo_root,
            )
        finally:
            dirty_path.unlink(missing_ok=True)

    assert passing.returncode == 0
    assert failing.returncode == 1

    passing_payload = json.loads(passing.stdout)
    failing_payload = json.loads(failing.stdout)

    assert passing_payload["result"] == "PASS"
    assert passing_payload["allow_dirty"] is True
    assert failing_payload["result"] == "FAIL"
    assert failing_payload["problems"] == [
        "changed_files_outside_allowed_prefixes",
        "outside_prefix:_safe_pr_gate_dirty_test.tmp",
    ]
