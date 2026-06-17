# Agent Skill 12 — Agent Handoff Profile

This skill defines the safe handoff profile and repository coordination guidelines for future Antigravity agent sessions.

## 1. Validated Commands

The following commands are validated for usage inside `agy7rust/`:
- `cargo fmt --all --check`
- `cargo check`
- `cargo test`
- `cargo clippy -- -D warnings`
- `cargo run --bin agy-ct -- run`
- `cargo run --bin agy-ct -- doctor`
- `cargo run --bin agy-ct -- validate`
- `cargo run --bin agy-ct -- context all`
- `cargo run --bin sparkctl -- doctor`

## 2. Protected Local Files

The following files are untracked local runtime outputs and must remain untracked (never stage or commit them):
- `reports/latest.json`
- `POST_PUSH_GITHUB_VERIFICATION.md`

## 3. Operations Rules

Future sessions must adhere to these coordination rules:
1. **Inspect Before Editing:** Read the active handbook and existing snapshot documentation before making any modifications.
2. **Smallest Safe Patch:** Prefer small, scoped changes over large edits.
3. **Change Only Allowed Files:** Restrict edits to the paths explicitly specified in the active phase roadmap.
4. **No Premature Staging:** Keep generated runtime output files untracked.
5. **No Unauthorized Commits/Pushes:** Only stage, commit, or push when explicitly instructed by the user's phase requests.

## 4. Standard Return Format

Handoff status updates must be reported using the following format:
- `STATUS: <success | blocked>`
- `CURRENT_STATE: <summary of the current codebase state>`
- `SAFE_COMMANDS: <list of verified working commands>`
- `PROTECTED_FILES: <list of untracked files to be preserved>`
- `RECOMMENDED_NEXT_ACTION: <next step in the roadmap>`
- `RISKS: <potential environmental risks or dependency concerns>`
