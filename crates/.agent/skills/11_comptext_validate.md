# Agent Skill 11 — CompText Validation

This skill defines the verification process for checking generated local CompText-Sparkctl artifacts.

## 1. Input Files

Verification targets the presence and integrity of the following local files:
- `reports/latest.json`
- `reports/performance_baseline.json`
- `artifacts/spark/context.json`
- `artifacts/spark/context_render.txt`
- `artifacts/spark/extraction.spkg`

## 2. Validation Commands

Execute these commands inside `agy7rust/` to validate the files:
- `cargo run --bin agy-ct -- run`
- `cargo run --bin agy-ct -- context all`
- `python -m json.tool ../reports/latest.json`
- `python -m json.tool ../reports/performance_baseline.json`

## 3. Checklist

Verify each of the following:
1. **JSON Parsability:** Run `python -m json.tool` on `reports/latest.json` and `reports/performance_baseline.json` to confirm valid formatting.
2. **Artifact Existence:** Ensure that `context.json`, `context_render.txt`, and `extraction.spkg` exist in `artifacts/spark/`.
3. **Render Check:** Verify that the rendered context `context_render.txt` is non-empty and correctly formatted.
4. **Git Untracked State:** Confirm that the generated latest report `reports/latest.json` remains untracked in git.
5. **Ledger and Hash Chain Validation:** Verify that `ledger_root` matches the final entry hash in the cryptographic chain.
6. **Pre-Replay Validation Guardrail:** Ensure that package verification is executed as a prerequisite before running step simulations.
7. **Failure Label Analysis:** If validation or replay fails, map the error using structured labels:
   - `EVIDENCE_LOSS`: Critical metadata or tool sequence records are missing.
   - `CONSTRAINT_DRIFT`: Decoded state commits or hashes diverge from baseline values.

## 4. Standard Return Format

Validation results must be reported using the following format:
- `STATUS: <success | blocked>`
- `CHECKED_ARTIFACTS: <list of verified artifact files>`
- `MISSING_ARTIFACTS: <list of missing files if any>`
- `VALIDATION_NOTES: <validation details and verification summary>`
- `RISKS: <environmental risks or scheduling concerns>`
- `NEXT: <recommended next step>`
