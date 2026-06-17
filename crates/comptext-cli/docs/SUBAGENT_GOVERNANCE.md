# Subagent Governance Model

Subagents allow parallel task execution and validation. To prevent recursive execution issues or safety bypasses, subagents are subject to strict governance boundaries.

---

## 1. Allowed Roles

Only the following specialist subagent roles are permitted in the CompText workspace:

- **`security-reviewer`**: Audits codebase modifications and document updates for secret leakage, credentials, and forbidden readiness/compatibility claims.
- **`ci-diagnoser`**: Analyzes Cargo compilation failures, clippy warnings, or test logs, and recommends precise, localized corrections.
- **`docs-consistency-checker`**: Audits documentation links, checks for file presence, and verifies README consistency.
- **`proposal-auditor`**: Reviews proposal JSON structures before apply gate execution, confirming target write path safety.

---

## 2. Structural Constraints

- **Read-Only Baseline**: Subagents are read-only by default. They are authorized to search and inspect files but are strictly denied write access to the repository unless explicitly authorized for a highly specific, localized task.
- **No Git Commit or Push Authority**: Subagents must never stage, commit, or push changes to Git. Only the primary orchestrator holds Git progression authority.
- **No Autonomous Feature Building**: Subagents are bounded specialist validators. They are prohibited from writing new features, modifying program logic, or creating new provider adapters.
- **Inherited Boundaries**: Subagents inherit the parent agent's configuration, including network blockades, secret redaction policies, and stop conditions. They must never be used to circumvent parental sandboxes.
