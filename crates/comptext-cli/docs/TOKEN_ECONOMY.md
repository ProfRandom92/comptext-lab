# Token Economy Guidelines

To maintain long-running, safe autonomous development, CompText enforces a token-efficient operating model. Large context windows introduce noise, increase costs, and degrade model reasoning capabilities. Bounding the context size is a core safety control.

---

## 1. Context Minimization Principles

- **Read-First Minimalism**: The agent must read only the files declared in the `Read first` section of the active skill. Bulk directory reads or loading file logs outside the active scope are prohibited.
- **One-Skill-at-a-Time Loading**: Only the single skill matching the active phase should be loaded into the workspace context. Loading multiple skills simultaneously causes instruction interference and unnecessary token consumption.
- **No Repo-Wide Rereads Without Justification**: Repeating full context pack harvests (e.g., `ctxt context pack`) is permitted only when source files have changed or a new task boundary is crossed.
- **Compact Phase Reports**: Status reports in the `reports/` folder must remain structured and concise. Avoid dumping complete compilation outputs, test outputs, or whole files. Summarize verification command results in a few clear bullet points.
- **Session State Tracking**: The file `.comptext/session_state.md` is designated as the temporary local runtime session cache. This file is ignored by Git and is used to store active task notes, remaining token counts, and session progress metrics.

---

## 2. Model Effort Selection

To optimize costs and reasoning depths, the orchestrator should select model efforts based on task complexity:

| Complexity / Task Type | Target Model Effort | Description |
|---|---|---|
| **Low** / Syntax, Formatting, Clippy fixes | **Medium Effort** | Use for minor document cleanups, format checking, running local cargo checks, or generating release metadata. |
| **High** / Structural Code, Merge Resolving, Security Auditing | **High Effort** | Use for resolving Git merge conflicts, reconciling branched PR states, running security/credential scans, or verifying critical provider adapter boundaries. |

---

## 3. Skill-Based Prompt Referencing

Instead of repeating long, descriptive instructions inside the agent's chat window prompts, prompts should reference skills directly:

- **Reference Syntax**: *"Load and execute skill `ctxt-phase-XX-name` by reading `file:///.agent/skills/ctxt-phase-XX-name/SKILL.md`."*
- **Reasoning**: This offloads instruction formatting from the central chat context, ensuring the model references the precise skill markdown file statically rather than bloating the conversation transcript.
