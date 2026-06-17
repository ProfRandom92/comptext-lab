# Fixture Template v1

## Purpose

Use this template to create deterministic, additive, CI-friendly replay-validation fixtures for `ContractValidator`.

## Directory structure

```text
fixtures/<fixture_id>/
├── original/
│   ├── trace.json
│   ├── state.json
│   ├── dependency_graph.json
│   └── contracts/
│       └── *.json
├── reconstructed/
│   ├── trace.json
│   ├── state.json
│   └── dependency_graph.json
├── expected/
│   ├── admissibility.json
│   └── failures.json
└── README.md
```

## Required files

- `original/trace.json`: event list used by ordering contract checks (use `events` with `action` keys).
- `original/state.json`: compact deterministic state fields (for example `evidence`, `constraints`, `blockers`, `recovery_paths`, `dependencies`).
- `original/dependency_graph.json`: stable `DependencyGraph.to_dict()` JSON payload.
- `original/contracts/*.json`: one file per contract.
- `reconstructed/trace.json`, `reconstructed/state.json`, `reconstructed/dependency_graph.json`: reconstructed artifacts to validate.
- `expected/admissibility.json`: fixture-level admissibility and must-hold contracts.
- `expected/failures.json`: explicit expected/allowed/disallowed failure label sets.
- `README.md`: fixture scope, workflow, contracts, and expected behavior.

## Contracts folder

Each contract JSON must include:

- `contract_id`
- `layer`
- `type` (`ordering`, `reachability`, `causality`, or `invariant`)
- `definition`
- `severity`

Sort contracts deterministically in tests (for example, by filename).

## dependency_graph.json usage

`dependency_graph.json` must match `DependencyGraph.to_dict()` shape:

- `graph_version`
- `nodes`: list of `{node_id, label, metadata}`
- `edges`: list of `{source, target, relation, metadata}`

Use explicit stable node IDs and deterministic edge lists.

## expected/admissibility.json

Recommended fields:

- `fixture_id`
- `fixture_version`
- `expected_admissible`
- `must_hold_contracts`
- `expected_layer_scores`
- `notes`

## expected/failures.json

Recommended fields:

- `expected_failures`
- `allowed_failures`
- `disallowed_failures`

For positive fixtures, `expected_failures` and `allowed_failures` should be empty arrays.


## Fixture manifest

- All fixture bundles must be listed in `fixtures/manifest.json`.
- The manifest is deterministic and hand-reviewable.
- `fixture_id`, `fixture_version`, `contracts`, `expected_failure_labels`, and `path` must match committed fixture metadata.
- Benchmark artifacts should reference only registered fixtures from the manifest.

## Positive and negative fixtures

- Positive fixtures should pass all must-hold contracts.
- Negative/degraded fixtures should intentionally encode expected failures.
- Expected failure labels must be committed in `expected/failures.json`.
- Negative fixtures are for validating failure detection, not for runtime recovery.

## How fixtures are validated

A fixture validation test should:

1. Load original and reconstructed payload files.
2. Load contracts from `original/contracts/` in deterministic sorted order.
3. Run `ContractValidator().validate_contracts(original, reconstructed, contracts)`.
4. Assert pass/fail outcomes against `expected/admissibility.json` and `expected/failures.json`.
5. Assert deterministic evidence fields needed by relational checks (comparator metrics and labels).

## Non-goals

- no runtime orchestration
- no LLM judges
- no embeddings
- no fuzzy matching
