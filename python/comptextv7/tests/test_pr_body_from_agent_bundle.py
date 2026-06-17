from __future__ import annotations

import json
from pathlib import Path

import scripts.pr_body_from_agent_bundle as pr_body
from scripts.generate_pr_body_from_agent_bundle_example import generate_pr_body_from_agent_bundle_example

ARTIFACT_PATH = Path("artifacts/agent_artifact_bundle_example.json")
PR_BODY_ARTIFACT_PATH = Path("artifacts/pr_body_from_agent_bundle_example.md")


def test_render_pr_body_from_committed_bundle_is_deterministic() -> None:
    first = pr_body.render_pr_body_from_file(ARTIFACT_PATH)
    second = pr_body.render_pr_body_from_file(ARTIFACT_PATH)

    assert first == second
    assert first == "\n".join(
        [
            "## Summary",
            "",
            "Deterministic agent artifact bundle evidence for this change.",
            "",
            "## Scope",
            "",
            "- `artifacts/agent_artifact_bundle_example.json`",
            "- `scripts/generate_agent_artifact_bundle_example.py`",
            "- `tests/test_agent_artifact_bundle.py`",
            "",
            "## Validation",
            "",
            "- `python -m compileall -q scripts/agent_artifact_bundle.py scripts/generate_agent_artifact_bundle_example.py`: `pass`",
            "- `pytest tests/test_agent_artifact_bundle.py -q`: `pass`",
            "",
            "## Safety Gate",
            "",
            "- result: `PASS`",
            "- ok: `true`",
            "- allow_dirty: `false`",
            "- problems: `none`",
            "",
            "## Evidence",
            "",
            "- branch: `feat/agent-artifact-bundle-example`",
            "- bundle_result: `PASS`",
            "- mcp_context_output_ref: `artifacts/mcp_context_layer_example.json`",
            "",
        ]
    )


def test_render_pr_body_uses_only_bundle_validation_evidence() -> None:
    bundle = {
        "branch": "feat/no-validation",
        "changed_files": [],
        "ok": True,
        "result": "PASS",
        "safe_pr_gate": {
            "allow_dirty": False,
            "allowed_prefixes": [],
            "branch": "feat/no-validation",
            "changed_paths": [],
            "ok": True,
            "problems": [],
            "result": "PASS",
            "status_short": [],
        },
        "validation_evidence": [],
    }

    rendered = pr_body.render_pr_body_from_payload(bundle)

    assert "- No validation evidence provided in bundle." in rendered
    assert "pytest" not in rendered


def test_render_pr_body_rejects_invalid_bundle_without_markdown() -> None:
    invalid = {
        "branch": "feat/bad",
        "changed_files": [],
        "ok": True,
        "result": "FAIL",
        "safe_pr_gate": {
            "allow_dirty": False,
            "allowed_prefixes": [],
            "branch": "feat/bad",
            "changed_paths": [],
            "ok": True,
            "problems": [],
            "result": "PASS",
            "status_short": [],
        },
        "validation_evidence": [],
    }

    try:
        pr_body.render_pr_body_from_payload(invalid)
    except RuntimeError as exc:
        assert "bundle.result must match bundle.ok" in str(exc)
    else:
        raise AssertionError("expected invalid bundle to raise RuntimeError")


def test_cli_outputs_markdown_only_for_valid_bundle(tmp_path: Path, capsys) -> None:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    exit_code = pr_body.main(["--bundle", str(bundle_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.startswith("## Summary\n")
    assert "## Safety Gate\n" in captured.out


def test_pr_body_example_artifact_matches_generator_output(tmp_path: Path) -> None:
    output_path = tmp_path / "pr_body_from_agent_bundle_example.md"
    generate_pr_body_from_agent_bundle_example(output_path)

    assert output_path.read_text(encoding="utf-8") == PR_BODY_ARTIFACT_PATH.read_text(encoding="utf-8")
