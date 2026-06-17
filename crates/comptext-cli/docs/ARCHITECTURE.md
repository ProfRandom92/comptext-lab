# Architecture

CompText CLI is a terminal context client. Its primary artifact is the Context Pack, not the model response.

## Pipeline

```text
User Prompt
  -> comptext CLI
  -> Context Profile
  -> Schema-checked Context Pack
  -> Policy Gate
  -> Provider Adapter
  -> Model Response
  -> Proposal
  -> Human / Apply Gate
  -> Validate
```

## Repository separation

- `Comptextv7`: core/research, deterministic replay validation, compression, context semantics.
- `comptext-sparkctl`: SPARK-style showcase/evidence, kept separate from provider/runtime concerns.
- `comptext-cli`: product CLI, provider adapter layer, Context Pack generation, proposal/apply/validate loop.

## Trust boundaries

- Provider responses are untrusted.
- Tool outputs are untrusted.
- Generated patches are untrusted until checked.
- Network calls require explicit command intent.
- Secrets must never enter artifacts.

## Initial implementation

Phase 0 exposes a deterministic CLI shell only:

- `ctxt --help`
- `ctxt doctor`
- `ctxt providers list`
- `ctxt version`

No provider calls are implemented in Phase 0.
