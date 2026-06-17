from __future__ import annotations

import pytest

from src.validation.contract_validator import ContractValidationError, ContractValidator
from src.validation.dependency_graph_comparator import DependencyEdge, DependencyGraph, DependencyNode, RelationType


def _graph_payload(nodes: list[str], edges: list[tuple[str, str, RelationType]]) -> dict[str, object]:
    graph = DependencyGraph()
    for node_id in nodes:
        graph.add_node(DependencyNode(node_id=node_id, label=node_id, metadata=None))
    for source, target, relation in edges:
        graph.add_edge(DependencyEdge(source=source, target=target, relation=relation, metadata=None))
    return graph.to_dict()


def test_ordering_contract_passes_when_required_sequence_is_subsequence() -> None:
    contract = {
        "contract_id": "pre_merge_review",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["generate_patch", "run_tests", "human_review", "merge"]},
        "severity": "CRITICAL",
    }
    reconstructed = {
        "events": [
            {"action": "setup"},
            {"tool": "generate_patch"},
            {"action": "run_tests"},
            {"tool": "human_review"},
            {"action": "merge"},
        ]
    }

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is True
    assert result.failure_label is None


def test_ordering_contract_fails_with_policy_order_broken_and_evidence() -> None:
    contract = {
        "contract_id": "pre_merge_review",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["generate_patch", "run_tests", "human_review", "merge"]},
        "severity": "CRITICAL",
    }
    reconstructed = {"trace": [{"action": "generate_patch"}, {"action": "human_review"}, {"action": "run_tests"}]}

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "POLICY_ORDER_BROKEN"
    assert result.invariant_category == "ordering"
    assert result.deterministic_evidence["required_sequence"] == ["generate_patch", "run_tests", "human_review", "merge"]
    assert result.deterministic_evidence["observed_sequence"] == ["generate_patch", "human_review", "run_tests"]


def test_ordering_contract_without_failure_label_on_violation_keeps_legacy_default_label() -> None:
    contract = {
        "contract_id": "legacy_ordering_contract",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["validate", "approve", "deploy"]},
        "severity": "CRITICAL",
    }
    reconstructed = {"events": [{"action": "validate"}, {"action": "deploy"}]}

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "POLICY_ORDER_BROKEN"


def test_ordering_contract_with_registered_failure_label_on_violation_emits_configured_label() -> None:
    contract = {
        "contract_id": "configured_ordering_contract",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["validate", "approve", "deploy"]},
        "severity": "CRITICAL",
        "failure_label_on_violation": "APPROVAL_GATE_LOSS",
    }
    reconstructed = {"events": [{"action": "validate"}, {"action": "deploy"}]}

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "APPROVAL_GATE_LOSS"


def test_unregistered_failure_label_on_violation_raises_contract_validation_error() -> None:
    contract = {
        "contract_id": "invalid_failure_label_mapping",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["validate", "approve", "deploy"]},
        "severity": "CRITICAL",
        "failure_label_on_violation": "NOT_A_REGISTERED_LABEL",
    }
    reconstructed = {"events": [{"action": "validate"}, {"action": "deploy"}]}

    with pytest.raises(
        ContractValidationError,
        match="has unregistered failure_label_on_violation: NOT_A_REGISTERED_LABEL",
    ):
        ContractValidator().validate_contract({}, reconstructed, contract)


def test_non_string_failure_label_on_violation_raises_contract_validation_error() -> None:
    contract = {
        "contract_id": "non_string_failure_label_mapping",
        "layer": "operational",
        "type": "ordering",
        "definition": {"required_sequence": ["validate", "approve", "deploy"]},
        "severity": "CRITICAL",
        "failure_label_on_violation": ["APPROVAL_GATE_LOSS"],
    }
    reconstructed = {"events": [{"action": "validate"}, {"action": "deploy"}]}

    with pytest.raises(
        ContractValidationError,
        match=r"has non-string failure_label_on_violation: \['APPROVAL_GATE_LOSS'\]",
    ):
        ContractValidator().validate_contract({}, reconstructed, contract)


def test_reachability_contract_passes_when_target_reachable() -> None:
    contract = {
        "contract_id": "recovery_path_available",
        "layer": "relational",
        "type": "reachability",
        "definition": {"from": "main_workflow_failure", "to": ["rollback", "escalate_to_human"], "min_paths": 1},
        "severity": "HIGH",
    }
    original = {
        "dependency_graph": _graph_payload(
            ["main_workflow_failure", "rollback", "escalate_to_human"],
            [("main_workflow_failure", "rollback", RelationType.RECOVERY)],
        )
    }
    reconstructed = {
        "dependency_graph": _graph_payload(
            ["main_workflow_failure", "rollback", "escalate_to_human"],
            [("main_workflow_failure", "rollback", RelationType.RECOVERY)],
        )
    }

    result = ContractValidator().validate_contract(original, reconstructed, contract)

    assert result.passed is True
    assert result.deterministic_evidence["reachable_targets"] == ["rollback"]


def test_reachability_contract_fails_with_recovery_path_invalid() -> None:
    contract = {
        "contract_id": "recovery_path_available",
        "layer": "relational",
        "type": "reachability",
        "definition": {"from": "main_workflow_failure", "to": ["rollback", "escalate_to_human"], "min_paths": 2},
        "severity": "HIGH",
    }
    original = {
        "dependency_graph": _graph_payload(
            ["main_workflow_failure", "rollback", "escalate_to_human"],
            [
                ("main_workflow_failure", "rollback", RelationType.RECOVERY),
                ("main_workflow_failure", "escalate_to_human", RelationType.RECOVERY),
            ],
        )
    }
    reconstructed = {
        "dependency_graph": _graph_payload(
            ["main_workflow_failure", "rollback", "escalate_to_human"],
            [("main_workflow_failure", "rollback", RelationType.RECOVERY)],
        )
    }

    result = ContractValidator().validate_contract(original, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "RECOVERY_PATH_INVALID"
    assert result.invariant_category == "reachability"


def test_causality_contract_passes_when_required_causal_edge_exists() -> None:
    contract = {
        "contract_id": "causal_failure_blocks_deploy",
        "layer": "relational",
        "type": "causality",
        "definition": {"required_causal_edges": [["security_scan_failed", "deploy_blocked"]]},
        "severity": "HIGH",
    }
    reconstructed = {
        "dependency_graph": _graph_payload(
            ["security_scan_failed", "deploy_blocked"],
            [("security_scan_failed", "deploy_blocked", RelationType.CAUSAL)],
        )
    }

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is True
    assert result.deterministic_evidence["missing_causal_edges"] == []


def test_causality_contract_fails_with_causal_dependency_loss() -> None:
    contract = {
        "contract_id": "causal_failure_blocks_deploy",
        "layer": "relational",
        "type": "causality",
        "definition": {"required_causal_edges": [["security_scan_failed", "deploy_blocked"]]},
        "severity": "HIGH",
    }
    reconstructed = {
        "dependency_graph": _graph_payload(["security_scan_failed", "deploy_blocked"], []),
    }

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "CAUSAL_DEPENDENCY_LOSS"


def test_invariant_no_orphan_dependencies_fails_when_reconstructed_graph_has_orphan() -> None:
    contract = {
        "contract_id": "no_orphan_dependencies",
        "layer": "relational",
        "type": "invariant",
        "definition": {"rule": "no_orphan_dependencies"},
        "severity": "HIGH",
    }
    original = {
        "dependency_graph": _graph_payload(
            ["A", "B", "C"],
            [("A", "B", RelationType.PREREQUISITE), ("C", "B", RelationType.DATA_FLOW)],
        )
    }
    reconstructed = {
        "dependency_graph": _graph_payload(["A", "B", "C"], [("A", "C", RelationType.PREREQUISITE)]),
    }

    result = ContractValidator().validate_contract(original, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "INVARIANT_VIOLATION"


def test_malformed_contract_raises_contract_validation_error() -> None:
    malformed = {
        "contract_id": "bad",
        "layer": "relational",
        "type": "reachability",
        "definition": {"from": "a", "to": ["b"]},
        "severity": "HIGH",
    }

    with pytest.raises(ContractValidationError):
        ContractValidator().validate_contract({"dependency_graph": _graph_payload(["a", "b"], [])}, {"dependency_graph": _graph_payload(["a", "b"], [])}, malformed)


def test_unknown_contract_type_raises_contract_validation_error() -> None:
    contract = {
        "contract_id": "unknown",
        "layer": "relational",
        "type": "unknown_type",
        "definition": {},
        "severity": "HIGH",
    }

    with pytest.raises(ContractValidationError):
        ContractValidator().validate_contract({}, {}, contract)


def test_relational_contract_evidence_contains_comparator_metrics() -> None:
    contract = {
        "contract_id": "recovery_path_available",
        "layer": "relational",
        "type": "reachability",
        "definition": {"from": "main_workflow_failure", "to": ["rollback"], "min_paths": 1},
        "severity": "HIGH",
    }
    payload = _graph_payload(["main_workflow_failure", "rollback"], [("main_workflow_failure", "rollback", RelationType.RECOVERY)])

    result = ContractValidator().validate_contract({"dependency_graph": payload}, {"dependency_graph": payload}, contract)

    assert "comparator_metrics" in result.deterministic_evidence
    metrics = result.deterministic_evidence["comparator_metrics"]
    assert set(metrics.keys()) == {
        "reachability_preservation",
        "dependency_integrity_score",
        "causal_preservation_score",
        "temporal_order_violation_rate",
    }


def test_invariant_required_boundaries_preserved_emits_configured_label_when_boundary_missing() -> None:
    contract = {
        "contract_id": "capability_boundary_respected",
        "layer": "governance",
        "type": "invariant",
        "definition": {
            "rule": "required_boundaries_preserved",
            "required_boundaries": [["human_approval", "execute_external_action"]],
        },
        "severity": "CRITICAL",
        "failure_label_on_violation": "APPROVAL_GATE_LOSS",
    }
    reconstructed = {"state": {"capability_boundaries": []}}

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "APPROVAL_GATE_LOSS"
    assert result.deterministic_evidence["missing_boundaries"] == [["human_approval", "execute_external_action"]]


def test_invariant_required_dependency_edges_preserved_emits_configured_label_when_edge_missing() -> None:
    contract = {
        "contract_id": "dependency_chain_preserved",
        "layer": "relational",
        "type": "invariant",
        "definition": {
            "rule": "required_dependency_edges_preserved",
            "required_edges": [["read_context", "validate_external_action"]],
        },
        "severity": "HIGH",
        "failure_label_on_violation": "DEPENDENCY_CHAIN_BREAK",
    }
    reconstructed = {
        "dependency_graph": _graph_payload(
            ["read_context", "validate_external_action"],
            [],
        )
    }

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is False
    assert result.failure_label == "DEPENDENCY_CHAIN_BREAK"
    assert result.deterministic_evidence["missing_edges"] == [["read_context", "validate_external_action"]]


def test_invariant_required_boundaries_preserved_treats_null_lists_as_empty() -> None:
    contract = {
        "contract_id": "capability_boundary_respected",
        "layer": "governance",
        "type": "invariant",
        "definition": {
            "rule": "required_boundaries_preserved",
            "required_boundaries": None,
        },
        "severity": "CRITICAL",
    }
    reconstructed = {"state": {"capability_boundaries": None}}

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is True
    assert result.failure_label is None


def test_invariant_required_dependency_edges_preserved_treats_null_list_as_empty() -> None:
    contract = {
        "contract_id": "dependency_chain_preserved",
        "layer": "relational",
        "type": "invariant",
        "definition": {
            "rule": "required_dependency_edges_preserved",
            "required_edges": None,
        },
        "severity": "HIGH",
    }
    reconstructed = {
        "dependency_graph": _graph_payload(["read_context", "validate_external_action"], []),
    }

    result = ContractValidator().validate_contract({}, reconstructed, contract)

    assert result.passed is True
    assert result.failure_label is None


def test_invariant_required_lists_reject_non_list_values() -> None:
    bad_boundaries = {
        "contract_id": "capability_boundary_respected",
        "layer": "governance",
        "type": "invariant",
        "definition": {"rule": "required_boundaries_preserved", "required_boundaries": "not-a-list"},
        "severity": "CRITICAL",
    }
    with pytest.raises(RuntimeError, match="requires definition.required_boundaries as list"):
        ContractValidator().validate_contract({}, {"state": {"capability_boundaries": []}}, bad_boundaries)

    bad_capability_boundaries = {
        "contract_id": "capability_boundary_respected",
        "layer": "governance",
        "type": "invariant",
        "definition": {"rule": "required_boundaries_preserved", "required_boundaries": []},
        "severity": "CRITICAL",
    }
    with pytest.raises(RuntimeError, match="requires reconstructed capability_boundaries as list"):
        ContractValidator().validate_contract({}, {"state": {"capability_boundaries": "not-a-list"}}, bad_capability_boundaries)

    bad_edges = {
        "contract_id": "dependency_chain_preserved",
        "layer": "relational",
        "type": "invariant",
        "definition": {"rule": "required_dependency_edges_preserved", "required_edges": "not-a-list"},
        "severity": "HIGH",
    }
    with pytest.raises(RuntimeError, match="requires definition.required_edges as list"):
        ContractValidator().validate_contract(
            {},
            {"dependency_graph": _graph_payload(["read_context", "validate_external_action"], [])},
            bad_edges,
        )
