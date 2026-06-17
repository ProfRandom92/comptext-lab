# Import bases

## comptext-cli
Basis: `pr-5-runtime-autonomy`

Reason:
- Runtime autonomy branch passed local `cargo check` and `cargo test`.
- Contains runtime contract, runtime.rs, CLI smoke coverage, examples, and release-readiness checks.

## comptext-sparkctl
Basis: `main`

Additional import:
- `pr-13` / `origin/license-claim-hygiene`
- Imported license/non-claim files:
  - `LICENSE.sparkctl-repo`
  - `LICENSING.sparkctl.md`
  - `NOTICE.sparkctl.md`
  - `THIRD_PARTY_LICENSES.sparkctl.md`
  - `crates/comptext-sparkctl/LICENSE`

Reason:
- `main` already contains the current Rust crate, SPARK evidence packet, PDF extraction contract, CLI surface, and tests.
- Older PR feature branches show large negative diffs against current main and are not suitable import bases.

## Comptextv7
Basis: `main`

Reason:
- Latest PR comparison showed `pr-218` empty against `main`, so `main` is the safest current import base.
- `pr-213` cleanup was reviewed, but using it as full basis may regress newer main changes.
- Stale `showcase/` and `GEMINI.md` are excluded from the monorepo import if present.

## comptext-air
Basis: `main`

Reason:
- Only visible PR is Dependabot `actions/checkout` bump.
- No schema/core import value from that PR.
