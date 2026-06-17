# Phase 4F sparkctl handoff-check Planning Handbook

## 1. Objective
Define the implementation blueprint for the `sparkctl handoff-check` subcommand. This subcommand inspects the presence and status of local handoff files, verifies correct operational artifacts, and validates CLI command availability prior to git repository handoffs.

## 2. Strict Scope
- **Command:** `sparkctl handoff-check`
- **Default Handoff Files to Inspect:**
  - `AGENTS.md`
  - `.agent/skills/00_project_system.md`
  - `.agent/skills/01_phase_gate.md`
  - `.agent/skills/02_rust_validation.md`
  - `.agent/skills/03_artifact_validation.md`
  - `.agent/skills/04_spark_context_layer.md`
  - `.agent/skills/05_claim_hygiene.md`
  - `.agent/skills/06_git_handoff.md`
  - `PHASE3_CONTEXT_LAYER_FINAL_SNAPSHOT.md`
  - `PHASE4A_SPARKCTL_PLANNING_HANDBOOK.md`
  - `PHASE4B_SPARKCTL_DOCTOR_SNAPSHOT.md`
  - `PHASE4C_SPARKCTL_RUST_VALIDATE_SNAPSHOT.md`
  - `PHASE4D_SPARKCTL_CONTEXT_ALL_SNAPSHOT.md`
  - `PHASE4E_SPARKCTL_SPARK_DEMO_SNAPSHOT.md`
  - `agy7rust/PHASE4D_STATUS.md`
  - `agy7rust/PHASE4E_STATUS.md`
  - `artifacts/spark/extraction.spkg`
  - `artifacts/spark/context.json`
  - `artifacts/spark/context_render.txt`
  - `examples/spark/extraction.json`
  - `schemas/genehmigung_v1.json`
- **Expected Command Surface Checks (spawning local commands only):**
  - `cargo run --bin sparkctl -- doctor`
  - `cargo run --bin sparkctl -- context-all`
  - `cargo run --bin sparkctl -- spark-demo`
- **Exit Code:** Exits with status `0` if all checks and subcommands pass, and a non-zero code if any file is missing or any command fails.
- **Stop on Failure:** The command stops on the first failed check.

## 3. Forbidden Scope
- **No Git Access:** The command must not run any git command or perform git operations.
- **No Network Usage:** Work must occur 100% offline.
- **No File Mutations:** The command must verify configurations but not modify files.
- **No Directory Escapes:** Do not scan folders outside the sandbox directory.
- **No Compliance Claims:** No claims regarding EU AI Act or official SPARK schemas compatibility.
- **No Raw Payload Dumps:** Ensure logs do not print original payload fields (applicant, recommendation, notes).

## 4. Execution & Reporting Rules
- **Execution Directory:** The tool must execute local check commands within the `agy7rust` workspace directory root path.
- **Diagnostics Formatting:** Output must show a clean list of checked subcommands with status indicator tags (e.g. `[AGENTS] OK`, `[DOCTOR_CMD] PASS`).

## 5. Safety & Security Boundaries
- Validation runs local crate subcommands and file checks only via direct library orchestration.
- Offline behavior was deterministic in the validated test scope.
- Configured leak checks passed in the validated scope.
- No blocking risks found in the validated scope.

## 6. Validation Checklist
Before completion, verification must confirm:
```bash
cargo check
cargo test
sparkctl doctor
sparkctl rust-validate
sparkctl context-all
sparkctl spark-demo
sparkctl handoff-check
```

## 7. Stop Conditions
Stop implementation and return `blocked` if:
- Verification checks require external registry updates or internet connections.
- Validation checks require accessing remote credentials or secrets.

## 8. Return Format for Phase 4F Implementation
```text
PHASE: Phase 4F sparkctl handoff-check implementation
STATUS: success | blocked
COMMANDS_RUN:
- ...
FILES_CHANGED:
- ...
HANDOFF_CHECK_OUTPUT:
- ...
VALIDATION:
- ...
RISKS:
- ...
NEXT:
- Phase 4F audit/snapshot only after approval
```
