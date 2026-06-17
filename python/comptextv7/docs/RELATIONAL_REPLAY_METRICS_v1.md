# RELATIONAL_REPLAY_METRICS_v1

## Purpose

This document defines deterministic relational replay metrics for CompTextv7's Relational Survival layer. The scope is limited to explicit dependency graph comparison between an original replay artifact and a reconstructed replay artifact.

This layer is prototype-scoped, serialization-first, and CI-friendly. It is intended to feed future ContractValidator reachability and causality contracts in a follow-up integration PR.

## Non-goals

- no embeddings
- no fuzzy matching
- no LLM judges
- no runtime orchestration

## Metrics

- `dependency_integrity_score`: average of node Jaccard similarity and edge Jaccard similarity.
- `orphan_rate`: fraction of original nodes that had incoming dependencies originally but have zero incoming dependencies in reconstruction.
- `detached_dependency_rate`: fraction of original edges that are missing in reconstruction.
- `temporal_order_violation_rate`: deterministic inversion rate computed from lexical tie-broken topological orders over shared nodes.
- `acyclicity_preserved`: false only when the original graph is acyclic and reconstruction introduces a cycle.
- `reachability_preservation`: preserved original reachable pairs divided by original reachable pairs.
- `causal_preservation_score`: preserved original causal edges divided by original causal edges.

## Failure labels

- `ORPHAN_DEPENDENCY`
- `DETACHED_DEPENDENCY`
- `TEMPORAL_ORDER_VIOLATION`
- `GRAPH_FRAGMENTATION`
- `CYCLE_INTRODUCED`
- `CAUSAL_DEPENDENCY_LOSS`

## Relational Survival positioning

This comparator is deterministic and explicit by design. It does not execute runtime orchestration and does not infer semantics from probabilistic systems. It provides structured relational evidence that can later feed ContractValidator reachability and causality contracts.
