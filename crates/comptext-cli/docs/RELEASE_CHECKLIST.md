# CompText CLI Release Checklist

Use this checklist to verify the stability, security boundaries, and validation requirements before packaging any local release of the CompText CLI (`ctxt`) tool.

## 1. Metadata and Configuration
- [ ] Version in `Cargo.toml` is correct and current (current MVP version: `0.1.0`).
- [ ] `comptext.example.toml` contains clean configuration defaults without any real API keys or sensitive values.
- [ ] All public documentation (`README.md`, `PROJEKT.md`, `docs/MVP_STATUS.md`) is updated to reflect the release scope and version.

## 2. Security Boundaries & Fail-Closed Logic
- [ ] Live network/provider execution is **denied by default** in the config.
- [ ] Ollama and OpenAI-compatible adapters fail closed if network is not explicitly allowed.
- [ ] Exclusions for sensitive paths (e.g., `.env`, `.pem`, `.key`, `id_rsa`) are fully active in `src/cli.rs`.
- [ ] No secrets or keys are stored in the codebase or logged to `stdout`/`stderr`.

## 3. Local Verification Suite
- [ ] Formatting is clean:
  ```bash
  cargo fmt --all --check
  ```
- [ ] Code compiles without errors:
  ```bash
  cargo check
  ```
- [ ] All tests pass successfully:
  ```bash
  cargo test
  ```
- [ ] Clippy lints are clean:
  ```bash
  cargo clippy -- -D warnings
  ```
- [ ] Release target build succeeds:
  ```bash
  cargo build --release
  ```

## 4. Command Smoke Checks
Ensure all key CLI commands function correctly in dry-run/dummy mode:
- [ ] `cargo run --bin ctxt -- --help`
- [ ] `cargo run --bin ctxt -- doctor`
- [ ] `cargo run --bin ctxt -- providers list`
- [ ] `cargo run --bin ctxt -- version`
- [ ] `cargo run --bin ctxt -- validate`

## 5. Git Hygiene Check
- [ ] Runtime assets (in `.comptext/` and `proposals/`) are not tracked or committed in Git.
- [ ] Workspace remains in a clean-tree state after running the test suite:
  ```bash
  git diff --exit-code
  git diff --cached --exit-code
  ```
