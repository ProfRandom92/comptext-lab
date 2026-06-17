# Agent Runtime CLI

CompText CLI is not a replacement for Codex CLI or Antigravity CLI. It is a deterministic safety wrapper that prepares and records local agent runs before any external coding agent is allowed to act.

## Phase 1 Behavior

Phase 1 does not execute external agents.

`ctxt agent list` reports the agent kinds known to the runtime:

- `dummy`: local/offline placeholder.
- `codex`: external agent, dry-run-only in Phase 1.
- `antigravity`: external agent, dry-run-only in Phase 1.

`ctxt agent run --kind <kind> --task "<task>"` always creates a Context Pack and writes a run artifact at:

```text
.comptext/runs/latest/run.json
```

The artifact records the task, agent kind, context pack path, network policy, proposal policy, validation commands, timestamp, and safety flags.

## Safety Model

CompText keeps these boundaries in front of future agent execution:

- Context is packed deterministically before an agent run.
- Network remains denied by default.
- Proposal-before-apply remains required.
- Generated proposals are not applied automatically.
- External agents are not invoked unless a future phase adds an explicit execution gate.
- Phase 1 treats Codex and Antigravity runs as dry-run-only unless later phase flags are used.

## Phase 2 Behavior

Phase 2 adds execution plans only. It does not invoke Codex CLI, Antigravity CLI, or any other external agent.

`ctxt agent run --kind codex --task "<task>" --allow-external --proposal-only` and the matching `antigravity` command return an `execution-plan-only` JSON response. The run artifact records the same execution plan and confirms that no external process was invoked.

Proposal-only means:

- no apply
- no external process
- no network

This prepares the contract for future gated execution without changing the Phase 1 safety boundary.

## Phase 3 Behavior

Phase 3 adds discovery only.

`ctxt agent discover` lists the external agent kinds that CompText knows how to discover:

- `codex`
- `antigravity`

`ctxt agent discover --kind <kind>` scans local `PATH` metadata for the matching CLI binary. It does not execute external agents, does not execute version commands, does not use network, and does not apply proposals.

Version detection is deferred to a future gated capability because even a version check would invoke the external binary.

## Phase 4b Behavior

Phase 4b adds read-only, agent-friendly CLI introspection.

`ctxt --json capabilities` reports the stable machine-readable runtime capability surface, including supported phases, safety defaults, feature flags, and safe command families.

`ctxt --json runs list` lists first-class run references. Phase 4b exposes `latest` at:

```text
.comptext/runs/latest/run.json
```

`ctxt --json runs read latest --max-bytes 12000` and `ctxt --json runs read --id latest --max-bytes 12000` read that run artifact through a bounded interface. The default read limit is 12000 bytes.

These commands are read-only. They do not use network, do not invoke external agents, do not execute version commands, do not apply proposals, and do not add real external execution.

## Phase 4c Behavior

Phase 4c adds read-only JSON contract introspection.

`ctxt --json schema` reports stable machine-readable contract summaries for major JSON outputs:

- `capabilities`
- `runs list`
- `runs read`
- `agent discover`
- `agent run --allow-external --proposal-only`
- `validate`

The schema command returns static JSON only. It does not read files, write files, use network, invoke external agents, apply proposals, or add real external execution.

## Phase 4d Behavior

Phase 4d adds cross-agent compatibility guidance only.

`ctxt` is the common source of truth for Codex and Antigravity. Both agents must use the same safe JSON commands rather than separate runtime behavior:

```powershell
cargo run --bin ctxt -- --json schema
cargo run --bin ctxt -- --json capabilities
cargo run --bin ctxt -- --json runs list
cargo run --bin ctxt -- --json runs read latest --max-bytes 12000
cargo run --bin ctxt -- --json agent discover
cargo run --bin ctxt -- --json agent run --kind codex --task "..." --allow-external --proposal-only
cargo run --bin ctxt -- --json agent run --kind antigravity --task "..." --allow-external --proposal-only
cargo run --bin ctxt -- --json validate --run
```

Phase 4d does not add plugin packaging, MCP servers, hooks, network, apply, or real external execution. Antigravity guidance is an adapter to `ctxt`, not a separate runtime, policy, or execution system.

## Phase 4e Behavior

Phase 4e adds a read-only runtime startup report.

`ctxt --json self report` returns stable JSON summarizing the local `ctxt` runtime baseline, safe entrypoints, validation baseline, and cross-agent policy. It is intended as a useful first command for Codex and Antigravity sessions.

The self report command is static and read-only. It does not read files, write files, use network, invoke external agents, apply proposals, or add real external execution.

## Phase 4f Behavior

Phase 4f adds a read-only proposal artifact contract.

Proposal artifacts live under:

```text
proposals/<id>.json
```

The proposal ID is the filename stem. IDs must be safe ASCII slugs using letters, digits, `T`, `Z`, and hyphen. `latest` resolves to the lexicographically greatest safe `.json` filename in `proposals/`.

Safe proposal commands:

```powershell
ctxt --json proposals list
ctxt --json proposals inspect latest --max-bytes 12000
ctxt --json proposals inspect --id latest --max-bytes 12000
ctxt --json proposals validate latest
ctxt --json proposals validate --id latest
```

`ctxt --json proposals validate` checks the minimal `proposal.v1` contract: schema version, filename-matching ID, timestamp, phase, title, summary, intent, allowed files, forbidden scope, change list, validation list, network status, secrets statement, and proposal status.

Proposal artifacts are untrusted input. Inspection and validation are read-only, approval metadata does not apply changes, and apply behavior remains out of scope for Phase 4f.

## Phase 4g Behavior

Phase 4g adds proposal contracts to schema introspection.

`ctxt --json schema` now describes:

- `proposals list`
- `proposals inspect`
- `proposals validate`
- `proposal.v1 artifact`

Codex and Antigravity should inspect `ctxt --json schema` before using proposal commands. Phase 4g is read-only schema introspection only: no apply, network, external agents, hooks, MCP, plugin packaging, or real execution.

## Phase 4h Behavior

Phase 4h adds proposal support metadata to `ctxt --json capabilities`.

`ctxt --json capabilities` now advertises that proposal list, inspect, and validate are available as read-only JSON commands. Proposal apply and proposal generation remain unsupported.

Phase 4h is read-only capabilities introspection only: no apply, network, external agents, hooks, MCP, plugin packaging, or real execution.

## Phase 5a Behavior

Phase 5a adds a deterministic subagent role contract.

`ctxt --json subagents list` reports the reviewer roles that project work may reference:

- `schema-reviewer`
- `capabilities-reviewer`
- `proposal-reviewer`
- `test-reviewer`
- `docs-reviewer`
- `safety-reviewer`

These roles are static contracts only. `ctxt` does not execute subagents, start background tasks, invoke Codex CLI, invoke Antigravity CLI, call providers, use network, apply proposals, or perform git writes.

External tools may use subagents as deterministic review or planning helpers when the phase permits it, but `ctxt` itself only exposes the allowed role contracts. Every role is `contract-only`, may emit findings, risks, and recommendations, and may not edit files or run commands.

## Phase 5b Behavior

Phase 5b adds a deterministic review artifact contract.

Review artifacts live under:

```text
reviews/<id>.review.json
```

Safe review commands:

```powershell
ctxt --json reviews list
ctxt --json reviews inspect latest --max-bytes 12000
ctxt --json reviews inspect --id latest --max-bytes 12000
ctxt --json reviews validate latest
ctxt --json reviews validate --id latest
```

Review artifacts are local JSON evidence contracts only. They can record reviewer findings, risks, recommendations, validation references, and safety flags, but they are not workspace truth and must be treated as untrusted evidence until validated.

Phase 5b does not generate review artifacts, apply review recommendations, execute subagents, invoke Codex CLI, invoke Antigravity CLI, invoke external agents, use network, call providers, create hooks, create plugins, or start background tasks.

## Phase 5c Behavior

Phase 5c adds a deterministic startup review flow contract.

`ctxt --json startup flow` returns a static recommended sequence for safe Codex and Antigravity project sessions:

```powershell
ctxt --json self report
ctxt --json schema
ctxt --json capabilities
ctxt --json subagents list
ctxt --json proposals list
ctxt --json reviews list
ctxt --json validate --run
```

The startup flow is a contract-only checklist. It does not execute the flow, invoke Codex CLI, invoke Antigravity CLI, invoke external agents, use network, execute subagents, apply proposals, apply review recommendations, or perform git writes.

External tools may use `ctxt --json startup flow` as a deterministic startup checklist. They remain responsible for executing allowed commands one by one only when the active phase permits those commands.

## Phase 5d Behavior

Phase 5d adds a deterministic startup readiness contract.

`ctxt --json startup readiness` returns a static readiness report for the deterministic review workflow. It reports that review workflow contracts are ready and that external execution remains disabled.

The readiness report is not an execution gate. It does not execute commands, invoke Codex CLI, invoke Antigravity CLI, invoke external agents, use network, execute subagents, apply proposals, apply review recommendations, or perform git writes.

External tools may use `ctxt --json startup readiness` to decide whether the deterministic review workflow is available. `ready_for_review_workflow: true` does not imply external execution is allowed; `ready_for_external_execution: false` remains the hard boundary.

## Phase 5e Behavior

Phase 5e adds a deterministic review workflow contract.

`ctxt --json review workflow` returns a static checklist that connects startup readiness, startup flow, subagent role contracts, proposal artifacts, review artifacts, and `ctxt --json validate --run`.

The review workflow contract does not execute commands, read artifacts, apply proposals, apply review recommendations, invoke Codex CLI, invoke Antigravity CLI, invoke external agents, use network, execute subagents, or perform git writes.

External tools may use `ctxt --json review workflow` as a deterministic checklist for review work. The singular `review workflow` namespace is static workflow introspection; the plural `reviews` namespace remains the local review artifact interface.

## Future Phases

Later phases may add real Codex CLI or Antigravity CLI invocation behind explicit gates. Those phases should preserve the run artifact, keep JSON output machine-readable, and record provenance before and after external execution.
