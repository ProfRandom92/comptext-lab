# Phase 4A sparkctl Planning Handbook

## 1. Product Identity
- **Repository Name:** `Antigravity-CompText-sparkctl`
- **CLI Binary Name:** `sparkctl`

## 2. Phase 4 Purpose
Transition the individual package extraction, validation, and operational context commands into a single cohesive CLI utility (`sparkctl`) to simplify workflow diagnostic audits and record-keeping operations.

## 3. Strict Scope
- Implement a unified CLI interface wrapping standard packaging and validation subcommands.
- Preserve all existing Phase 1, 2, and 3 Rust validation rules and logic.
- Target commands must execute offline and output clean, structured, and parseable summaries.
- Prefer dry-run and validation check reporting behavior before performing execution or write actions.

## 4. Forbidden Scope
- **No Git Destructive Actions:** Do not stage, delete, revert, or force-push commits.
- **No GitHub Writes:** Do not perform git push or alter remotes configurations.
- **No Network Access:** All calculations and checks must run 100% offline.
- **No Directory Escapes:** Do not scan directories outside the sandbox workspace root.
- **No Advanced Integrations:** Do not add MCP server integrations, RAG systems, embeddings, vector databases, or LLM wrappers.
- **No Compliance Certifications:** Do not claim compatibility with official SPARK schemas or compliance with the EU AI Act.

## 5. Recommended CLI Command Surface
- `sparkctl doctor`: Diagnoses toolchain setup, workspace folders, schemas, and git layout.
- `sparkctl rust-validate`: Triggers Cargo formatting, check, clippy, and integration tests pipeline.
- `sparkctl spark-demo`: Executes E2E package compress, inspect, verification, and adversarial suite run.
- `sparkctl context-all`: Sequences context-build, context-render, and context-validate actions on target package and schema sidecars.
- `sparkctl handoff-check`: Verifies Git staging cleanliness and remote status readiness in dry-run mode.

## 6. Implementation Phases
1. **Phase 4A: Planning Handbook:** Define structure and boundaries (Current Phase).
2. **Phase 4B: Code Packaging & CLI Renaming:** Rename crate binary to `sparkctl`, register unified subcommands interface.
3. **Phase 4C: Commands Implementation:** Port existing scripts and validations into the registered `sparkctl` functions.
4. **Phase 4D: E2E Verification & Handoff:** Final validation and snapshot reporting.

## 7. Safety & Git Boundaries
- The tool must execute exclusively inside the sandbox root directory.
- File system mutations must be restricted to the `artifacts/` folder.
- Staging commands must use explicit file paths. Wildcards are strictly prohibited.

## 8. Validation Checklist
Before completion, the following checks must run successfully:
```bash
cargo fmt --all --check
cargo check
cargo test
cargo clippy -- -D warnings
sparkctl doctor
sparkctl rust-validate
sparkctl spark-demo
sparkctl context-all -i ../artifacts/spark/extraction.spkg -s ../schemas/genehmigung_v1.json
sparkctl handoff-check
```

## 9. Validation Claims and Assurances
- Offline behavior was deterministic in the validated test scope.
- Configured leak checks passed in the validated scope.
- No blocking risks found in the validated scope.

## 10. Stop Conditions
Stop execution and report `blocked` if:
- Commands require external webhooks or network calls.
- Verification requires importing external crate libraries with native system dependencies.
- Changes necessitate structural changes to the validated operational context json model schema.

## 11. Return Format for Phase 4B Implementation
```text
PHASE: Phase 4B sparkctl implementation
STATUS: success | blocked
COMMANDS_RUN:
- ...
FILES_CHANGED:
- ...
SPARKCTL_STATUS:
- ...
RISKS:
- ...
NEXT:
- Phase 4C implementation only after approval
```
