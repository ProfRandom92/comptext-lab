# Antigravity Autonomy Model

## Goal

Antigravity CLI should do most of the planning and implementation work while preserving explicit control over risky boundaries.

## Levels

### Level 0 — Read-only analysis

Allowed: repo reading, docs reading, read-only MCP context, inventory generation.

Output: `context/**/*.json` and `context/**/*.md`.

### Level 1 — Scaffold within allowed files

Allowed: initial repo structure, Rust CLI skeleton, docs, skill files, CI.

Not allowed: provider calls, secret reads, git commit/push.

### Level 2 — Proposal generation

Allowed: concrete proposals with rationale, file operations, validation commands, rollback strategy.

Output: `proposals/**/*.md` and `proposals/**/*.json`.

### Level 3 — Controlled implementation

Allowed only when phase explicitly permits: small code changes and local validation.

Not allowed: unattended network, destructive shell, commits, pushes.

### Level 4 — Apply gate

Not performed blindly by Antigravity. A human or CompText CLI selects and applies proposals explicitly.

## Practical rule

Antigravity may prepare 80–90% of the work. Context and proposals can be autonomous; provider/network/apply/git/deploy remain explicit.
