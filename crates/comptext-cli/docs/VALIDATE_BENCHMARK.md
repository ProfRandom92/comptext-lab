# Validation and Benchmarking

This document details the usage and specifications for the local validation and benchmarking features of `comptext` CLI (`ctxt`).

## 1. Local Validation Command

The `ctxt validate` command prints the standard local validation commands used to ensure codebase integrity and safety verification.

### Usage
```bash
ctxt validate
```

### Output
```text
Standard local validation commands:
cargo fmt --all --check
cargo check
cargo test
cargo clippy -- -D warnings
```

---

## 2. Deterministic Benchmark Command

The `ctxt benchmark` command evaluates context packaging and model request generation deterministically under an offline sandbox.

### Usage
```bash
ctxt benchmark --provider dummy "How should I test this repo?"
```

- **`--provider`**: Optional argument. Currently, only `"dummy"` is supported to prevent unauthorized live network calls (fails closed if another provider is specified). Defaults to `"dummy"`.
- **task description**: The target prompt to run the benchmark against.

### Artifact Outputs

Each benchmark run builds a schema-checked Context Pack and runs the offline model query. It writes a deterministic JSON artifact to `.comptext/benchmark.latest.json` containing:

- `schema_version`: Version of the benchmark format.
- `task`: The prompt task.
- `provider`: The provider used.
- `context_pack_path`: Filepath to the generated Context Pack.
- `request_artifact_path`: Filepath to the generated Model Request.
- `response_artifact_path`: Filepath to the generated Model Response.
- `validation_commands`: List of local validation commands.
- `network`: Network state declaration (always `"offline-only"` in this phase).
- `secrets`: Secrets handling status (always `"redacted"`).
- `status`: Benchmark run completion status (always `"success"` if successful).
