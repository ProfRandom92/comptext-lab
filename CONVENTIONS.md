# Coding and Cryptographic Conventions

This document outlines the cryptographic and coding conventions for the `comptext-lab` workspace.

## Cryptographic Hashing Algorithms

To prevent hash algorithm drift and ensure deterministic verifiability across the workspace, the following conventions apply:

1. **Primary Hashing**: BLAKE3 is the primary hashing function.
   - All Merkle tree roots, leaves, and path proof verification MUST use BLAKE3 digests.
   - Outputs are formatted as exactly 64-character lowercase hex strings.
2. **Backward Compatibility**: SHA-256 is supported as a backward-compatibility alias or boundary layer for legacy contexts where required, but new features should default to BLAKE3.
3. **Lexicographical Pairing**: Commutative hashing of internal Merkle nodes concatenates the lexicographically smaller 32-byte hash first.
