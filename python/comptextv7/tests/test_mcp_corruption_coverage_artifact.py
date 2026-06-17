from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.generate_mcp_corruption_coverage_artifact import (
    OUTPUT_PATH,
    generate_mcp_corruption_coverage_artifact,
)
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_mcp_corruption_coverage_artifact.py"


def _load_artifact() -> dict[str, object]:
    return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))


def test_committed_artifact_matches_regenerated_output(tmp_path: Path) -> None:
    committed = _load_artifact()
    regenerated = generate_mcp_corruption_coverage_artifact(tmp_path / "mcp_corruption_coverage.json")
    assert committed == regenerated


def test_repeated_generation_is_stable(tmp_path: Path) -> None:
    first = generate_mcp_corruption_coverage_artifact(tmp_path / "first.json")
    second = generate_mcp_corruption_coverage_artifact(tmp_path / "second.json")
    assert first == second


def test_summary_and_distribution_values() -> None:
    artifact = _load_artifact()
    summary = artifact["coverage_summary"]

    assert summary == {
        "total_corruptions": 18,
        "native_contract_covered": 18,
        "adapter_gaps": 0,
        "operator_count": 6,
        "fixture_family_count": 3,
        "failure_label_count": 6,
        "coverage_ratio": 1.0,
    }

    assert artifact["operator_coverage"] == {
        "COLLAPSE_CAPABILITY_BOUNDARY": 3,
        "DROP_APPROVAL_GATE": 3,
        "INSERT_UNVALIDATED_ACTION": 3,
        "REMOVE_DEPENDENCY_EDGE": 3,
        "SWAP_TOOL_ORDER": 3,
        "TRUNCATE_RECOVERY_PATH": 3,
    }
    assert artifact["fixture_family_coverage"] == {
        "mcp_trace_replay_degraded_v1": 6,
        "mcp_trace_replay_mild_v1": 6,
        "mcp_trace_replay_moderate_v1": 6,
    }
    assert artifact["failure_label_coverage"] == {
        "APPROVAL_GATE_LOSS": 3,
        "CAPABILITY_BOUNDARY_LOSS": 3,
        "DEPENDENCY_CHAIN_BREAK": 3,
        "POLICY_ENFORCEMENT_GAP": 3,
        "RECOVERY_PATH_INVALID": 3,
        "TOOL_ORDER_VIOLATION": 3,
    }


def test_per_entry_coverage_invariants_and_taxonomy_registration() -> None:
    artifact = _load_artifact()
    entries = artifact["entries"]
    assert isinstance(entries, list)
    assert len(entries) == 18

    operators: Counter[str] = Counter()
    families: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    for entry in entries:
        assert entry["native_contract_covered"] is True
        assert entry["adapter_gap"] is False
        expected_label = entry["expected_failure_label"]
        observed = entry["observed_failure_labels"]
        assert expected_label in observed
        assert expected_label in FAILURE_TAXONOMY
        operators[entry["operator"]] += 1
        families[Path(entry["source_fixture"]).name] += 1
        labels[expected_label] += 1

    assert all(count == 3 for count in operators.values())
    assert all(count == 6 for count in families.values())
    assert all(count == 3 for count in labels.values())


def test_artifact_contains_no_absolute_paths_or_timestamps() -> None:
    text = OUTPUT_PATH.read_text(encoding="utf-8")
    assert str(REPO_ROOT) not in text
    assert '"timestamp"' not in text


def test_generator_fails_when_expected_label_not_emitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "scripts.generate_mcp_corruption_coverage_artifact.ContractValidator.validate_contracts",
        lambda *args, **kwargs: [],
    )

    with pytest.raises(RuntimeError, match="adapter gap detected"):
        generate_mcp_corruption_coverage_artifact(tmp_path / "negative.json")
