# Merkle Proof API (Sparkctl V3)

Worktree: `feature/merkle-proof` in `comptext-lab-feature-merkle`.

## Public API (`agy7rust`)

- `generate_manifest_merkle_proof` / `verify_manifest_merkle_proof`
- `generate_ledger_merkle_proof` / `verify_ledger_merkle_proof`
- `proof_to_hex` / `proof_from_hex` (`MerkleProofHex`)
- `MerkleTree`, `MerkleProof`, `verify_proof_hash`

## CLI

```bash
sparkctl merkle manifest-proof -i evidence.json --index 0 -o proof.json
sparkctl merkle verify-manifest --root <hex> --leaf <hex> -i proof.json
sparkctl merkle ledger-proof -i package.json --index 0
sparkctl merkle verify-ledger --root <hex> --entry <hex> -i proof.json
```

## Merge Readiness

1. `cargo test -p agy7rust` (full suite)
2. Review diff vs `comptext-lab` main
3. Local merge: `git checkout <target> && git merge feature/merkle-proof`
4. No remote push without explicit approval (AGENTS.md)