# Agent Operating Model

Antigravity may work autonomously only inside phase-scoped tasks.

Every task must include:
- phase name
- read-first files
- precise goal
- allowed files
- hard scope
- forbidden scope
- implementation rules
- validation commands
- return schema

---

## 1. Default Implementation Rules

- **Smallest Safe Patch**: Prefer micro-patches and incremental updates rather than broad modifications.
- **Inspect Before Edit**: Always read and verify existing file contents before editing.
- **No Unrelated Changes**: Do not perform unrelated refactoring.
- **No Committed Cached Outputs**: Runtime files in `.comptext/` are ignored and must never be committed.
- **Secrets Cleanliness**: No private keys or auth environment variables in logs or reports.
- **Explicit Network Boundaries**: Socket access is denied by default unless explicitly allowed.
- **Explicit Git Progression**: Commits and pushes occur only after validation checks pass successfully.
- **Untrusted Provider Inputs**: Model answers are handled as untrusted and must be verified.

---

## 2. Crystallized Autonomy Rules

To ensure long-running safe autonomous execution, the following rules are strictly enforced:

1. **Required Phase Reports**: Every developmental phase must produce a phase report in the `reports/` folder.
2. **Network Status Disclosures**: Every phase report must explicitly declare its `NETWORK` status (offline-only, local-only, allowed-external).
3. **Single Source of Truth**: Chat history is not the source of truth; the tracking state in `PROJEKT.md` is.
4. **Evidence vs. Truth**: Runtime artifacts (in `.comptext/` and `reports/`) are audit evidence, not trusted workspace configuration truths.
5. **Untrusted Provider Output**: All outputs, code fragments, or patch suggestions received from providers/models are treated as untrusted input.
6. **Proposal Mutability Boundary**: Proposal outputs (in `proposals/`) must never mutate active source files until approved and applied through the apply gate.
7. **Subagent Restrictions**: Subagents may validate, search, or inspect codebase assets but must never be used to bypass network, API key, browser, or write restrictions.
8. **Browser Sandbox**: Browser use is denied by default and requires explicit phase permission.
9. **Network Sandbox**: Network socket connections are denied by default and require explicit phase permission.
10. **Provider Isolation**: Live provider LLM calls are denied by default and require explicit phase permission.
11. **Secrets Redaction**: Private keys, `.env` file details, passwords, and API credentials must never be read, printed, packed, proposed, or committed.
12. **Git Progression Pipeline**: After completing a phase successfully (all checks green), the agent must validate the build, update `PROJEKT.md` status, commit the modifications, and push changes to origin.
13. **Explicit Halt**: If blocked by stop conditions, the agent must immediately stop execution and report the precise reason to the user.

---

## 3. Standard Return Schema

```text
PHASE: <Phase Number and Title>
STATUS: <success | blocked>
FILES_CHANGED: <list of changed files>
COMMANDS_RUN: <list of commands executed>
VALIDATION: <validation output summary>
ARTIFACTS: <list of generated artifacts>
GIT: <git commit and push hash/result>
NETWORK: <network status during phase>
SECRETS: <secrets status>
POLICY_DECISIONS: <policy status>
RISKS: <analysis of potential risks>
NEXT: <next action or phase name>
```
