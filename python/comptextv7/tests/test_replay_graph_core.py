from __future__ import annotations

import pytest

from src.comptext_v7.graph import (
    ReplayGraphDiff,
    adjacency_map,
    compare_edges,
    find_order_violations,
    has_path,
    nodes_from_edges,
    normalize_edges,
    reachable_nodes,
)


def test_normalize_edges_removes_duplicates_and_sorts() -> None:
    edges = [("b", "c"), ("a", "b"), ("b", "c")]
    assert normalize_edges(edges) == (("a", "b"), ("b", "c"))


def test_normalize_edges_rejects_self_loop() -> None:
    with pytest.raises(ValueError):
        normalize_edges([("n1", "n1")])


def test_nodes_from_edges_returns_sorted_nodes() -> None:
    edges = [("b", "c"), ("a", "b")]
    assert nodes_from_edges(edges) == ("a", "b", "c")


def test_adjacency_map_is_deterministic() -> None:
    edges = [("b", "c"), ("a", "b"), ("a", "c")]
    assert adjacency_map(edges) == {
        "a": ("b", "c"),
        "b": ("c",),
        "c": (),
    }


def test_find_order_violations_detects_reversed_and_sorts() -> None:
    sequence = ["c", "b", "a"]
    required = [("a", "b"), ("b", "c"), ("x", "a")]
    assert find_order_violations(sequence, required) == (("a", "b"), ("b", "c"))


def test_find_order_violations_ignores_missing_nodes() -> None:
    sequence = ["a", "b"]
    required = [("x", "b"), ("a", "y")]
    assert find_order_violations(sequence, required) == ()


def test_reachable_nodes_and_path_on_connected_graph() -> None:
    edges = [("a", "b"), ("b", "d"), ("a", "c")]
    assert reachable_nodes(edges, "a") == ("b", "c", "d")
    assert has_path(edges, "a", "d") is True
    assert has_path(edges, "c", "d") is False


def test_reachable_nodes_handles_disconnected_graph() -> None:
    edges = [("a", "b"), ("x", "y")]
    assert reachable_nodes(edges, "a") == ("b",)
    assert reachable_nodes(edges, "z") == ()


def test_reachable_nodes_includes_start_when_cycle_exists() -> None:
    edges = [("a", "b"), ("b", "a")]
    assert reachable_nodes(edges, "a") == ("a", "b")
    assert has_path(edges, "a", "a") is True


def test_compare_edges_detects_edge_and_node_diffs_deterministically() -> None:
    original = [("a", "b"), ("b", "c"), ("d", "e")]
    replay = [("a", "b"), ("b", "d"), ("x", "y")]

    diff = compare_edges(original, replay)

    assert diff == ReplayGraphDiff(
        missing_edges=(("b", "c"), ("d", "e")),
        added_edges=(("b", "d"), ("x", "y")),
        missing_nodes=("c", "e"),
        added_nodes=("x", "y"),
    )
    assert isinstance(diff.missing_edges, tuple)
    assert isinstance(diff.added_nodes, tuple)
