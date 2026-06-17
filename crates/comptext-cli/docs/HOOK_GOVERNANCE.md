# Hook Governance Model

Hooks are policy-interceptor targets designed to enforce safety boundaries before, during, and after agent runs. This document defines the target architecture for interceptor hooks within the CompText workspace. Note that these hooks represent a planned target architecture and are not yet locally implemented in the current code execution pipeline.

---

## 1. Interception Points

The target architecture defines four critical interceptor locations:

```text
[ SessionStart Hook ]
         │
         ▼
[ PreToolUse Hook ] ────( Violations? )────► [ FAIL CLOSED / HALT ]
         │
         ▼
    ( Tool Run )
         │
         ▼
[ PostToolUse Hook ] ───( Redact Secrets )──► [ Filtered Context ]
         │
         ▼
[ PostPhase Hook ] ─────( Cargo Validation )──► [ Git Commit Pipeline ]
```

1. **SessionStart**:
   - **Trigger**: Planned trigger when a new agent session or subagent run is initiated.
   - **Verification**: Intended to parse workspace config and verify CLI version. Checks local Git state by default; matching against remote origin main branches is performed only when remote checks are explicitly authorized.
2. **PreToolUse**:
   - **Trigger**: Planned trigger immediately before any tool (e.g. file read, file write, shell command execution) is run.
   - **Verification**: Intended to evaluate inputs against active policy rules, failing closed and blocking execution if a violation is detected.
3. **PostToolUse**:
   - **Trigger**: Planned trigger immediately after a tool finishes running, before returning the output to the agent's context.
   - **Verification**: Intended to filter and redact high-entropy secrets, passwords, or credentials from command output and file read buffers.
4. **PostPhase**:
   - **Trigger**: Planned trigger when an agent signals completion of a roadmap phase.
   - **Verification**: Intended to run the **Global Validation Suite** and check Git status to ensure the working tree remains clean before triggering the Git push progression pipeline.

---

## 2. Intended Policy Enforcement (Target Architecture)

The hook governance target architecture is designed for the following intended enforcement policies:

- **Block `.env` and Secret Reads**: PreToolUse hooks are planned to block attempts to read `.env`, `.env.*`, keyfiles (`*.key`, `*.pem`, `*.p12`, `*.pfx`), or private keys.
- **Block Environment Variable Printing**: Intended to block executing commands like `env`, `printenv`, or `Get-ChildItem Env:` to prevent leakages of system configuration credentials.
- **Block Network and Provider Calls**: Intended to intercept socket calls or provider invocations unless the active phase config explicitly permits network access.
- **Block Out-of-Bounds Writes**: Intended to restrict file modifications to paths inside the repository root, rejecting edits targeting directories outside the workspace.
- **Block Broad Repository Rereads**: Intended to limit tool executions that read the entire codebase recursively unless justified by a phase transition.
- **Require Proposal Before Apply**: Intended to enforce that source code modification is only done via the `ctxt apply` flow referencing a verified JSON proposal from `proposals/`.
- **Require Local Validation**: Intended to block marking a phase as complete until all commands in the validation suite pass successfully.
