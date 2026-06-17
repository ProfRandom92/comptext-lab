# CompText Runtime Contract

This document describes the current local `ctxt` runtime behavior on the
`fusion/ctxt-runtime-only` experiment branch.

The runtime support described here is experimental and local-only. It is not a
claim of production MCP support, full MCP compliance, full legacy DSL
compatibility, or universal token reduction.

## Command Matrix

| Command | Primary output | Success behavior | Error behavior |
| --- | --- | --- | --- |
| `ctxt parse <symbolic-command>` | stdout text, or stdout JSON with `--json` | Parses one symbolic command. | Non-zero exit; error text on stderr, or JSON error on stderr with `--json`. |
| `ctxt encode --command <name> --task <task> [--language <name>] [--modifier <name>]` | stdout text, or stdout JSON with `--json` | Emits an encoded symbolic command. | Non-zero exit; error text on stderr, or JSON error on stderr with `--json`. |
| `ctxt batch <batch-expression>` | stdout text, or stdout JSON with `--json` | Parses a local batch expression. | Non-zero exit; error text on stderr, or JSON error on stderr with `--json`. |
| `ctxt dsl validate <path>` | stdout text, or stdout JSON with `--json` | Validates the current local DSL fixture shape. | Invalid DSL reports are emitted on stdout JSON when `--json` is used, then the command exits non-zero. Runtime file-read failures use stderr errors. |
| `ctxt evidence hash <path>` | stdout text, or stdout JSON with `--json` | Hashes a local file after path validation. | Non-zero exit; error text on stderr, or JSON error on stderr with `--json`. |
| `ctxt mcp serve --allowed-root <path>` | JSON-RPC lines on stdout | Serves local stdio JSON-RPC requests under an explicit root. | JSON-RPC error objects on stdout for request-level MCP errors. Startup/runtime server failures use CLI stderr errors. |
| `ctxt detect-illegible-cot <path>` | stdout text, or stdout JSON with `--json` | Runs a deterministic phrase heuristic over a local trace file. | Non-zero exit; error text on stderr, or JSON error on stderr with `--json`. |

## Stdout, Stderr, And Exit Codes

Non-MCP commands write successful results to stdout. When `--json` is used,
successful command output is machine-readable JSON on stdout.

Non-MCP command errors are written to stderr. With `--json`, the current error
shape is:

```json
{
  "ok": false,
  "error": "short human-readable message"
}
```

Successful non-MCP commands exit `0`. Command validation failures, malformed
inputs, blocked paths, and failed local file reads exit non-zero.

`ctxt mcp serve --allowed-root <path>` is a stdio server. Request-level errors
are returned as JSON-RPC error responses on stdout instead of CLI stderr. A
malformed server invocation or server I/O failure still follows normal CLI error
handling.

## DSL Fixture Validation

`ctxt dsl validate <path>` validates a small local fixture subset only. It does
not claim full legacy DSL compatibility and does not execute skills, tools,
tasks, providers, shell commands, OAuth flows, network resources, or MCP tool
definitions.

The current accepted subset is:

| Syntax | Meaning |
| --- | --- |
| `use:<identifier>` | Counts a local use directive. |
| `$skill-name` | Counts a skill-shaped reference without invoking it. |
| `@workspace/path` | Counts a local resource-shaped reference without reading or resolving it. |
| `C;P:FIB` style lines | Parses a symbolic command using the existing symbolic parser. |

The validator rejects executable legacy semantics, including `tool { ... }`
blocks, `task { ... }` blocks, OAuth/network resource URLs, provider
declarations, and shell execution statements. With `--json`, the report includes
`subset: "local-fixture-v1"`, stable counts for accepted syntax, accepted syntax
labels, rejected semantic labels, and an ordered error list.

## MCP JSON-RPC Contract

MCP request responses use JSON-RPC-style objects:

```json
{
  "jsonrpc": "2.0",
  "id": "request id or null",
  "result": {}
}
```

MCP errors use this stable shape:

```json
{
  "jsonrpc": "2.0",
  "id": "request id or null",
  "error": {
    "code": -32602,
    "message": "short stable message",
    "data": {
      "kind": "stable_machine_kind",
      "detail": "bounded human detail"
    }
  }
}
```

Current MCP error kinds:

| Kind | Code | Meaning |
| --- | --- | --- |
| `parse_error` | `-32700` | Malformed JSON input. |
| `invalid_request` | `-32600` | Request is not a JSON object, or `method` is missing/non-string. |
| `method_not_found` | `-32601` | Unknown JSON-RPC method. |
| `invalid_params` | `-32602` | Known method with invalid parameter shape or values. |
| `access_denied` | `-32000` | Local access blocked before read. |
| `denied_sensitive_path` | `-32000` | Sensitive path component was denied. |
| `outside_allowed_root` | `-32000` | Canonical path resolved outside the allowed MCP root. |
| `file_too_large` | `-32000` | File exceeds the runtime maximum file size. |

Valid JSON-RPC notification objects without `id` produce no response line.
Malformed JSON is never treated as a notification and still returns
`parse_error`.

## Local File-Read Rules

Runtime file reads are local-only and bounded. File inputs must be relative
paths. Absolute paths and parent-directory traversal are denied before reads.

For runtime file commands, paths are canonicalized against the current worktree.
For MCP file reads, requested files are canonicalized against the explicit
`--allowed-root`. Canonical paths that resolve outside the allowed root are
denied.

Sensitive path components are denied before content is read. Sensitive names
include `.env` variants, credential-like filenames, private-key-like filenames,
and names containing token or secret markers.

Files larger than the runtime maximum file size are denied. MCP `max_bytes`
limits the returned byte range but does not bypass the maximum file-size gate.

MCP file-read results include a hash of the returned bytes, not a claim about
the full file when the returned content is truncated. The structured result
reports `sha256_scope: "returned_bytes"` for that reason.

`ctxt evidence hash <path>` hashes the validated local file bytes that are read
for that command. It does not read denied, sensitive, outside-root, traversal, or
oversized paths.

## Deterministic Validation Matrix

This matrix maps the current local runtime surface to deterministic evidence.
It is not an LLM judge, production-readiness claim, full MCP compliance claim,
full DSL compatibility claim, hidden chain-of-thought capture claim, or
universal token-reduction claim. Correctness is bounded to local command
outputs, stable JSON contracts, deterministic hashes, exact exit codes, smoke
tests, and `cargo test`.

| Capability | Command or test area | Positive evidence | Negative evidence | JSON contract evidence | Security boundary evidence | Current test names | Missing test gaps | Claim boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parse symbolic command | `ctxt parse <symbolic-command> --json` | Parses `C;P:FIB` into command, language, task, and raw fields. | Rejects invalid command code, invalid language segment, invalid modifier, duplicate language, missing task, malformed segments, and invalid task characters. | JSON object includes symbolic command fields and machine-readable JSON error on failure. | No file read, network, provider, shell, or apply path is involved. | `ctxt_parse_json_roundtrips_symbolic_command`; `ctxt_rejects_invalid_command_language_and_modifier`; `ctxt_rejects_ambiguous_and_malformed_symbolic_commands` | None for the current symbolic subset. | Validates only the local symbolic subset. |
| Encode symbolic command | `ctxt encode --command <name> --task <task> [--language <name>] --json` | Emits `C;P:FIB` for CODE/PYTHON/FIB and can report parsed JSON when JSON mode is used. | Rejects invalid language and missing required values through parser/command validation. | JSON mode returns `ok`, `encoded`, and `parsed`. | No file read, network, provider, shell, or apply path is involved. | `ctxt_encode_emits_expected_symbolic_command`; `ctxt_encode_json_reports_stable_shape`; `ctxt_rejects_invalid_command_language_and_modifier` | None for the current encode JSON shape. | Encodes only the local command/language/modifier vocabulary. |
| Batch symbolic expression | `ctxt batch <batch-expression> --json` | Parses `B:[D:SUM]\|[C;P:FIB]` into deterministic `SEQ` items. | Rejects missing `B:` prefix, unwrapped items, empty trailing items, and invalid nested symbolic commands. | JSON object includes `ok`, `mode`, and ordered `items`. | No file read, network, provider, shell, or apply path is involved. | `ctxt_batch_parses_items`; `ctxt_batch_rejects_malformed_items` | None for the current batch subset. | Batch is parsing only, not execution or scheduling. |
| DSL local-fixture-v1 validation | `ctxt dsl validate <path> --json` | Accepts `use:<identifier>`, `$skill-name`, local `@workspace/path`, and symbolic command fixture lines. | Rejects malformed skill/use/resource syntax, unsupported fixture lines, executable legacy `tool` and `task` blocks, URL resources, provider declarations, shell statements, traversal, and symlink escape where supported. | JSON report includes `ok`, `valid`, `subset`, `accepted_syntax`, `rejected_semantics`, `counts`, and ordered `errors`. | Runtime file input is relative, canonicalized under the worktree, size-bounded, sensitive-path denied, and UTF-8 checked. Resource-shaped lines are not read or resolved. | `ctxt_dsl_validate_accepts_basic_fixture`; `ctxt_dsl_validate_rejects_invalid_fixture`; `ctxt_dsl_validate_rejects_executable_legacy_semantics`; `ctxt_dsl_validate_rejects_symlink_escape_when_supported` | Consider a dedicated sensitive-path DSL fixture test if DSL fixture paths expand beyond current runtime input checks. | Fixture validation only; no full legacy DSL compatibility, skill execution, MCP tool execution, OAuth, network, provider calls, or task execution. |
| Evidence hash | `ctxt evidence hash <path> --json` | Produces stable SHA-256 for local files, including the empty-file vector. | Rejects sensitive names, traversal, and symlink escape where supported. | JSON includes `ok`, `algorithm`, normalized `path`, `bytes`, and `sha256`. | Runtime file input is relative, canonicalized under the worktree, size-bounded, and sensitive-path denied before read. | `ctxt_evidence_hash_is_stable_sha256`; `ctxt_evidence_hash_matches_empty_file_vector`; `ctxt_evidence_hash_rejects_sensitive_and_traversal_paths`; `ctxt_evidence_hash_rejects_symlink_escape_when_supported` | Add an oversized-file test if evidence hashing max-size behavior becomes a release gate. | Hashes only validated local bytes; no provenance or legal/compliance assurance. |
| MCP-style stdio file-read adapter | `ctxt mcp serve --allowed-root <path>` | Handles `initialize`, `tools/list`, and `tools/call` for `ctxt.read_file` under an explicit root. | Rejects malformed JSON, invalid request shape, missing/non-string methods, unknown methods, invalid params, traversal, sensitive paths, symlink escape where supported, outside-root paths, and oversized files. Notifications without `id` produce no response. | JSON-RPC responses include `jsonrpc`, `id`, `result`; errors include stable `code`, `message`, `data.kind`, and bounded `data.detail`. File reads report returned-byte hash scope. | Explicit allowed root, canonical containment, sensitive-path denial before and after canonicalization, max file-size gate, and `max_bytes` bounded returned content. | `ctxt_mcp_allows_rooted_file_read`; `ctxt_mcp_returns_structured_parse_error_for_malformed_json`; `ctxt_mcp_returns_structured_invalid_request_for_missing_method`; `ctxt_mcp_returns_structured_invalid_request_for_non_string_method`; `ctxt_mcp_notification_with_no_id_produces_no_response`; `ctxt_mcp_returns_structured_method_not_found`; `ctxt_mcp_returns_structured_invalid_params`; `ctxt_mcp_blocks_traversal`; `ctxt_mcp_blocks_sensitive_paths_without_reading_content`; `ctxt_mcp_blocks_symlink_escape_when_supported`; `ctxt_mcp_reports_returned_byte_hash_scope`; `ctxt_mcp_blocks_file_too_large` | Add additional invalid `max_bytes` edge cases if the adapter contract expands. | Local stdio adapter only; no full MCP compliance, network transport, OAuth, provider calls, shell execution, or general filesystem access. |
| Trace heuristic detection | `ctxt detect-illegible-cot <path> --json` | Flags deterministic phrase fixtures and reports finding IDs, and reports no findings for a clean trace fixture. | File-read errors follow runtime input validation. | JSON includes `ok`, `detected`, `findings`, and `scope`. | Runtime file input is relative, canonicalized under the worktree, size-bounded, sensitive-path denied, and UTF-8 checked. | `ctxt_detect_illegible_cot_flags_trace_fixture`; `ctxt_detect_illegible_cot_reports_clean_trace` | Add sensitive/traversal tests if trace triage becomes a release gate. | Phrase heuristic only; no hidden chain-of-thought capture or correctness claim about model reasoning. |
| Proposal contract behavior | `ctxt proposals list/inspect/validate --json` | Lists valid proposal artifacts, inspects bounded proposal content, accepts valid `proposal.v1`, and supports `latest` positional and `--id latest`. | Rejects missing required fields, id mismatch, malformed JSON, traversal IDs, invalid `max_bytes`, and duplicate IDs. | JSON contracts are discoverable through `ctxt --json schema` and `ctxt --json capabilities`; proposal command outputs include command identity, schema version, validity, paths, and errors. | Proposal artifacts are untrusted local files; inspection is bounded; validation does not apply changes. | `proposals_list_missing_root_returns_empty`; `proposals_list_shows_valid_proposal`; `proposals_inspect_latest_reads_proposal_object`; `proposals_inspect_latest_flag_id_matches_positional`; `proposals_validate_latest_accepts_valid_contract`; `proposals_validate_latest_flag_id_accepts_valid_contract`; `proposals_validate_missing_required_field_returns_invalid`; `proposals_validate_id_mismatch_returns_invalid`; `proposals_validate_malformed_json_returns_invalid`; `proposals_reject_path_traversal_id_with_json_error`; `proposals_reject_invalid_max_bytes_with_json_error`; `proposals_reject_duplicate_id_with_json_error`; `schema_json_reports_proposal_contract_details`; `capabilities_json_reports_proposal_capabilities` | Add proposal artifact size-limit tests if proposal inspection limits become a release gate. | Contract validation only; no approval, generation, apply, provider, network, or git action. |
| Review contract behavior | `ctxt reviews list/inspect/validate --json`; `ctxt review workflow --json` | Lists valid review artifacts, inspects bounded review content, accepts valid `review.v1`, validates workflow contract, and reports disabled execution/apply flags. | Rejects missing required fields, id mismatch, malformed JSON, traversal IDs, invalid `max_bytes`, duplicate IDs, invalid role IDs, safety flags set to true, and unsupported review workflow commands. | JSON contracts are discoverable through `ctxt --json schema`; review outputs include command identity, schema version, validity, role IDs, safety flags, and errors. | Review artifacts are untrusted local evidence; inspection is bounded; runtime does not execute subagents, generate reviews, apply recommendations, use network, or write git history. | `reviews_list_missing_root_returns_empty`; `reviews_list_shows_valid_review`; `reviews_inspect_latest_reads_review_object`; `reviews_inspect_latest_flag_id_matches_positional`; `reviews_validate_latest_accepts_valid_contract`; `reviews_validate_latest_flag_id_accepts_valid_contract`; `reviews_validate_missing_required_field_returns_invalid`; `reviews_validate_id_mismatch_returns_invalid`; `reviews_validate_malformed_json_returns_invalid_and_listable`; `reviews_reject_path_traversal_id_with_json_error`; `reviews_reject_invalid_max_bytes_with_json_error`; `reviews_reject_duplicate_id_with_json_error`; `reviews_validate_true_safety_flag_returns_invalid`; `reviews_validate_invalid_role_id_returns_invalid`; `reviews_unknown_commands_fail_with_json_errors`; `review_workflow_json_reports_static_contract`; `review_workflow_unknown_commands_fail_with_json_errors`; `schema_json_reports_review_contract_details`; `schema_json_reports_review_workflow_contract_details` | Add bounded-size review artifact tests if inspection limits become a release gate. | Contract-only review workflow; no subagent execution, LLM judge, apply, provider, network, or git action. |
| Provider dry-run and network-deny behavior | `ctxt ask/propose/benchmark/agent run` provider-related smoke tests | Dummy provider paths succeed locally; dry-run reports artifacts without provider call; proposal-only agent run returns execution plans when explicitly allowed. | Ollama respects network-deny policy; unsupported benchmark provider is rejected; external agent run defaults to dry-run for Codex and Antigravity. | JSON outputs report provider/artifact fields, safety flags, and execution-plan fields in covered paths. | Network default deny, provider output treated as untrusted, external agents not invoked by default, and proposal-only mode does not apply changes. | `ask_json_dry_run_reports_artifacts_without_provider_call`; `ask_dummy_provider_succeeds`; `ask_ollama_provider_respects_network_deny_policy`; `propose_dummy_provider_succeeds`; `propose_json_reports_proposal_artifacts`; `agent_run_dummy_writes_run_artifact`; `agent_run_codex_is_dry_run_by_default`; `agent_run_antigravity_is_dry_run_by_default`; `agent_run_codex_allow_external_proposal_only_returns_execution_plan`; `agent_run_antigravity_allow_external_proposal_only_returns_execution_plan`; `unknown_agent_kind_fails_with_json_error`; unit tests `provider::tests::test_openai_fails_closed_without_network`, `provider::tests::test_openai_no_network_call_made`, `provider::tests::test_openai_request_serialization_shape`, `provider::tests::test_ollama_local_offline_error`, `provider::tests::test_ollama_missing_auth_env`, `cli::tests::test_unsupported_provider_benchmark_rejected` | Add explicit JSON assertions for every safety flag if these paths become external-review gates. | Local dry-run/network-deny evidence only; no live provider correctness, performance, production, or availability claim. |

Validation for this matrix is `cargo fmt --check`, `cargo test`, stable JSON
smoke tests, deterministic hashes, exact exit codes, and git status. Claims
outside those checks remain out of scope.
