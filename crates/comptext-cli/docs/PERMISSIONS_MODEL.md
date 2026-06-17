# Permissions Model

CompText utilizes a defense-in-depth permissions model to restrict agent actions at the orchestrator and runtime execution environment level. 

---

## 1. Defense-in-Depth Doctrine

Permissions do not serve as the primary policy compiler. Instead, they act as low-level guards supporting the Safety Constitution (`AGENTS.md`):

1. **Safety Constitution (`AGENTS.md`)**: The primary rulebook governing logical behavior.
2. **Hook Interceptors (`docs/HOOK_GOVERNANCE.md`)**: Contextual software gates executing within the workspace.
3. **Permissions Model**: Orchestrator-enforced runtime restrictions acting as a defense-in-depth policy layer.

In the target architecture, if a hook fails or an agent attempts to bypass logical constraints, the orchestrator's runtime permissions model is intended to act as a secondary layer to block unauthorized actions. Note that this runtime enforcement represents a design target and is not a Rust-level guarantee.

---

## 2. Intended Permission Scopes (Target Baseline)

The target host policy baseline for the runtime environment is partitioned into the following intended permission scopes:

- **Read Access**: Restricted to the repository workspace directory. The intended permission baseline is that reading system paths (such as `/etc`, `C:\Windows`, system temp directories, or user home directories outside the workspace) should be denied by default. CompText treats this as a required orchestrator constraint, not a Rust-level guarantee.
- **Write Access**: Restricted to allowed targets within the workspace. Target host policy should deny writing to system folders or configuration targets outside the project root.
- **Network Access**: Denied by default. The intended permission baseline is that remote socket connections should be blocked by the orchestrator unless network access is explicitly authorized for the active phase.
- **Provider Access**: Denied by default. Target host policy should block calling external LLM providers or remote endpoints unless the phase explicitly authorizes mock or local integrations.

---

## 3. Explicit Phase Approval

If a task requires a restricted operation (e.g., querying a local Ollama socket), the host/orchestrator permission profile should be explicitly approved using phase-scoped configurations in the task definition. Once the phase transitions, the intended host policy should return to the default-deny baseline. This configuration acts as orchestrator-level governance, not a Rust-level compilation check.
