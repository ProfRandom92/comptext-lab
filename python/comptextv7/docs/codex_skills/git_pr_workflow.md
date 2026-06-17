# Git PR Workflow Skill

## Purpose

Handle CompTextv7 branch sync, local commits, pushes, and pull-request setup with staged-file discipline.

## When to use

Use for branch setup, syncing from `main`, local commits, staged-file review, pushing current branches, PR creation, and CI follow-up.

## Allowed actions

- Inspect `git status --short` before git operations.
- Use non-destructive git commands.
- Stage only explicitly allowed paths.
- Show staged files with `git diff --cached --name-only` before committing.
- Commit only after staged files match the requested scope.
- Push only when explicitly requested and the working tree is clean.
- Create a PR only when explicitly requested and GitHub CLI is available and authenticated.

## Forbidden actions

- No force push.
- No merge unless explicitly requested.
- No branch deletion.
- No destructive commands such as `git reset --hard` or `git clean -fd`.
- No changing commits unless explicitly requested.
- No commit or push unless explicitly requested.

## Required validation

- Before commit: `git status --short`, `git diff --stat`, and `git diff --cached --name-only`.
- Before push: clean `git status --short` and current branch confirmation.
- For PRs: include validation commands actually run; do not claim CI status unless checked.
- For agent-assisted pre-push or pre-PR checks, run `python scripts/safe_pr_gate.py` on the current branch before pushing.

## Stop conditions

- Stop if working tree contains unrelated changes.
- Stop if staged files exceed the allowed scope.
- Stop if GitHub CLI is missing or unauthenticated; print manual commands.
- Stop if sync or push fails.

## Preferred prompt pattern

```text
Task: create a local commit or PR for current scoped changes.
Allowed files: exact paths.
Validation already run: exact commands.
Steps: status, stage exact files, show staged list, commit/push only if scoped.
Done when: local commit or PR is created, no merge performed.
```
