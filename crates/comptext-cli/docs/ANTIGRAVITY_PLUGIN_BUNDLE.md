# Antigravity Plugin Bundle Specification

This document specifies the architecture, boundaries, and components of the Antigravity Plugin Bundle system in the CompText CLI ecosystem.

## Architectural Principles

1. **Deterministic Control**:
   CompText serves as the deterministic Evidence-Control-Plane. Every context pack, state report, and proposal is strictly structured, schema-checked, and local.
   
2. **Execution Surface**:
   Antigravity acts as the Agent Execution Surface. It processes agent commands, imports/exports configurations, and manages local tools/skills.
   
3. **No LLM Judge**:
   There is no LLM-based verification authority. Autonomy and state transition checks must rely purely on deterministic local validations (e.g. check-sum, compilation, pattern matching).

4. **Advisory Subagents**:
   Subagents (e.g., in `.agents/`) are advisory-only. They lack the authority to issue PASS/FAIL verdicts. Only local CLI tools verify execution states.

5. **Untrusted Protocol Boundaries**:
   MCP outputs, external APIs, and model-provided patches are treated as untrusted input. They must pass validation and audit gates before application.

6. **Hooks Policy Audits**:
   Hooks configured in the bundle (e.g. `hooks.json`) are templates used for linting and safety checks. They are not executed live in the CLI engine at runtime.

7. **Repo-Relative and Sandboxed Paths**:
   All paths configured or accessed by plugin bundles must be repo-relative. Absolute paths are strictly forbidden to ensure isolation.

## Component Structure

A standard Antigravity Plugin Bundle consists of the following components:
- `plugin_manifest.json`: Root metadata containing dependencies, permissions, and paths.
- `skills/`: Local skill folders with detailed instructions and boundaries (`SKILL.md`).
- `rules/comptext-rules.md`: Bounded execution markdown checklists.
- `hooks/hooks.json`: Interception rules and policy templates.
- `mcp/mcp_config.json`: Configuration for local Model Context Protocol servers.
- `permissions/permissions.template.json`: Declared permissions for actions (e.g. `command`, `write_file`, `read_url`, `mcp`).
- `agents/`: Specifications for advisory subagents.
