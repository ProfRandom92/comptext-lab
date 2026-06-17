# Skill Authoring Guide

Skills are progressive context-loading capsules that guide agent behavior for specific phases or architectural boundaries. This document outlines the structure, syntax, and registry rules for creating new skills.

---

## 1. Skill Folder and File Layout

Every skill must be authored as a directory under `.agent/skills/` (or `.agents/skills/`) containing a `SKILL.md` file. For example, `.agent/skills/ctxt-antigravity-governance/SKILL.md`.

The frontmatter of each `SKILL.md` file must be structured as:

```markdown
---
name: ctxt-phase-XX-name
description: "A detailed description of the skill used as the primary routing and trigger field by the Antigravity Orchestrator."
summary: "Optional secondary metadata summarizing the skill."
---

# Skill: ctxt-phase-XX-name

## Goal
The exact objective this skill is authorized to accomplish.

## Read first
List of absolute or workspace-relative file links that the agent must read before executing any task under this skill.

## Use when
Explicit description of triggers, keywords, or phase constraints under which this skill is active.

## Allowed
Specific actions, files, or scopes that the agent is authorized to modify or access.

## Forbidden
Concrete list of actions, commands, and files that are strictly banned while this skill is active.

## Validation
Command sequence required to verify task completeness.

## Return
The requested response format (e.g., standard status report schema).
```

---

## 2. YAML Trigger Tracing

Triggers in the YAML frontmatter inform the Antigravity Orchestrator when a skill is relevant. Triggers are resolved from:
- The **task description** matching the skill `name` or `description`.
- Active **phase declarations** (e.g., `Phase 12`).

---

## 3. Naming Conventions

To keep the registry consistent, all skill filenames and YAML names must follow one of these patterns:

- `ctxt-phase-XX-*`: Mapped to a specific sequential phase in the project state machine (e.g., `ctxt-phase-12-antigravity-governance`).
- `ctxt-security-review`: General security review and claims validation.
- `ctxt-release-packaging`: Build verification and release checklist validation.
- `ctxt-antigravity-governance`: Governance policy auditing.

---

## 4. Required Content Sections

1. **Goal**: Must be concrete and bounded (no vague goals like *"Improve code"*).
2. **Read first**: Must list the files representing the source of truth for the task (e.g., `AGENTS.md`, `PROJEKT.md`).
3. **Use when**: Must describe the precise phase state.
4. **Allowed**: Must list specific actions, files, or scopes the agent is authorized to modify or access.
5. **Forbidden**: Must list global rules (e.g., *no network*, *no .env reads*) and task-specific constraints.
6. **Validation**: Must include standard local commands (`cargo check`, `cargo test`, etc.).
7. **Return**: Must match the standard schema declared in `AGENTS.md`.
