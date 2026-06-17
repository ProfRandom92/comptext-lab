# Provider Adapters

Providers are transport/model backends. They are not trusted execution authorities.

## Planned providers

| Provider | Network | Auth | Purpose |
|---|---:|---|---|
| `dummy` | no | none | offline tests |
| `ollama-local` | explicit | none | local Ollama API at `http://localhost:11434` |
| `ollama-cloud-via-local` | explicit | local Ollama sign-in | cloud models routed through local Ollama using `*-cloud` models |
| `ollama-cloud-direct` | explicit | `OLLAMA_API_KEY` | direct hosted API at `https://ollama.com` |
| `openai-compatible` | explicit | configured env var | compatible APIs, including local compatibility layers |
| `future-openai` | explicit | TBD | future dedicated adapter |
| `future-gemini` | explicit | TBD | future dedicated adapter |
| `custom` | explicit | configured | user-defined adapters |

## Rules

- `ask --dry-run` must be available before real provider calls.
- Provider network requires explicit command intent.
- Provider responses are untrusted.
- API keys must never be printed, logged, packed, proposed, snapshotted, or committed.

## OpenAI-Compatible Adapter

Exposes an OpenAI-compatible adapter skeleton (`kind = "openai-compatible"`).

### Configuration Options

The following fields can be defined inside `comptext.toml` (or `comptext.example.toml`):
- `kind`: Must be set to `"openai-compatible"`.
- `base_url`: Endpoint URL, e.g. `"http://localhost:11434/v1"`.
- `model`: Optional target model name, defaults to `"gpt-4o"`.
- `auth_env`: Optional environment variable name holding the API key (metadata only in current MVP).
- `network`: Policy switch (`true` or `false`). Defaults to `true` if not specified.

### Behavior & Security Limits

- **Offline Safe MVP**: The adapter skeleton operates fully offline to prevent unexpected network requests during development/dry-runs.
- **Request Serialization**: Generates a normalized chat completion request payload saved to `.comptext/openai_request.latest.json` on dry-runs or executions.
- **Fail-Closed Network Guard**: Blocks execution if `allow_provider_network` is disabled globally or if the provider's `network` setting is false.
- **Secrets Redaction**: Systematically redacts secrets from metadata listings and outputs.

