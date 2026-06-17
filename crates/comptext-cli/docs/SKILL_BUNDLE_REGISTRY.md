# Skill Bundle Registry

This document describes the design, directory convention, and change-detection integrity rules of the local **Skill Bundle Registry** for CompText agent workflows.

---

## 1. Local Architectural Scope

The Skill Bundle Registry is a repository-local index designed to compile, catalog, and locate reusable workflow skills.

- **Local Registry Root**: Canonical workspace root lives under `.agent/skills/` at the project root directory. Any `.agents/skills/` directory is treated purely as legacy/compatibility metadata.
- **Directory Layout**: Every skill registry entry must be structured as a directory containing a `SKILL.md` file (e.g. `.agent/skills/ctxt-security-review/SKILL.md`).
- **Trigger Properties**: The `description` field in the frontmatter of each `SKILL.md` acts as the primary orchestrator keyword routing trigger.
- **Registry Index**: The file `.agent/skills/REGISTRY.md` maintains the complete index of authorized skills, scopes, and validation commands.

---

## 2. Integrity and Change-Detection Hashes

To ensure stability during autonomous operations, the local registry compiles SHA-256 integrity hashes for each skill's `SKILL.md` file.

- **Change-Detection Policy**: Checksums are used strictly as local change-detection metadata to verify that a skill's instructions have not been mutated by unapproved tasks.
- **Not an Assurance Claim**: These hashes do **not** represent unsupported assurance claims.
- **Offline Integrity**: Calculations are performed entirely offline using local hashing commands (such as `Get-FileHash` or `sha256sum`).

---

## 3. Safety and Security Rules

All skills managed within the registry must inherit and conform to the following safety constraints:
- **Default-Deny Provider Socket Access**: Prohibits socket or network requests by default.
- **No Credentials Access**: Restricts reading private keys, `.env` files, or system credentials.
- **No System Dumps**: Prohibits printing environment variables.
- **Sandboxed Write Execution**: Restricts file modifications to paths inside the repository workspace root.
- **No Autonomous Feature Building**: Bounded execution prohibits subagents or routines from writing core features outside active phase tasks.
- **No Distributed Networking**: No remote downloads, distributed lookups, or third-party plugin marketplaces are supported.
