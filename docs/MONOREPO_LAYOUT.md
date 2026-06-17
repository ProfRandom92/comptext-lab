# Monorepo layout

comptext/
  crates/
    comptext-core/
    comptext-cli/
    comptext-sparkctl/
  python/
    comptextv7/
  air/
  docs/
  examples/
  schemas/
  artifacts/

## Package roles

- comptext-core: shared Rust primitives for hashing, canonical data, runtime safety, and future SPARK/context extraction.
- comptext-cli: user-facing context/runtime CLI imported from pr-5-runtime-autonomy.
- comptext-sparkctl: SPARK/evidence/context CLI imported from current main.
- python/comptextv7: deterministic replay-validation and research/benchmark layer.
- air: schemas/contracts/spec fixtures.

## Known migration debt

- comptext-sparkctl still contains repo-relative ../examples, ../schemas, and ../artifacts assumptions.
- comptext-core is only seeded; shared code extraction is still pending.
- comptext-cli has one brittle provenance path assertion after monorepo import.
- Python/Node validation for Comptextv7 requires dashboard Node dependencies before full pytest -q.
