# Rust Crate Evaluation

This note records crate choices for the current `ctxt` CLI shape. The goal is to keep the tool durable for future Codex runs without adding runtime complexity that weakens the local-first safety model.

## Current Decision

Keep the runtime synchronous for now, but use the current `ureq` API deliberately.

- `tokio`: defer. Tokio is valuable for async network applications, schedulers, timers, async filesystem, and high-concurrency clients. `ctxt` currently performs bounded local filesystem work plus explicit provider calls behind policy gates, so an async runtime would add dependency and execution complexity without improving the core local workflow.
- `ureq`: keep and modernize. The provider path now targets `ureq` 3.x with the `json` feature, a bounded global timeout, `send_json`, and `read_json`. This preserves the blocking local-first model while removing manual JSON body string handling.
- `clap`: good future migration candidate. The hand-written parser is now covered by tests, but `clap` would improve generated help, argument validation, suggested fixes, shell completion paths, and long-term CLI maintainability.
- `anyhow`: good future internal refactor candidate. The code currently uses `Result<T, String>` to control JSON error shape. `anyhow` would help attach richer internal context, but public JSON errors should still be normalized before output.
- `reqwest`: defer unless the provider layer moves to async or needs richer HTTP behavior. If adopted in async mode, it pairs naturally with Tokio; if adopted in blocking mode, compare binary/dependency cost against `ureq`.

## Recommended Order

1. Keep the current optimized synchronous `ureq` 3.x path for Phase 18.
2. Add `clap` only as a deliberate parser migration, with parity tests for every existing command.
3. Add `anyhow` only behind a small error-normalization boundary so JSON stderr remains stable.
4. Add `tokio` and async HTTP only when there is a concrete concurrency requirement, such as parallel artifact uploads, long-running provider streams, live watches, or concurrent provider benchmark runs.

## Evidence Sources

- Tokio describes itself as an async Rust runtime with networking, I/O, timers, filesystem, synchronization, and scheduling facilities: <https://tokio.rs/>
- Clap is the Rust command-line argument parser and documents polished help generation, common argument behavior, suggested fixes, and derive/builder APIs: <https://docs.rs/clap/latest/clap/>
- Anyhow provides an application-oriented error type and context helpers for fallible Rust code: <https://docs.rs/anyhow/latest/anyhow/>
- Reqwest provides HTTP client functionality and supports async usage; introducing it should be tied to provider-layer needs: <https://docs.rs/reqwest/latest/reqwest/>
