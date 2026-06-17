# Agent Skill 00 — Project System

This skill defines the repository structure, active directories, permissions, and operating boundaries for the sandbox environment.

## 1. Operating Boundaries

- **Sandbox Root:** current workspace clone
- **Allowed Write Paths:**
  - `agy7rust/` (Rust crate)
  - `examples/spark/` (Synthetic SPARK-style fixtures)
  - `artifacts/spark/` (Verification and demo outputs)
  - `.agent/skills/` (Local agent instructions)
- **Forbidden Paths:** Any parent directory, desktop, sibling workspaces, and the `.git` metadata of the system. Agents must not inspect, modify, copy, move, delete, or index any CompText-related files outside the current workspace clone.
- **Historical Evidence Paths:** Old Antigravity-Comptextv7 paths, `C:\Users\contr` paths, Termux paths, `git_post_push_verification` paths, and `file:///C:/` links are historical evidence only and must not be used as valid active paths.
- **Search Boundaries:** Do NOT perform global searches, recursive searches, or file indexing outside the sandbox root.

## 2. Command Permissions

- **Cargo Access:** Running `cargo` command actions (`cargo fmt`, `cargo check`, `cargo test`, `cargo clippy`, `cargo run`) is strictly limited to the `agy7rust/` subdirectory.
- **Git Restrictions:** No git remotes config, git fetch, git pull, or git push commands are permitted.
- **Network Access:** All network calls and API connections are blocked. The project works entirely offline.

## 3. Standard Return Format

Every completed agent execution step must output the exact formatted block:

```text
PHASE: <phase_name>
STATUS: <success | blocked>
FILES_CHANGED:
- ...
COMMANDS_RUN:
- ...
TESTS:
- ...
RISKS:
- ...
NEXT:
- ...
```
