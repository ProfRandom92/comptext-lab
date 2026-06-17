# Agent Skill 10 — SPARK Evidence Review

This skill defines the requirements and checklist for reviewing the README-linked demo evidence and local baseline artifacts of the CompText-Sparkctl toolkit.

## 1. Input Files

The reviewer path verifies the presence of the following files:
- `README.md`
- `DEMO_SPARK_EVIDENCE.md`
- `PERFORMANCE_BASELINE.md`
- `reports/performance_baseline.json`
- `artifacts/spark/context.json`
- `artifacts/spark/context_render.txt`

## 2. Review Commands

Reviewers should execute and inspect the output of these commands inside `agy7rust/`:
- `cargo run --bin agy-ct -- run`
- `python -m json.tool ../reports/latest.json`
- `python -m json.tool ../reports/performance_baseline.json`

## 3. Checklist

Verify each of the following:
1. **File Presence:** Ensure all input files exist at their expected locations under the workspace directory.
2. **JSON Parsability:** Run `python -m json.tool` on the JSON reports to guarantee they are correctly structured.
3. **Reviewer Path Clarity:** Confirm that `README.md` contains clear links to the demo evidence documents, and the reviewer path is easy to follow.
4. **Claim Hygiene:** Ensure all documents strictly avoid prohibited assertions (such as official specification compatibility, production/enterprise setup readiness, and regulatory certifications).

## 4. Standard Return Format

The results of this review must be reported using the following format:
- `STATUS: <success | blocked>`
- `EVIDENCE_FILES: <list of verified files>`
- `COMMANDS_CHECKED: <list of executed command lines>`
- `CLAIM_HYGIENE: <hygiene verification note>`
- `REVIEWER_SUMMARY: <concise summary of findings>`
- `RISKS: <local environmental or scheduling risks>`
- `NEXT: <recommended next step>`
