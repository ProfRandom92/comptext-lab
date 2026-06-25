# FEATURE_MERKLE.md — BLAKE3 Merkle Proofs (Consolidated Final Status)

**Worktree / Feature:** `comptext-lab-feature-merkle` — Merkle proof support for SPARK-style evidence packets.

**Status:** Consolidated after Phase 2 (BLAKE3 centralization + path robustness). All quality gates passed.

> This is a **Hackathon Prototype • synthetic-only • human-in-the-loop required**.  
> CompText SPARK / sparkctl is a local-first, offline Rust CLI prototype and library for building deterministic context packs, SPARK Evidence Packets v1, and BLAKE3 Merkle proofs. It is a hackathon project for research and demonstration purposes.  
> It is **not** an official BMDS or SPARK component. It is not a production system, provides no legal or regulatory compliance, and requires explicit human review for any decision.

## Current Consolidated Architecture (Post-Phase 2)

The core BLAKE3 handling has been centralized for consistency and strict validation:

```
crates/comptext-sparkctl/src/codec/
├── hash.rs                 # blake3_hex (primary) + sha256 alias (for backward compat)
├── hex.rs                  # Central strict BLAKE3 hex utilities (decode/encode + 64-char lowercase validation)
├── merkle.rs               # MerkleTree + MerkleProof with sorted-pair BLAKE3 hashing (uses hex.rs)
└── package.rs              # Evidence envelopes, manifest/ledger proofs, integration with ClaimHygiene (uses hex.rs)
```

Key improvements consolidated here:
- **BLAKE3 centralization**: All 32-byte hash decode/encode/validation logic now lives in `codec/hex.rs` (`decode_blake3_hex`, `try_decode_blake3_hex`, `encode_hex_32`, `is_valid_blake3_hex`). Strictest rule enforced: exactly 64 lowercase hex digits.
- Merkle trees continue to use lexicographically sorted child pairing for commutative internal nodes.
- Manifest and ledger Merkle proofs are generated/verified with strict pre-validation (no silent bad hashes).
- `MerkleProofHex` roundtrips and CLI proof commands remain stable.

Path/CWD robustness (affects usability of Merkle and related commands):
- Report writing and sub-cargo invocations (`rust-validate`) no longer rely on fragile relative `../reports` or bare `cargo` calls.
- All operations are expected to be run from the repository root with `-p agy7rust`.

## Public API (`agy7rust` crate)

- `generate_manifest_merkle_proof` / `verify_manifest_merkle_proof`
- `generate_ledger_merkle_proof` / `verify_ledger_merkle_proof`
- `proof_to_hex` / `proof_from_hex` (`MerkleProofHex`)
- `MerkleTree`, `MerkleProof`, `verify_proof`, `verify_proof_hash`, `Hash`

All functions are deterministic and offline-only.

## CLI Surface (sparkctl)

```powershell
# Generate
sparkctl merkle manifest-proof -i artifacts/spark/evidence-envelope.json --index 0 -o proof.json
sparkctl merkle ledger-proof -i package.json --index 0

# Verify
sparkctl merkle verify-manifest --root <64-hex> --leaf <64-hex> -i proof.json
sparkctl merkle verify-ledger --root <64-hex> --entry <64-hex> -i proof.json
```

The `merkle` subcommand is part of the aggregated `sparkctl` binary. Granular access is also available via `agy-ct` flows where relevant.

## Test & Quality Status

- Full Merkle unit tests (tree construction, proof generation, negative cases, hex roundtrips, tamper detection).
- Integration coverage in `spark_roundtrip.rs` (manifest/ledger roundtrips, root validation, negative cases).
- All gates (`cargo fmt --all --check`, `cargo check -p agy7rust --workspace`, `cargo clippy -p agy7rust -- -D warnings`, `cargo test -p agy7rust`) are green.

## Claim Hygiene (Skill 05 — Exact)

This project follows strict claim hygiene and explicitly documents what it does **not** claim.

### Allowed Claims (we may state these)
- **Synthetic SPARK-Style Fixture:** We operate against static mock datasets representing administrative structures.
- **Deterministic Packaging:** Packaging code creates identical byte outputs across repeated executions from the same input.
- **Replayable Metadata:** We extract canonical field paths and commitment tokens.
- **Tamper-Sensitive Hash Chain:** The package structure incorporates verification chains (payload SHA-256 / BLAKE3, sidecar final state hash, and package integrity hash).
- **Schema Sidecar Validation:** The CLI enforces required field presence and scalar types on input JSON templates.
- **Deterministic Replay Only:** The tool is designed exclusively for offline package packaging, verification, and schema checks; it does not perform active runtime execution, predictions, or online agent coordination.

### Forbidden Claims (strictly prohibited)
- **SPARK JSON Compatibility:** Do not claim compatibility with official SPARK JSON extractors or schemas.
- **EU AI Act Compliance:** Do not claim the tool certifies or is compliant with the EU AI Act. Mention only "Art.-12-oriented record keeping support" as a design pattern.
- **Legal or Judicial Proof:** Do not claim that packages constitute court-admissible evidence, legally binding proofs, or legal validation.
- **Forensic Certainty & Recovery:** Avoid terms like "100% forensic security", "invulnerable tamper resistance", or automated forensic recovery/repair. Use "tamper-sensitive validation" only.
- **MCP Integration:** Do not claim MCP capability or server features unless explicitly built in a future phase.
- **Production Readiness:** The system is a mock prototype only. No production or enterprise setup readiness.
- **Autonomous Decisions:** The tool does not make autonomous planning or administrative decisions.

See also `NOTICE.sparkctl.md`, `README.md` (Claim-Hygiene section), and the `claim_hygiene` fields inside generated evidence packets.

## Limitations & Scope

- This is a **prototype / hackathon project**. It is not intended for production use.
- All operations are local and offline. No external services or model providers are called.
- Fixtures and examples are synthetic.
- Historical development snapshots (`PHASE*.md`, `*SNAPSHOT*.md`) exist under `crates/` and `crates/comptext-sparkctl/` for audit trail. They are not updated with current status.
- The current consolidated view of the Merkle feature is documented here and referenced from the main `README.md`.

## Related Files

- `README.md` — overall project overview, CLI surface, claim hygiene
- `NOTICE.sparkctl.md` — additional non-claims guidance
- `crates/comptext-sparkctl/src/codec/hex.rs` (implementation detail — read-only reference)
- Historical snapshots (retained for auditability)

---

**Last consolidated:** 2026-06-20 (after Phase 2 completion, no code changes in this phase)
