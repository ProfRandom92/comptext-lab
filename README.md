# CompText monorepo

Unified workspace for CompText runtime, SPARK evidence/context tooling, replay-validation research assets, and AIR schemas.

## Layout

- crates/comptext-core — shared Rust core primitives.
- crates/comptext-cli — context/runtime CLI.
- crates/comptext-sparkctl — SPARK evidence/context CLI.
- python/comptextv7 — replay-validation research and benchmark layer.
- air — schemas, contracts, and fixtures.
- docs — migration notes and import decisions.

## Validation

Run:

    cargo fmt --all --check
    cargo check --workspace
    cargo test -p comptext-core
    cargo test -p agy7rust --lib

Full CLI/integration suites include legacy path assumptions and will be stabilized after initial import.
