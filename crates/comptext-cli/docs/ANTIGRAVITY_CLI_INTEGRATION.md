# Antigravity CLI Integration Model

This document outlines the integration architecture and operational boundaries between the **Antigravity Framework** (the Agent Execution Surface) and the **CompText CLI** (the Context, Policy, and Evidence Control Plane).

---

## 1. Core Doctrine

CompText operates under a strict separation of concerns between agent execution and context governance:

- **Antigravity CLI is the Agent Execution Surface**: Handles task orchestration, command execution, tool invocations, and subagent lifecycle management.
- **CompText CLI (`ctxt`) is the Context, Policy, and Evidence Control Plane**: Manages deterministic context packaging, proposal audits, file-write validation gates, and safety constraints.
- **Skills are progressive context-loading capsules**: Bounded guidelines designed to prevent context bloat and restrict agent operations.
- **Hooks are policy-interceptor targets (target architecture)**: Planned structural interception points designed for verifying before, during, and after agent activities, not locally active in the current implementation.
- **Permissions are defense-in-depth, not the source of truth**: Runtime/orchestrator permission boundaries that back up (but do not replace) the repository safety constitution.
- **Subagents are bounded specialist reviewers**: Highly targeted, read-only assistants delegated for review rather than autonomous development.
- **The source of truth remains the code repository**: Safety constitution (`AGENTS.md`), project tracker (`PROJEKT.md`), CompText configurations, the Proposal/Apply Gate, and local validation commands.

---

## 2. Structural Interaction

```mermaid
flowchart TD
    subagent[Antigravity Subagent]
    agent[Antigravity Orchestrator]
    ctxt[CompText CLI]
    repo[(Repository Codebase)]
    policy[Policy Gate / Target Hook]

    agent -->|1. context inspect| ctxt
    ctxt -->|2. harvest & redact| repo
    ctxt -->|3. pack latest| pack[.comptext/context_pack.latest.json]
    agent -->|4. propose| ctxt
    ctxt -->|5. write proposal| prop[proposals/proposal.latest.json]
    agent -->|6. invoke reviewer| subagent
    subagent -->|7. audit proposal| prop
    agent -->|8. apply gate| ctxt
    ctxt -->|9. planned policy target| policy
    policy -->|10. validated write execution| repo
```

---

## 3. Operational Flow

1. **Context Harvesting**: Before launching a task, the Antigravity Orchestrator executes `ctxt context pack --task "<task_description>"`. This harvest sanitizes the repository state, redacting secrets and building a deterministic Context Pack under `.comptext/context_pack.latest.json`.
2. **Proposal Generation**: When proposing changes, the agent runs `ctxt propose --provider dummy "<prompt>"`. This creates a structured JSON patch proposal under `proposals/` without mutating source files. Note that `proposals/` contains ignored/generated runtime state and is excluded from Git tracking in the release package baseline.
3. **Apply and Verification**: To modify the codebase, the agent calls `ctxt apply <proposal_path>`. The CompText CLI validates write boundaries and runs local verification (checking path-traversal safety, prompting for user confirmation, applying the patches, and executing validation tests). Interceptor hook checks (such as PreToolUse or PostToolUse) represent planned target architecture only and do not execute during runtime apply operations.
