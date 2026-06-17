from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.generate_replay_semantic_integrity_artifact import (
    ARTIFACT_ID,
    COMMITMENT_CLASS_ORDER,
    LEVELS,
    _class_for_contract,
    generate_replay_semantic_integrity_artifact,
)
from src.validation.contract_validator import ContractValidator
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

ARTIFACT_PATH = Path("artifacts/replay_semantic_integrity_results.json")
MANIFEST_PATH = Path("fixtures/manifest.json")
EXPECTED_FAMILIES = [
    "coding_workflow_pr_review",
    "incident_response_page_triage",
    "cross_domain_operational_dependency_workflow",
    "mcp_trace_replay",
]
FORBIDDEN_FIELDS = {
    "timestamp",
    "generated_at",
    "environment",
    "hostname",
    "cwd",
    "machine",
    "semantic_similarity",
    "embedding",
    "llm",
    "judge",
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value.keys())
        for nested in value.values():
            keys.update(_walk_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_walk_keys(nested))
    return keys


def _validation_label_union_by_family_and_class() -> dict[str, dict[str, set[str]]]:
    manifest = _load_json(MANIFEST_PATH)
    validator = ContractValidator()
    output: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for fixture_entry in manifest["fixtures"]:
        fixture_path = Path(fixture_entry["path"])
        original: dict[str, Any] = {
            **_load_json(fixture_path / "original/trace.json"),
            **_load_json(fixture_path / "original/state.json"),
            "dependency_graph": _load_json(fixture_path / "original/dependency_graph.json"),
        }
        reconstructed: dict[str, Any] = {
            **_load_json(fixture_path / "reconstructed/trace.json"),
            **_load_json(fixture_path / "reconstructed/state.json"),
            "dependency_graph": _load_json(fixture_path / "reconstructed/dependency_graph.json"),
        }
        contracts_dir = fixture_path / "original/contracts"
        contracts_by_id = {
            contract["contract_id"]: contract for contract in (_load_json(path) for path in sorted(contracts_dir.glob("*.json")))
        }
        contracts = [contracts_by_id[contract_id] for contract_id in fixture_entry["contracts"]]
        results = validator.validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)

        family = fixture_entry["family"]
        for result in results:
            commitment_class = _class_for_contract(result.contract_id, result.contract_type, result.layer)
            if not result.passed and result.failure_label is not None:
                output[family][commitment_class].add(result.failure_label)

    return output


def test_script_output_matches_committed_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "replay_semantic_integrity_results.json"
    generate_replay_semantic_integrity_artifact(output_path)

    assert _load_json(output_path) == _load_json(ARTIFACT_PATH)


def test_artifact_schema_has_no_time_or_environment_fields() -> None:
    payload = _load_json(ARTIFACT_PATH)
    assert payload["artifact_id"] == ARTIFACT_ID

    all_keys = _walk_keys(payload)
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in all_keys


def test_all_required_families_are_represented_in_manifest_order() -> None:
    payload = _load_json(ARTIFACT_PATH)
    families = [entry["family"] for entry in payload["families"]]
    assert families == EXPECTED_FAMILIES


def test_fixture_count_matches_manifest_and_levels_are_deterministic() -> None:
    payload = _load_json(ARTIFACT_PATH)
    manifest = _load_json(MANIFEST_PATH)

    expected_fixture_count = len(manifest["fixtures"])
    assert payload["global_summary"]["fixture_count"] == expected_fixture_count

    for family_payload in payload["families"]:
        assert family_payload["fixture_count"] == 4
        assert family_payload["levels"] == list(LEVELS)


def test_commitment_class_order_is_stable_and_complete() -> None:
    payload = _load_json(ARTIFACT_PATH)

    for family_payload in payload["families"]:
        class_keys = list(family_payload["commitment_classes"].keys())
        assert class_keys == list(COMMITMENT_CLASS_ORDER)


def test_failure_labels_are_registered_and_sorted() -> None:
    payload = _load_json(ARTIFACT_PATH)
    registered_labels = set(FAILURE_TAXONOMY.keys())

    for family_payload in payload["families"]:
        for class_payload in family_payload["commitment_classes"].values():
            labels = class_payload["failure_labels"]
            assert labels == sorted(labels)
            for label in labels:
                assert label in registered_labels


def test_artifact_declares_deterministic_mode_and_no_external_evaluators() -> None:
    payload = _load_json(ARTIFACT_PATH)

    assert payload["evaluation_mode"] == "deterministic"
    assert payload["llm_judges"] == "none"
    assert payload["external_apis"] == "none"
    assert payload["global_summary"]["deterministic_evaluation"] is True
    assert payload["global_summary"]["llm_judges"] == "none"
    assert payload["global_summary"]["external_apis"] == "none"


def test_contract_linked_label_behavior_recovery_and_ordering() -> None:
    payload = _load_json(ARTIFACT_PATH)
    families = {entry["family"]: entry for entry in payload["families"]}

    coding_recovery_labels = set(families["coding_workflow_pr_review"]["commitment_classes"]["recovery_paths"]["failure_labels"])
    assert "POLICY_ORDER_BROKEN" not in coding_recovery_labels
    assert "CAUSAL_DEPENDENCY_LOSS" not in coding_recovery_labels
    assert coding_recovery_labels == {"RECOVERY_PATH_INVALID"}

    cross_domain_order_labels = set(
        families["cross_domain_operational_dependency_workflow"]["commitment_classes"]["governance_or_policy"]["failure_labels"]
    )
    assert cross_domain_order_labels == {"POLICY_ORDER_BROKEN"}


def test_no_class_gets_full_fixture_label_set_without_contract_support() -> None:
    payload = _load_json(ARTIFACT_PATH)
    validation_union = _validation_label_union_by_family_and_class()

    for family_payload in payload["families"]:
        family = family_payload["family"]
        for commitment_class, class_payload in family_payload["commitment_classes"].items():
            artifact_labels = set(class_payload["failure_labels"])
            expected_labels = validation_union.get(family, {}).get(commitment_class, set())
            assert artifact_labels == expected_labels


def test_direct_validation_consistency_for_labels() -> None:
    payload = _load_json(ARTIFACT_PATH)
    validation_union = _validation_label_union_by_family_and_class()

    for family_payload in payload["families"]:
        family = family_payload["family"]
        for commitment_class, class_payload in family_payload["commitment_classes"].items():
            assert set(class_payload["failure_labels"]) == validation_union.get(family, {}).get(commitment_class, set())
