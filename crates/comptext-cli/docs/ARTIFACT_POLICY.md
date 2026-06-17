# CompText CLI Artifact Policy

This document clarifies the classification, location, and Git tracking rules for all files generated or used during the execution of the CompText CLI (`ctxt`) tool.

## 1. Runtime State (.comptext/)
- **Classification**: Ignored runtime output.
- **Location**: `.comptext/` at the repository root.
- **Git Policy**: **Strictly ignored**. Must never be committed to the repository history.
- **Purpose**: Temporary workspace state and cache, including context packs (`context_pack.latest.json`), request skeletons (`model_request.latest.json`, `openai_request.latest.json`), responses (`model_response.latest.json`), and benchmarking reports (`benchmark.latest.json`).

## 2. Reviewable Change Proposals (proposals/)
- **Classification**: Ignored/generated runtime artifacts.
- **Location**: `proposals/` at the repository root.
- **Git Policy**: **Ignored by default**. The directory structure itself is preserved via `proposals/.keep`, but generated JSON proposals (such as `proposal.latest.json` and `proposal_*.json`) are listed in `.gitignore` to prevent cluttering the Git history during development.
- **Purpose**: Holds proposals containing targeted diffs and execution preconditions. They are reviewed prior to run-time execution of the `apply` command.

## 3. Phase Evidence (reports/)
- **Classification**: Committed audit evidence.
- **Location**: `reports/` at the repository root.
- **Git Policy**: **Tracked**. These files serve as permanent evidence of completed developmental milestones, including network constraints and validation command logs.
- **Purpose**: Documents phase reports and milestone tracking logs (e.g., `reports/phase_*_status.md`).
