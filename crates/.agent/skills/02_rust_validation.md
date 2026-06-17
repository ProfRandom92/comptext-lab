# Agent Skill 02 — Rust Validation

This skill lists the commands and code audits required to validate the Rust codebase.

## 1. Quality Gates

Run these commands inside `agy7rust/` in order before submitting:

1. **Formatting:**
   ```bash
   cargo fmt --all --check
   ```
2. **Compilation:**
   ```bash
   cargo check
   ```
3. **Tests:**
   ```bash
   cargo test
   ```
4. **Lints (Warnings as Errors):**
   ```bash
   cargo clippy -- -D warnings
   ```
5. **Demo Check:**
   ```bash
   powershell -File .\demo_spark.ps1
   ```

## 2. Determinism Validation

To guarantee byte-level determinism, compile packages twice and compare their hashes:
```bash
cargo run -- compress -i <input.json> -o determinism_a.spkg
cargo run -- compress -i <input.json> -o determinism_b.spkg
# Compare file hashes:
Get-FileHash determinism_a.spkg
Get-FileHash determinism_b.spkg
```
Both hashes must match identically.

## 3. Code Standards

- **No Unsafe:** Use `#![deny(unsafe_code)]` at crate root.
- **Robust Error Handling:** Avoid `.unwrap()` and `.expect()` in production code. Return `Result<T>` and bubble up errors cleanly using `anyhow` or custom errors.
- **No Side-Effects:** No timestamps, UUID generation, random numbers, or environment variables that alter output bytes. All hashes must be completely deterministic.
