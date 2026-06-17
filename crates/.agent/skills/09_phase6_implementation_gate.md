# Skill 09: Phase 6 Implementation Gates

## 1. Phased Execution Roadmap
No cross-phase implementations are allowed. Development must follow these strict gates:
- **Phase 6B**: `agy-ct` binary configuration and `clap` tree definition (Complete).
- **Phase 6C**: Compatibility wrappers mapping `doctor`, `validate`, `handoff`, `demo`, and `context all` (Complete).
- **Phase 6D**: Automatic `agy-ct run` orchestrator sequencing doctor, context pipeline, demo, and handoff checks (Complete).
- **Phase 6E**: Execution JSON report exporter writing to `reports/latest.json` (Complete).
- **Phase 6F**: Context cache valve functionality and optional NotebookLM source bundle exporter (Future / Optional).
- **Performance Baseline & Hardening**: Baseline validation benchmarks and downstream event loop execution (Future work).

## 2. Dependency Restriction
- The installation of heavy or complex libraries (`dag_exec`, `asupersync`, `wasm_sandbox`, `wasmtime`, `tokio`, `ratatui`) is deferred for future phases.
- No new packages or dependencies may be registered in `Cargo.toml` without explicit phase-gate approval.

## 3. Safety and Sandbox Bounds
- **Offline Operations**: By default, no subcommands may access the network.
- **Git Safety**: CLI commands must never run git commits or push operations.
- **No Destructive Overwrites**: Commands must prompt before overwriting files unless overridden by `--non-interactive` or `--force`.
- **Directory Bounds**: Commands must restrict all scans to the workspace directory. No parent or sibling directory searches are permitted.
