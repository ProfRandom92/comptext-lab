# benchmarks/

Isolated benchmark harness for the CompText workspace (lab use only).

## Quick Start

```bash
# From repo root
bash benchmarks/run-benchmarks.sh

# View results
open benchmarks/reports/cockpit.html
# or
cat benchmarks/reports/latest.json
```

```bash
# Manual
cargo bench -p comptext-benchmarks
```

## What it measures (synthetic data only)

- `package_lifecycle` — build/verify/replay of evidence packets
- `merkle_proof` — tree construction + proof generation/verification
- `context_pipeline` — build → render → validate

CLI macro-benchmarks via hyperfine on the built `agy-ct` / `sparkctl` binaries.

## Output

- `benchmarks/reports/latest_divan.json`
- `benchmarks/reports/latest.json`
- `benchmarks/reports/cockpit.html` (static, self-contained)

## Claim Hygiene (Skill 05 — strictly observed)

This is a **lab-only** development tool.

- Operates exclusively on **synthetic** mock data.
- Provides **deterministic** measurements of packaging, Merkle proofs, and context construction on the provided fixtures.
- **No** claims of:
  - production readiness
  - EU AI Act compliance or certification
  - legal / forensic validity
  - performance guarantees outside this specific environment
- All results are **environment-specific** and for internal regression detection.
- Human review is required for any interpretation or decision.

See also the root `NOTICE.sparkctl.md`, `FEATURE_MERKLE.md`, and `crates/comptext-sparkctl` claim hygiene fields.

## CI

The GitHub Action (`.github/workflows/bench-regression.yml`) runs the harness and performs a simple >15% regression check against `benchmarks/reports/performance_baseline.json` (dummy on first run).

---

**Remember:** This infrastructure exists to support development of the CompText prototype. It does not constitute any form of certification or guarantee.
