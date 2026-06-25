# CompText Lab / comptext-lab

**License:** MIT (crate) / EUPL-1.2 (repo docs & artifacts) **Status:** Hackathon Prototype • synthetic-only • human-in-the-loop required

> CompText Lab / comptext-lab is a local-first, offline Rust CLI prototype and library for building deterministic context packs, CT-LAB Evidence Packets v1, and BLAKE3 Merkle proofs. It is a hackathon project for research and demonstration purposes.  
> It is **not** an official BMDS or CT-LAB component. It is not a production system, provides no legal or regulatory compliance, and requires explicit human review for any decision.

## Inhaltsverzeichnis

- Überblick
- Architektur
- Quickstart
- CLI-Surface
  - agy-ct (granular)
  - sparkctl (aggregiert)
- Evidence Gate Lifecycle
- Repository-Struktur
- Test-Strategie
- Claim-Hygiene
- Hintergrund (BMDS/CT-LAB)
- Limitierungen
- Lizenz

## Überblick

CompText Lab / comptext-lab provides tooling to package synthetic extraction data into verifiable artifacts. It supports canonical serialization, BLAKE3 hashing, Merkle-tree based proofs, schema-driven context building, and the creation of CT-LAB Evidence Packets that record policy results, claim boundaries, and human review decisions.

The main goals are determinism and tamper-evidence for local review workflows. All operations run completely offline. The system works exclusively with synthetic data in the provided examples and fixtures.

Two CLIs are built from the same crate:
- `agy-ct` offers fine-grained commands for packaging, context handling, schema validation, and adversarial checks.
- `sparkctl` provides higher-level aggregated commands for common end-to-end demo and evidence flows.

The underlying Rust crate is named `comptext-lab`.

## Architektur

The project is a Cargo workspace. The core implementation lives in the `comptext-lab` package.

```
Repository root
├── crates/comptext-merkle/          # Package "comptext-lab"
│   ├── Cargo.toml
│   ├── src/
│   │   ├── bin/
│   │   │   ├── agy_ct.rs              # Granular CLI entry
│   │   │   ├── sparkctl.rs            # Aggregated CLI entry
│   │   │   └── spark_bench.rs
│   │   ├── commands/                  # Individual operations (compress, adversarial, context-*, ...)
│   │   ├── context/                   # Build, render and validate operational context
│   │   ├── codec/
│   │   │   ├── hash.rs                # blake3_hex (primary) + sha256 alias
│   │   │   ├── hex.rs                 # Central strict BLAKE3 hex utilities (decode/encode + 64-char lowercase validation)
│   │   │   ├── merkle.rs              # MerkleTree + Proof with sorted-pair BLAKE3 (uses hex.rs)
│   │   │   └── package.rs             # Evidence envelopes, manifest/ledger proofs, ClaimHygiene (uses hex.rs)
│   │   └── sparkctl/                  # High-level modules (demo, evidence, rust-validate, ...)
│   └── tests/
├── crates/examples/spark/             # Synthetic fixtures
│   └── extraction.json
├── crates/schemas/                    # Validation schemas (e.g. genehmigung_v1)
└── target/release/                    # Built binaries: sparkctl.exe, agy-ct.exe
```

Key technical characteristics:
- All serialization uses canonical JSON (sorted keys).
- Merkle trees use BLAKE3 with lexicographically sorted child pairing.
- Evidence packets explicitly carry allowed and blocked claims plus a human review decision field.
- No network access or external model calls are performed by the core tooling.

For the current consolidated status of the Merkle feature (BLAKE3 centralization in `codec/hex.rs`, path robustness), see `FEATURE_MERKLE.md`.

## Quickstart

Requirements: Rust stable toolchain.

From the repository root:

```powershell
Set-Location 'C:\CompText-CT-LAB-Sandbox-TESTING\CompText-CT-LAB-Sandbox\repos\comptext-lab-feature-merkle'

cargo build --release -p comptext-lab

.\target\release\sparkctl.exe --help
.\target\release\agy-ct.exe --help
```

Example usage with the synthetic fixture:

```powershell
# High-level evidence roundtrip
.\target\release\sparkctl.exe spark-evidence-demo -o artifacts/spark/evidence-envelope.json
.\target\release\sparkctl.exe spark-evidence-validate -i artifacts/spark/evidence-envelope.json

# Granular package + adversarial check
.\target\release\agy-ct.exe package compress -i crates/examples/spark/extraction.json -o crates/artifacts/spark/extraction.spkg
.\target\release\agy-ct.exe package adversarial -i crates/examples/spark/extraction.json
```

Cargo equivalents (from repository root):

```powershell
cargo run -p comptext-lab --bin sparkctl -- spark-demo
cargo run -p comptext-lab --bin agy-ct -- context all -i crates/artifacts/spark/extraction.spkg ...
```

Note: Some demo code and older snapshots assume execution from inside the crate directory. Adjust paths accordingly when running from the repository root.

## CompText Lab - Open Research Corpus

CT-LAB ist das offene Nachfolgeprojekt von comptext-sparkctl.
Kernfunktion: DPL-Dateien als verifizierbaren Merkle-Corpus verarbeiten.

### Quick Start
```bash
agy-ct ingest corpus/comptext_kognitive_grenzwiss.dpl
agy-ct proof --leaf INSIGHT_COGNITION
agy-ct verify --root 998f8c6e2c6b071070f882aa8ad1f6b973bfbc9f9905dc5bdaadd7d7cb99931f --leaf INSIGHT_COGNITION
```

## CLI-Surface

### agy-ct (granular)

**Antigravity-CompText CT-LAB CLI**

Global options (apply to most commands): `--plain`, `--json`, `--output`, `-v/--verbose`, `-q/--quiet`, `--no-color`, `--non-interactive`, `--explain`.

Top-level commands:
- `run` — Automatically coordinate the full local step sequence
- `demo` — Run a predefined end-to-end trace workflow
- `doctor` — Diagnose local project readiness
- `validate` — Validate current project formatting, tests, and clippy rules
- `handoff` — Verify local repository handoff readiness
- `benchmark` — Run local performance benchmark and validation checks

Subcommand groups:
- `package`
  - `compress` — Compress raw extraction files to .spkg
  - `inspect` — Read sidecar properties and headers from .spkg
  - `verify` — Run SHA-256 cryptographic verification of .spkg
  - `replay` — Deterministically reconstruct and replay the sidecar trace
  - `adversarial` — Verify robustness against tampered payload attributes
- `context`
  - `build` — Generate structured operational context from a package
  - `render` — Render operational context into token-light text
  - `validate` — Run structural validation and leak checks on a context
  - `all` — Execute context build, render, and validate tasks in sequence
- `schema`
  - `check` — Validate raw trace files against target JSON schemas
- `report`
  - `export` — Exporter for generated pipeline JSON reports
- `notebook`
  - `bundle` — Bundles context state and text renderings into a unified documentation payload

### sparkctl (aggregiert)

**CT-LAB Operational Context Layer CLI**

Commands:
- `doctor` — Diagnose local project readiness
- `rust-validate` — Run local Rust quality checks (fmt, check, test, clippy)
- `context-all` — Run complete context lifecycle (build, render, validate)
- `spark-demo` — Run complete end-to-end demo pipeline (compress, build, render, validate)
- `spark-evidence-demo` — Write a deterministic CT-LAB Evidence Packet v1 demo envelope
- `spark-evidence-validate` — Validate a CT-LAB Evidence Packet v1 envelope
- `handoff-check` — Verify local repository handoff readiness
- `merkle` — Merkle proof generation and verification (BLAKE3)
  - `manifest-proof` — Generate a manifest Merkle proof from a CT-LAB evidence envelope
  - `verify-manifest` — Verify a manifest Merkle proof
  - `ledger-proof` — Generate a ledger Merkle proof from a CT-LAB package JSON
  - `verify-ledger` — Verify a ledger Merkle proof

## Evidence Gate Lifecycle

The tooling implements a sequence of local stages that turn a synthetic input into a reviewable, hash-chained artifact:

1. **Source fixture** — Synthetic JSON (e.g. administrative planning data with extracted fields).
2. **Package stage** (`agy-ct package ...`) — Compression to `.spkg`, sidecar hashing (SHA-256), field path extraction, integrity verification, deterministic replay, and adversarial tamper testing.
3. **Context stage** (`agy-ct context ...` or `sparkctl context-all`) — Schema-driven construction of structured context, token-light rendering, and validation including leak checks.
4. **Evidence Packet** (`sparkctl spark-evidence-*`) — Assembly of an envelope containing an artifact manifest, canonical hash, Merkle roots, goal description, policy result, provider boundary status, explicit claim hygiene lists, and placeholders for human review.
5. **Proofs** (`sparkctl merkle ...`) — Generation and verification of selective Merkle proofs over manifest entries or ledger entries.

Every stage is designed to support human review. The generated packets record that a proposal remains untrusted until a human decision is explicitly noted.

## Repository-Struktur

```
.
├── Cargo.toml                           # Workspace definition
├── crates/
│   ├── comptext-merkle/               # The "comptext-lab" crate
│   │   ├── Cargo.toml
│   │   ├── src/bin/{sparkctl.rs, agy_ct.rs, spark_bench.rs}
│   │   ├── src/commands/                # Package, context, schema, report, notebook commands
│   │   ├── src/context/                 # Build / render / validate logic
│   │   ├── src/codec/                   # hash, merkle, package (evidence + proofs)
│   │   ├── src/sparkctl/                # Aggregated high-level command modules
│   │   └── tests/
│   ├── examples/spark/
│   │   └── extraction.json              # Primary synthetic fixture
│   ├── artifacts/spark/                 # Example .spkg and context outputs
│   └── schemas/
├── artifacts/spark/                     # Generated evidence envelopes
├── air/                                 # Related AIR schemas and fixtures (separate)
├── python/                              # Additional benchmarks and tools
├── NOTICE.sparkctl.md
├── LICENSING.sparkctl.md
├── THIRD_PARTY_LICENSES.sparkctl.md
├── (multiple PHASE* and SNAPSHOT*.md files documenting development steps)
└── target/release/                      # Built CLIs after `cargo build --release`
```

**Note on historical snapshots:** The numerous `PHASE*.md` and `*SNAPSHOT*.md` files under `crates/` and `crates/comptext-merkle/` are historical development snapshots retained for auditability. The current consolidated architecture and Merkle feature status (including BLAKE3 centralization) are documented in this README and `FEATURE_MERKLE.md`.

## Test-Strategie

The primary test command is:

```powershell
cargo test -p comptext-lab
```

At the time of this audit:
- 62 tests passed.
- Release build succeeds.
- `cargo clippy -p comptext-lab --all-targets -- -D warnings` reports 1 error (a needless range loop lint in `src/codec/merkle.rs`).

The test suite covers Merkle roundtrips (manifest and ledger), package verification and replay, evidence packet shape and rejection cases (tampering, missing hygiene fields, etc.), schema validation, adversarial detection, and CLI execution smoke tests for the high-level sparkctl commands.

## Claim-Hygiene

This project follows strict claim hygiene and explicitly documents what it does **not** claim.

From `NOTICE.sparkctl.md` and generated artifacts:

- This project is **not** an official BMDS/CT-LAB component.
- It does **not** provide legal advice, administrative decision automation, regulatory certification, EU AI Act certification, or official compliance guarantees.
- All demo and example data is **synthetic-only**. Real citizen data or confidential records must not be used.
- Every meaningful output is intended to support **human-in-the-loop** review. No autonomous decision making or approval occurs.

The evidence packets themselves contain explicit `claim_hygiene` sections listing allowed and blocked claims. The project uses defensive wording such as "prototype", "demo", "hackathon project", "synthetic-only", and "local-first / offline".

## Hintergrund (BMDS/CT-LAB)

The tooling was developed in the context of research around AI-supported administrative planning and approval processes. Example fixtures reference structures similar to those found in German planning law contexts (e.g. BImSchG-related data).

It is an independent prototype exploring how deterministic packaging, context layers, and evidence artifacts could look for such workflows. It is **not** an official part of any government CT-LAB program or BMDS system.

## Limitierungen

- This is a **prototype / hackathon project**. It is not intended for production use.
- All operations are local and offline. No external services or model providers are called.
- Fixtures and examples are synthetic.
- Some internal demo code and path references assume specific working directories.
- Current strict clippy checks do not pass (one lint in the Merkle implementation).
- The repository contains a large amount of supporting material (Python benchmarks, AIR definitions, many development snapshots). This README focuses on the Rust CLI surface.
- Hash stability and reproducibility have been measured on the included tests and fixtures; no broader guarantees are made.
- Cross-platform behavior should be verified separately.

## Lizenz

- The Rust crate (`crates/comptext-merkle`, package name `comptext-lab`) is licensed under the MIT License.
- Repository-level documentation, examples, schemas, and workflow artifacts are licensed under the European Union Public Licence v1.2 (EUPL-1.2).
- Third-party dependencies retain their original licenses (see `THIRD_PARTY_LICENSES.sparkctl.md`).

Relevant files:
- `LICENSE.sparkctl-repo`
- `LICENSING.sparkctl.md`
- `NOTICE.sparkctl.md`
- `THIRD_PARTY_LICENSES.sparkctl.md`

---

Last updated: 2026-06-20 – Phase 3 Documentation Consolidation (FEATURE_MERKLE.md + Architektur-Update)
