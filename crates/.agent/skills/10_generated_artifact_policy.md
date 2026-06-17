# Agent Skill 10 - Generated Artifact Policy

This skill records how Codex sessions should handle generated CompText artifacts.

## Non-Commit Defaults

Generated runtime files are not automatically commit candidates:

- `reports/latest.json`
- `reports/performance_baseline.json`
- `artifacts/spark/*`
- Rust `target/` outputs

Do not stage or commit generated reports unless the human explicitly approves the exact files.

## Artifact Hygiene

- Prefer validation commands that do not regenerate reports when the task does not require new artifacts.
- Do not run `agy-ct run` or `agy-ct benchmark` during governance-only work.
- Treat generated artifacts as evidence trail material, not source-of-truth implementation.
- Preserve deterministic and replayable outputs; do not fake hashes or rewrite reports to satisfy a claim.

## Claim Hygiene

Generated reports and handoff text may describe local validation results, deterministic packaging behavior, and tamper-sensitive checks when evidenced by commands. They must not claim production readiness, legal proof, forensic certainty, EU AI Act compliance, official SPARK compatibility, or autonomous approval.
