# Agent Skill 06 — Git Handoff

This skill outlines guidelines for staging, committing, and handoff actions.

## 1. Operating Rules (Requires Explicit User Approval)

- **No Auto-Git Actions:** Do not perform git init, add, commit, push, checkout, pull, or merge unless explicitly requested.
- **Stage Allowed Paths Only:** If staging changes, add only the files belonging to the active phase scope. Do NOT run wildcard stages (e.g. `git add .` or `git add -A`) to avoid staging build target outputs or untracked local test files.
- **Dry-Run Review:** List all files to be staged for staging verification before committing:
  ```bash
  git status --short
  ```
- **Safety Boundaries:**
  - Never run force push (`git push -f` or `git push --force`).
  - Do not delete branches or rewrite commit history unless instructed.

## 2. Pull Request Template

When describing work for PRs or commits, use the template below:
```text
feat(<scope>): SPARK Hackathon <phase_name>

Summary:
- Brief bulleted list of changes

Validation:
- Test suite status
- Clippy and cargo format checks
```
