# CompText V7 Agent Instructions

## Repo-local skill docs
- Before starting work, read the relevant docs under `docs/codex_skills/`.
- Use `docs/codex_skills/mcp_context_layer.md` for MCP context layer, CLI, prompt rendering, validation, and adapter work.
- Use `docs/codex_skills/artifact_validation.md` for deterministic artifacts and regeneration checks.
- Use `docs/codex_skills/git_pr_workflow.md` for branch sync, commits, pushes, and PR preparation.
- Use `docs/codex_skills/docs_positioning.md` for README/docs positioning and scope boundaries.

## Default safety rules
- Repository state is the source of truth.
- Inspect before editing.
- Make the smallest safe patch.
- Keep behavior deterministic and fixture-bound.
- Maintain local sanitization and privacy boundaries (GDPR/DSGVO Art. 25) at all times.
- Do not introduce semantic scoring, embeddings, vector DBs, external APIs, autonomous orchestration, or runtime tool execution unless explicitly scoped.
- Prefer focused validation over broad checks unless the task requires broader validation.
- Do not commit, push, create PRs, or merge unless explicitly requested.

## Project focus
- CompText V7 is the deterministic replay-integrity layer for compressed operational agent traces.
- Current focus: core foundation, deterministic replay artifacts, CI artifacts, docs, and conservative positioning.
- Showcase work belongs in the separate showcase repository and must not be reintroduced here unless explicitly approved.
- Chilli/Hatch/Pet assets must not be touched unless explicitly requested.

## Non-goals
- No LLM judging.
- No embeddings.
- No vector DBs.
- No external APIs.
- No graph stores.
- No runtime autonomous agent execution.
- No benchmark logic changes unless explicitly requested.
- No production-ready / clinical-grade / solved-memory claims.

## PR discipline
- Keep PRs small and focused.
- Prefer docs-only PRs for positioning work.
- Core logic PRs require tests.
- Do not mix showcase, docs, and core refactors in one PR.
- Use Draft PRs until CI and review threads are clean.
- Do not mark ready until Actions are green and review threads are resolved/outdated.

## Task shape
- Use one concrete goal per task.
- Name exact files or narrow paths that may change.
- Keep instructions short and testable.
- Split unrelated changes into separate PRs.
- For test-only work, change only the target test file unless another file is required.
- For fixture work, keep generation and validation in separate PRs.
- If the task becomes unclear, leave a blocker comment instead of expanding scope.

## Task template
Task:
- One concrete change.

Allowed files:
- Exact files or narrow paths.

Steps:
- 3-6 explicit steps.

Tests:
- Exact commands.

Done when:
- Objective acceptance criteria.

## Validation
- Prefer cloud CI as source of truth.
- Do not claim local validation unless commands actually ran.
- Standard commands:
  - npm run layout
  - npm run typecheck
  - npm test
  - npm run check
- For targeted TS/Python bridge tests, run the specific pytest file too.

## Output format
Every agent PR summary must use:
Summary:
Changed files:
Testing:
Risks:
Next:

## Visibility requirement
- Work incrementally.
- Push after each meaningful change.
- Comment after each push with:
  Progress:
  - changed files
  - what was fixed
  - tests actually run
  - remaining issues
  - current blocker, if any
- If stuck, comment with current blocker instead of staying silent.
