# MVP Status & Release Readiness

This document outlines the current feature completion, safety design, and release readiness of the **CompText CLI** (`ctxt`) MVP.

## 1. Feature Completion Status (Phases 0–9)

All core architecture components and phase requirements are fully implemented and verified locally:
- **CLI Shell**: Base parser supporting version, doctor, help, and provider lists.
- **Context Harvester**: Inspects and compiles codebase context pack files deterministically.
- **Context Pack Contract**: Writes deterministic, sorted, and redacted packs to `.comptext/context_pack.latest.json`.
- **Offline Dummy Provider**: Fully offline deterministic execution flow with no external I/O.
- **Local Ollama Adapter**: Configurable endpoints targeting local environments with strict socket policy controls.
- **OpenAI-Compatible Adapter**: Offline-safe MVP skeleton formatting normalized completions requests.
- **Proposal & Apply Gates**: Two-step execution pipelines. Propose compiles context and writes proposals under `proposals/`. Apply verifies write-allowed targets, prompts for confirmation, and executes patches.
- **Validate & Benchmark**: Prints standard verification routines and saves deterministic performance benchmarks locally.

---

## 2. Security Boundaries & Constitution Alignment

- **Model/Provider Output Untrusted**: All suggestions, snippets, and patches produced by provider models are treated as untrusted inputs. They are subjected to the apply-time write sandbox and post-apply validation gates.
- **Network Boundaries (Deny-by-Default)**: Real external network execution is strictly denied unless explicitly authorized. The OpenAI-compatible adapter operates entirely offline in this MVP phase.
- **Secret Redaction**: Credentials, tokens, keys, and private configuration variables are systematically scrubbed from serialized metadata output and printed diagnostics.
- **Sandbox Write Protections**: Path-traversal checks prevent files outside the repository or inside sensitive targets (such as `.git/`, `.comptext/`, `reports/`) from being modified during apply procedures.

---

## 3. Release Readiness & Release Limitations

- **Experimental Scope**: This command-line interface is an experimental, local-first utility for research and development context packaging.
- **Honest Claim Policy**: No unsupported assurance claims are made.
