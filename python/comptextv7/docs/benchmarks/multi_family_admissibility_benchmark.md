# Deterministic Multi-Family Admissibility Benchmark

## Purpose

The deterministic multi-family admissibility benchmark tracks operational admissibility degradation across fixture families registered in the manifest.

Each manifest-registered fixture family contributes one deterministic degradation curve using the same standard levels, so contributors can compare progression behavior across families without changing scoring rules or artifact shape.

## Pipeline

```mermaid
flowchart LR
    A[fixtures/manifest.json]
    B[DegradationCurveGenerator.fixtures_for_manifest_family(...)]
    C[AdmissibilityScorer]
    D[artifacts/multi_family_admissibility_results.json]
    E[Reproducibility and progression tests]

    A --> B --> C --> D --> E
```

### Pipeline notes

1. `fixtures/manifest.json` is the source of truth for which fixture families participate.
2. `DegradationCurveGenerator.fixtures_for_manifest_family(...)` resolves fixtures for each family from manifest registration.
3. `AdmissibilityScorer` computes exact admissibility component outcomes for each level.
4. Results are written to `artifacts/multi_family_admissibility_results.json` in a stable deterministic JSON layout.
5. Reproducibility and progression tests validate that the committed artifact remains consistent and semantically protected.

## Current fixture families

The current multi-family benchmark includes these manifest-registered families:

- `coding_workflow_pr_review`
- `incident_response_page_triage`

## Standard degradation levels

Every included family is evaluated at exactly four standard levels in explicit order:

1. `baseline`
2. `mild`
3. `moderate`
4. `severe`

## Determinism guarantees

The benchmark is designed to remain deterministic across local runs and CI runs:

- manifest-driven family selection
- explicit level order (`baseline`, `mild`, `moderate`, `severe`)
- exact rational score aggregation
- stable JSON output structure and ordering
- no timestamps or environment-dependent fields

## Regeneration commands

Use either command to regenerate the deterministic multi-family artifact:

```bash
python scripts/generate_multi_family_admissibility_artifact.py
```

```bash
npm run generate:multi-family-admissibility
```

## Deterministic SVG rendering

The benchmark also includes a deterministic SVG rendering step:

- Input: `artifacts/multi_family_admissibility_results.json`
- Output: `artifacts/multi_family_admissibility_curves.svg`
- Script: `scripts/render_multi_family_admissibility_svg.py`
- npm command: `npm run generate:multi-family-svg`

The SVG output is deterministic by design with fixed dimensions, fixed axes, fixed degradation level order, lexicographic family order, a hardcoded palette, no timestamps, no generated IDs, and no embedded JavaScript.

## Validation commands

Run the targeted protections plus the repository-wide check entrypoint:

```bash
pytest tests/test_multi_family_admissibility_artifact.py -q
pytest tests/test_artifact_reproducibility.py -q
pytest tests/test_manifest_fixture_families.py -q
pytest tests/test_multi_family_svg_renderer.py -q
npm run check
```

## Regression protections

The benchmark is protected by deterministic regression checks that enforce:

- committed artifact must match regenerated output
- every family must expose all four standard levels
- baseline and severe behavior is explicitly checked
- mild and moderate behavior must be distinct
- degradation must be progressive:
  - `baseline > mild >= moderate > severe`

## Non-goals

This benchmark intentionally excludes:

- LLM judging
- embeddings
- fuzzy semantic similarity
- runtime orchestration
- deployment/showcase dependencies
