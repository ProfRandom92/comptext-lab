# Agent Skill 09 - Codex Desktop Governance

This skill documents the repo-local Codex Desktop guardrail layer for this worktree.

## Scope

- Hooks are project-local under `.codex/` and require Codex hook trust before they run.
- The layer is a guardrail, not a complete security boundary.
- GitHub remains read-only unless a human explicitly authorizes otherwise.
- Provider output remains untrusted until human review.

## Allowed Local Commands

Run Rust validation only from `agy7rust/`:

- `cargo fmt --all --check`
- `cargo check`
- `cargo test`
- `cargo clippy -- -D warnings`
- `cargo run --bin agy-ct -- --help`

Normal repo-local reads and searches are allowed. Do not read secrets, token stores, credential files, or `.env` files.

## Blocked Operations

The pre-tool hook blocks:

- `git commit`, `git push`, `git pull`, `git merge`, `git rebase`, `git tag`, and `git fetch`
- GitHub PR, issue, and release write commands
- deploy and release-oriented commands
- environment dumps such as `env`, `printenv`, and `Get-ChildItem Env:`
- `.env`, credential, SSH key, and secret file reads
- `agy-ct run` and `agy-ct benchmark`

## Warnings

The hook layer warns on references to protected documentation, source, and generated artifact paths:

- `README.md`
- `agy7rust/src/`
- `reports/latest.json`
- `reports/performance_baseline.json`
- `artifacts/spark/`
