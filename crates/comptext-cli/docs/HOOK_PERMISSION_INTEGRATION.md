# Hook and Permission Integration

This document defines the governance integration framework for CompText agent workflows. It specifies the boundaries between active local checks and planned runtime policies.

---

## 1. Implemented Behavior vs. Target Behavior

CompText maintains a strict distinction between behaviors actively executed by the local binary and behaviors designed as target integrations for the host/orchestrator:

| Governance Layer | Active Implemented Behavior | Planned Target Behavior |
|---|---|---|
| **Context Redaction** | Locally filters high-entropy secrets and sensitive configurations from Context Packs. | Planned target real-time token scanning of tool input/output streams (not active in current CLI). |
| **Apply Gate Checks** | Restricts modified files to allowed paths inside the workspace; runs local tests. | Planned target policy verification checks triggered before file system mutation (not active in current CLI). |
| **Policy Hooks** | Manual user execution of validation command suites. | Planned target interceptors evaluated before, during, or after tool usage (not active in current CLI). |
| **Host Permissions** | Guided instructions and safety baseline rulesets in `AGENTS.md`. | Planned target host/orchestrator permission constraints (not active in current CLI). |

---

## 2. Local-Only and Offline-First baseline

- **Authoritative Review-Gate**: The primary security enforcement layer remains the manual review and verification of proposed changes in the `proposals/` folder before running the apply gate (`ctxt apply`).
- **No Rust-Level Enforcements**: Hooks and permissions represent target policies for the hosting orchestrator (such as the Antigravity system). The local `ctxt` Rust binary does not contain active operating-system-level socket blockades.
- **Offline Integrity**: Calculations and change-detection hashes are performed entirely offline using local utilities. No remote distributed marketplaces or online registries are used.
