# CompText CLI Terminal Demo

This page documents the small VHS terminal demo asset for CompText CLI. The demo is intended for README and release-candidate review use: it shows the local JSON-oriented command surface without changing runtime code.

## Purpose

The demo gives reviewers a short visual pass through the commands that describe startup readiness, capabilities, review workflow, and local validation.

The script is stored as a VHS tape at `assets/demo/ctxt-demo.tape`. VHS keeps the terminal demo encoded as text so the commands, timing, dimensions, and output target are reviewable before a GIF is rendered.

## Demo Commands

```powershell
cargo run --bin ctxt -- --json startup readiness
cargo run --bin ctxt -- --json capabilities
cargo run --bin ctxt -- --json review workflow
cargo run --bin ctxt -- --json validate --run
```

These commands are local CLI invocations. They do not call providers, enable network access, execute external agents, execute subagents, apply proposals, or change runtime behavior.

## Preview And Render

VHS must be installed locally before rendering.

```powershell
vhs --version
vhs assets/demo/ctxt-demo.tape
```

The tape is configured to write `assets/demo/ctxt-demo.gif`. Rendering is optional for the repository: if the GIF is larger than 5 MB or rendering fails, keep only the text tape and documentation.

The intended visual style is a dark terminal window suitable for a compact README demo. Runtime duration can vary because the tape runs `cargo run` commands against the local checkout.

Current local render note: `vhs --version` reported `vhs version v0.11.0 (c6af91a)`, but `vhs assets/demo/ctxt-demo.tape` failed because `ttyd` is not installed. No GIF was committed for this attempt.

## Boundaries

- No secrets are required or expected.
- No network is required by the demo commands.
- No provider calls are part of the demo.
- No runtime-code changes are part of the demo asset plan.
- Generated media should be treated as optional review material, not source of truth.
