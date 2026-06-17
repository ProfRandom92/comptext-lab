# Contract Validation v1

## Purpose

Contract validation v1 executes deterministic replay contracts against reconstructed artifacts. It is additive and CI-friendly, and it integrates relational graph checks using `DependencyGraphComparator`.

## Supported contract types in v1

- `ordering`
- `reachability`
- `causality`
- `invariant` with predefined rule `no_orphan_dependencies`

## Non-goals

- no DSL
- no arbitrary expressions
- no LLM judges
- no embeddings
- no runtime orchestration

## Relational integration with DependencyGraphComparator

Relational contracts load `original["dependency_graph"]` and `reconstructed["dependency_graph"]` via `DependencyGraph.from_dict()`.

- Reachability contracts:
  - run `DependencyGraphComparator.compare(original_graph, reconstructed_graph)`
  - compute deterministic reachability over `reconstructed_graph.get_edges()`
  - return comparator metrics and failure labels as deterministic evidence

- Causality contracts:
  - check required causal edges against reconstructed graph edges filtered by `RelationType.CAUSAL`
  - if an original graph is provided, run comparator and include metrics/failure labels in evidence

- Invariant contracts (`no_orphan_dependencies`):
  - run comparator
  - fail when comparator failure labels include `ORPHAN_DEPENDENCY`

## Failure mappings

- `POLICY_ORDER_BROKEN` (ordering)
- `RECOVERY_PATH_INVALID` (reachability)
- `CAUSAL_DEPENDENCY_LOSS` (causality)
- `INVARIANT_VIOLATION` (invariant)

## Future

- fixture-level contract bundles
- additional predefined invariants
- layered admissibility scoring
