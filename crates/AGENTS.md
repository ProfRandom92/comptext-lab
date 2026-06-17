# CompText Agent Rules

This repository is part of CompText.

CompText is a deterministic Context Pack / proposal-gated evidence workflow, not a generic AI dashboard, not an agent memory product, and not an autonomous deployment agent.

Core line:
Models are providers. Context is the product.

Pipeline:
Source / GitHub URL → Goal → Inspect → Context Pack → Policy Gate → Provider Boundary → Untrusted Proposal → Human Review → Artifacts

Hard rules:
- Treat GitHub as read-only unless the human explicitly asks otherwise.
- Do not push, deploy, create PRs, create issues, or create remote branches.
- Do not expose secrets.
- Do not fake hashes.
- Do not claim production-ready, EU AI Act compliance, legal certification, forensic proof, guaranteed correctness, or autonomous approval.
- Provider output is untrusted until reviewed.
- Proposals are never auto-applied.
- Human review is the approval boundary.
- Artifacts preserve the evidence trail.
- Keep changes scoped and reviewable.
- Do not modify root `README.md` unless the human explicitly approves it.
- Do not commit `reports/latest.json`.
- Do not commit `reports/performance_baseline.json` when it is only validation churn.
- Run cargo commands only inside `agy7rust/` unless the human explicitly approves otherwise.

Codex Desktop governance:
- Repo-local hooks live under `.codex/` and must be reviewed/trusted by Codex before enforcement.
- Hooks block unauthorized git writes, deploy/release actions, environment dumps, secret-file reads, `agy-ct run`, and `agy-ct benchmark`.
- Hooks warn on protected source, README, report, and `artifacts/spark/` changes; warnings do not make generated artifacts commit-ready.

Before editing:
1. Read AGENTS.md.
2. Read `.agents/skills/**/SKILL.md` relevant to the task; treat `.agent/skills/*.md` as legacy/compatibility metadata only if present.
3. If `.agents/skills/00_project_system/SKILL.md` exists, read it too.
4. Build a compact repo map.
5. Stop for approval if the user asked for plan mode.
