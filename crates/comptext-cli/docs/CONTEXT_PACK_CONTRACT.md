# Context Pack Contract

A Context Pack is a deterministic, schema-checked payload prepared before any provider call.

## MVP shape

```json
{
  "schema_version": "0.1",
  "task": "...",
  "mode": "ask",
  "repo_profile": "default",
  "read_first": [],
  "included_files": [],
  "excluded_files": [],
  "allowed_write_paths": [],
  "forbidden_actions": [],
  "validation_commands": [],
  "provider": null,
  "rendered_context": "...",
  "policy": {
    "secrets_redacted": true,
    "generated_outputs_excluded": true,
    "patch_requires_approval": true
  }
}
```

## Determinism rules

- Sort object keys recursively.
- Avoid timestamps unless normalized.
- Avoid hostnames, process IDs, absolute local paths, and machine-specific cache paths.
- Exclude generated runtime outputs by default.
- Redact secrets before writing any artifact.

## Outputs

Planned default outputs:

- `.comptext/context_pack.latest.json`
- `.comptext/model_request.latest.json`

These outputs are runtime artifacts and should not be committed by default.
