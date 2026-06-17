from __future__ import annotations

from src.validation.dependency_graph_comparator import (
    DependencyEdge,
    DependencyGraph,
    DependencyGraphComparator,
    DependencyNode,
    RelationType,
)


def _build_graph(nodes: list[str], edges: list[tuple[str, str, RelationType]]) -> DependencyGraph:
    graph = DependencyGraph()
    for node_id in nodes:
        graph.add_node(DependencyNode(node_id=node_id, label=node_id, metadata=None))
    for source, target, relation in edges:
        graph.add_edge(DependencyEdge(source=source, target=target, relation=relation, metadata=None))
    return graph


def _labels(result) -> set[str]:
    return {failure.label for failure in result.failures}


def test_identical_graphs_have_perfect_scores_and_no_failures() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE), ("B", "C", RelationType.CAUSAL)])
    reconstructed = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE), ("B", "C", RelationType.CAUSAL)])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.dependency_integrity_score == 1.0
    assert result.orphan_rate == 0.0
    assert result.detached_dependency_rate == 0.0
    assert result.acyclicity_preserved is True
    assert result.reachability_preservation == 1.0
    assert result.temporal_order_violation_rate == 0.0
    assert result.causal_preservation_score == 1.0
    assert result.failures == ()


def test_missing_edge_triggers_detached_dependency() -> None:
    original = _build_graph(["A", "B"], [("A", "B", RelationType.PREREQUISITE)])
    reconstructed = _build_graph(["A", "B"], [])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.detached_dependency_rate == 1.0
    assert "DETACHED_DEPENDENCY" in _labels(result)


def test_missing_incoming_edge_triggers_orphan_dependency() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE), ("C", "B", RelationType.DATA_FLOW)])
    reconstructed = _build_graph(["A", "B", "C"], [("A", "C", RelationType.PREREQUISITE)])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.orphan_rate == 1.0 / 3.0
    assert "ORPHAN_DEPENDENCY" in _labels(result)


def test_cycle_introduced_triggers_cycle_failure() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE), ("B", "C", RelationType.PREREQUISITE)])
    reconstructed = _build_graph(
        ["A", "B", "C"],
        [("A", "B", RelationType.PREREQUISITE), ("B", "C", RelationType.PREREQUISITE), ("C", "A", RelationType.PREREQUISITE)],
    )

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.acyclicity_preserved is False
    assert "CYCLE_INTRODUCED" in _labels(result)


def test_reachability_loss_reduces_score_and_triggers_fragmentation() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE), ("B", "C", RelationType.PREREQUISITE)])
    reconstructed = _build_graph(["A", "B", "C"], [("A", "B", RelationType.PREREQUISITE)])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.reachability_preservation < 1.0
    assert "GRAPH_FRAGMENTATION" in _labels(result)


def test_temporal_order_inversion_triggers_violation() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.TEMPORAL), ("A", "C", RelationType.TEMPORAL)])
    reconstructed = _build_graph(["A", "B", "C"], [("B", "A", RelationType.TEMPORAL), ("A", "C", RelationType.TEMPORAL)])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.temporal_order_violation_rate > 0.0
    assert "TEMPORAL_ORDER_VIOLATION" in _labels(result)


def test_causal_edge_loss_reduces_score_and_triggers_causal_failure() -> None:
    original = _build_graph(["A", "B", "C"], [("A", "B", RelationType.CAUSAL), ("B", "C", RelationType.CAUSAL)])
    reconstructed = _build_graph(["A", "B", "C"], [("A", "B", RelationType.CAUSAL)])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.causal_preservation_score == 0.5
    assert "CAUSAL_DEPENDENCY_LOSS" in _labels(result)


def test_failure_evidence_has_deterministic_structured_fields() -> None:
    original = _build_graph(["A", "B"], [("A", "B", RelationType.CAUSAL)])
    reconstructed = _build_graph(["A", "B"], [])

    result = DependencyGraphComparator().compare(original, reconstructed)
    first = result.failures[0]

    assert first.label == "DETACHED_DEPENDENCY"
    assert first.severity == "HIGH"
    assert first.invariant_category == "dependency"
    assert first.affected_nodes == ()
    assert first.affected_edges == (("A", "B", "CAUSAL"),)
    assert first.details == {
        "reason": "original_dependency_edges_missing",
        "missing_edge_count": 1,
        "original_edge_count": 1,
    }


def test_stable_serialization_regardless_of_insertion_order() -> None:
    graph_one = DependencyGraph()
    graph_one.add_node(DependencyNode(node_id="B", label="B", metadata={"z": 1}))
    graph_one.add_node(DependencyNode(node_id="A", label="A", metadata=None))
    graph_one.add_edge(DependencyEdge(source="A", target="B", relation=RelationType.CAUSAL, metadata=None))

    graph_two = DependencyGraph()
    graph_two.add_node(DependencyNode(node_id="A", label="A", metadata={}))
    graph_two.add_node(DependencyNode(node_id="B", label="B", metadata={"z": 1}))
    graph_two.add_edge(DependencyEdge(source="A", target="B", relation=RelationType.CAUSAL, metadata={}))

    assert graph_one.to_dict() == graph_two.to_dict()
    assert DependencyGraph.from_dict(graph_one.to_dict()).to_dict() == graph_one.to_dict()


def test_empty_graphs_are_valid() -> None:
    original = _build_graph([], [])
    reconstructed = _build_graph([], [])

    result = DependencyGraphComparator().compare(original, reconstructed)

    assert result.dependency_integrity_score == 1.0
    assert result.orphan_rate == 0.0
    assert result.detached_dependency_rate == 0.0
    assert result.acyclicity_preserved is True
    assert result.reachability_preservation == 1.0
    assert result.temporal_order_violation_rate == 0.0
    assert result.causal_preservation_score == 1.0
    assert result.failures == ()
