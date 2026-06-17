# Roadmap

## Phase 0 — Repo Genesis

Create clean Rust/Cargo scaffold, docs, skills, CI, and static CLI commands. No provider calls.

## Phase 1 — CLI Shell

Commands:

```bash
ctxt --help
ctxt doctor
ctxt providers list
ctxt version
```

## Phase 2 — Context Pack Contract

Commands:

```bash
ctxt context inspect
ctxt context pack --task "..."
```

## Phase 3 — Ask Dry-run

Command:

```bash
ctxt ask --dry-run "How do I test this repo?"
```

Output only, no provider call:

```text
.comptext/model_request.latest.json
```

## Phase 4 — Dummy Provider

Offline request/response pipeline.

## Phase 5 — Ollama Adapter

Variants:

- `ollama-local`
- `ollama-cloud-via-local`
- `ollama-cloud-direct`

## Phase 6 — OpenAI-Compatible Provider

Generic normalized adapter.

## Phase 7 — Proposal Mode

`ctxt propose --provider ... "..."` writes inspectable proposals only.

## Phase 8 — Apply Gate

`ctxt apply proposals/...` applies selected proposals only after policy checks.

## Phase 9 — Validate and Benchmark

Local validation and deterministic benchmark flows.
