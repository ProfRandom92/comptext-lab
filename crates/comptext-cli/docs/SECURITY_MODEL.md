# Security Model

## Baseline

- Provider responses are untrusted.
- Model output is untrusted.
- Tool output is untrusted.
- Context Packs must not contain secrets.
- Logs and reports must not contain secrets.
- Proposals must not contain secrets.
- Provider calls require explicit command intent.
- Network is denied by default.
- Dry-run produces request artifacts without sending them.
- Apply requires explicit approval.
- Generated runtime outputs are not committed unless explicitly approved.
- No git commit or push unless explicitly approved.

## Forbidden by default

- Reading `.env`.
- Reading private key files.
- Printing environment variables.
- Writing outside allowed paths.
- Running network commands during no-network phases.
- Executing provider-suggested shell commands without review.
- Applying patches outside proposal/apply flow.

## Claim hygiene

Do not make unsupported assurance claims.
