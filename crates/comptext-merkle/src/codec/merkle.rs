//! BLAKE3 Merkle tree with **sorted pair hashing**.
//!
//! Internal nodes hash two child digests with BLAKE3, always concatenating the
//! lexicographically smaller 32-byte hash first. This commutative pairing works
//! for both `from_leaves` (BLAKE3 over raw bytes) and `from_hashes` (pre-hashed
//! leaves such as artifact `sha256` or ledger `entry_hash` values).

use blake3;
use serde::{Deserialize, Serialize};

use crate::codec::hex::{decode_blake3_hex, encode_hex_32};

pub type Hash = [u8; 32];

#[derive(Debug, Clone)]
pub struct MerkleTree {
    pub root: Hash,
    leaves: Vec<Hash>,
}

impl MerkleTree {
    /// Build a tree from raw leaf bytes (each leaf is BLAKE3-hashed first).
    pub fn from_leaves(leaves: &[&[u8]]) -> Self {
        let hashes: Vec<Hash> = leaves.iter().map(|l| blake3::hash(l).into()).collect();
        Self::from_hashes(hashes)
    }

    /// Build a tree from pre-computed 32-byte leaf digests (manifest/ledger path).
    pub fn from_hashes(mut hashes: Vec<Hash>) -> Self {
        if hashes.is_empty() {
            return Self {
                root: [0u8; 32],
                leaves: vec![],
            };
        }
        let leaves = hashes.clone();
        while hashes.len() > 1 {
            let mut next_level = vec![];
            for chunk in hashes.chunks(2) {
                let left = chunk[0];
                let right = if chunk.len() > 1 { chunk[1] } else { left };
                let h = hash_pair(left, right);
                next_level.push(h);
            }
            hashes = next_level;
        }
        Self {
            root: hashes[0],
            leaves,
        }
    }

    pub fn root(&self) -> Hash {
        self.root
    }

    pub fn leaf_count(&self) -> usize {
        self.leaves.len()
    }

    /// Generate a Merkle proof for the leaf at `index`, returning an error instead of panicking.
    pub fn try_generate_proof(&self, index: usize) -> anyhow::Result<MerkleProof> {
        if index >= self.leaves.len() {
            return Err(anyhow::anyhow!(
                "merkle proof index out of range: index {} len {}",
                index,
                self.leaves.len()
            ));
        }
        let mut proof_path = vec![];
        let mut level = self.leaves.clone();
        let mut idx = index;
        while level.len() > 1 {
            let sibling_idx = if idx.is_multiple_of(2) {
                idx + 1
            } else {
                idx - 1
            };
            if sibling_idx < level.len() {
                proof_path.push(level[sibling_idx]);
            } else {
                proof_path.push(level[idx]);
            }
            let mut next = vec![];
            for i in (0..level.len()).step_by(2) {
                let left = level[i];
                let right = if i + 1 < level.len() {
                    level[i + 1]
                } else {
                    left
                };
                next.push(hash_pair(left, right));
            }
            level = next;
            idx /= 2;
        }
        Ok(MerkleProof {
            leaf_hash: self.leaves[index],
            proof_path,
            root_hash: self.root,
        })
    }

    /// Backward-compatible wrapper around [`Self::try_generate_proof`].
    pub fn generate_proof(&self, index: usize) -> MerkleProof {
        self.try_generate_proof(index)
            .expect("merkle proof index out of range")
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MerkleProof {
    pub leaf_hash: Hash,
    pub proof_path: Vec<Hash>,
    pub root_hash: Hash,
}

/// Hex-encoded, JSON-serializable representation of a [`MerkleProof`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MerkleProofHex {
    pub leaf_hash: String,
    pub proof_path: Vec<String>,
    pub root_hash: String,
}

pub fn proof_to_hex(proof: &MerkleProof) -> MerkleProofHex {
    MerkleProofHex {
        leaf_hash: encode_hex_32(&proof.leaf_hash),
        proof_path: proof.proof_path.iter().map(encode_hex_32).collect(),
        root_hash: encode_hex_32(&proof.root_hash),
    }
}

pub fn proof_from_hex(hex: &MerkleProofHex) -> anyhow::Result<MerkleProof> {
    Ok(MerkleProof {
        leaf_hash: decode_blake3_hex("leaf_hash", &hex.leaf_hash)?,
        proof_path: hex
            .proof_path
            .iter()
            .enumerate()
            .map(|(i, h)| decode_blake3_hex(&format!("proof_path[{i}]"), h))
            .collect::<Result<Vec<_>, _>>()?,
        root_hash: decode_blake3_hex("root_hash", &hex.root_hash)?,
    })
}

/// Verify a proof for a raw leaf (BLAKE3-hashed before tree ascent).
pub fn verify_proof(leaf: &[u8], proof: &MerkleProof) -> bool {
    let leaf_hash: Hash = blake3::hash(leaf).into();
    verify_proof_hash(leaf_hash, proof)
}

/// Verify a proof for a pre-hashed leaf (manifest/ledger digests).
pub fn verify_proof_hash(mut current: Hash, proof: &MerkleProof) -> bool {
    if current != proof.leaf_hash {
        return false;
    }
    for sibling in &proof.proof_path {
        current = hash_pair(current, *sibling);
    }
    current == proof.root_hash
}

fn hash_pair(a: Hash, b: Hash) -> Hash {
    let mut hasher = blake3::Hasher::new();
    if a < b {
        hasher.update(&a);
        hasher.update(&b);
    } else {
        hasher.update(&b);
        hasher.update(&a);
    }
    hasher.finalize().into()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_tree_from_leaves() {
        let leaves: Vec<&[u8]> = vec![b"leaf1", b"leaf2", b"leaf3", b"leaf4"];
        let tree = MerkleTree::from_leaves(&leaves);
        assert_eq!(tree.leaves.len(), 4);
        assert_ne!(tree.root(), [0u8; 32]);
    }

    #[test]
    fn test_try_generate_proof_index_out_of_range() {
        let tree = MerkleTree::from_leaves(&[b"a", b"b"]);
        let err = tree.try_generate_proof(2).unwrap_err().to_string();
        assert!(err.contains("index out of range"));
    }

    #[test]
    fn test_generate_and_verify_proof_various_indices() {
        let data: Vec<&[u8]> = vec![b"a", b"b", b"c", b"d", b"e"];
        let tree = MerkleTree::from_leaves(&data);
        for i in 0..data.len() {
            let proof = tree.try_generate_proof(i).unwrap();
            assert!(verify_proof(data[i], &proof));
            assert_eq!(proof.root_hash, tree.root());
            let expected: Hash = blake3::hash(data[i]).into();
            assert_eq!(proof.leaf_hash, expected);
        }
    }

    #[test]
    fn test_from_hashes_proof_roundtrip() {
        let h0 = [0u8; 32];
        let mut h1 = [0u8; 32];
        h1[31] = 1;
        let tree = MerkleTree::from_hashes(vec![h0, h1]);
        let proof = tree.try_generate_proof(1).unwrap();
        assert!(verify_proof_hash(h1, &proof));
        assert_eq!(proof.root_hash, tree.root());
    }

    #[test]
    fn test_proof_hex_roundtrip() {
        let tree = MerkleTree::from_leaves(&[b"x", b"y", b"z"]);
        let proof = tree.try_generate_proof(2).unwrap();
        let hex = proof_to_hex(&proof);
        let restored = proof_from_hex(&hex).unwrap();
        assert_eq!(proof, restored);
        assert!(verify_proof(b"z", &restored));
    }

    #[test]
    fn test_proof_from_hex_invalid_length() {
        let hex = MerkleProofHex {
            leaf_hash: "abcd".to_string(),
            proof_path: vec![],
            root_hash: "00".repeat(32),
        };
        assert!(proof_from_hex(&hex).is_err());
    }

    #[test]
    fn test_verify_wrong_leaf_fails() {
        let data: Vec<&[u8]> = vec![b"a", b"b", b"c"];
        let tree = MerkleTree::from_leaves(&data);
        let proof = tree.generate_proof(0);
        assert!(!verify_proof(b"wrong_leaf", &proof));
    }

    #[test]
    fn test_verify_manipulated_proof_fails() {
        let data: Vec<&[u8]> = vec![b"a", b"b", b"c", b"d"];
        let tree = MerkleTree::from_leaves(&data);
        let mut proof = tree.generate_proof(1);
        if !proof.proof_path.is_empty() {
            proof.proof_path[0][0] ^= 0xFF;
        }
        assert!(!verify_proof(data[1], &proof));
    }

    #[test]
    fn test_verify_proof_hash_directly() {
        let data: Vec<&[u8]> = vec![b"data1", b"data2"];
        let tree = MerkleTree::from_leaves(&data);
        let proof = tree.generate_proof(0);
        let leaf_hash: Hash = blake3::hash(data[0]).into();
        assert!(verify_proof_hash(leaf_hash, &proof));
    }

    #[test]
    fn test_zero_allocation_verify_design() {
        let data: Vec<&[u8]> = vec![b"zeroalloc"];
        let tree = MerkleTree::from_leaves(&data);
        let proof = tree.generate_proof(0);
        let result = verify_proof(data[0], &proof);
        assert!(result);
    }

    use std::time::Instant;

    fn bench_from_leaves(size: usize) {
        let leaves: Vec<Vec<u8>> = (0..size)
            .map(|i| format!("leaf-{}", i).into_bytes())
            .collect();
        let leaves_ref: Vec<&[u8]> = leaves.iter().map(|v| v.as_slice()).collect();
        let start = Instant::now();
        let _tree = MerkleTree::from_leaves(&leaves_ref);
        let elapsed = start.elapsed();
        println!("bench from_leaves({}): {:?}", size, elapsed);
    }

    fn bench_generate_proof(size: usize) {
        let leaves: Vec<Vec<u8>> = (0..size)
            .map(|i| format!("leaf-{}", i).into_bytes())
            .collect();
        let leaves_ref: Vec<&[u8]> = leaves.iter().map(|v| v.as_slice()).collect();
        let tree = MerkleTree::from_leaves(&leaves_ref);
        let idx = size / 2;
        let start = Instant::now();
        let _proof = tree.try_generate_proof(idx).unwrap();
        let elapsed = start.elapsed();
        println!("bench generate_proof({}): {:?}", size, elapsed);
    }

    fn bench_verify_proof(size: usize) {
        let leaves: Vec<Vec<u8>> = (0..size)
            .map(|i| format!("leaf-{}", i).into_bytes())
            .collect();
        let leaves_ref: Vec<&[u8]> = leaves.iter().map(|v| v.as_slice()).collect();
        let tree = MerkleTree::from_leaves(&leaves_ref);
        let idx = size / 2;
        let proof = tree.generate_proof(idx);
        let leaf = leaves_ref[idx];
        let start = Instant::now();
        let _ok = verify_proof(leaf, &proof);
        let elapsed = start.elapsed();
        println!("bench verify_proof({}): {:?}", size, elapsed);
    }

    #[test]
    fn bench_merkle_various_sizes() {
        println!("\n=== Merkle Benchmarks (feature/merkle-proof worktree) ===");
        for &s in &[8, 64, 1024, 8192] {
            bench_from_leaves(s);
            bench_generate_proof(s);
            bench_verify_proof(s);
        }
        println!("=== End Benchmarks ===\n");
    }
}
