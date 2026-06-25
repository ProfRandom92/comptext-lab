use comptext_lab::dpl_ingest::{build_tree, compute_leaf_hashes, parse_dpl_blocks};
use comptext_lab::evidence::EvidencePackage;
use comptext_lab::{verify_proof_hash, MerkleProof};
use std::path::PathBuf;

fn find_corpus_path() -> PathBuf {
    let paths = [
        "corpus/comptext_kognitive_grenzwiss.dpl",
        "../corpus/comptext_kognitive_grenzwiss.dpl",
        "../../corpus/comptext_kognitive_grenzwiss.dpl",
    ];
    for p in &paths {
        let path = PathBuf::from(p);
        if path.exists() {
            return path;
        }
    }
    panic!("Could not find corpus DPL file in any expected location");
}

#[test]
fn test_real_dpl_ingest_and_proofs() {
    let dpl_path = find_corpus_path();
    let blocks = parse_dpl_blocks(&dpl_path).unwrap();
    assert_eq!(blocks.len(), 10, "Should have exactly 10 blocks");

    let expected_names = vec![
        "INSIGHT_COGNITION",
        "CONSCIOUSNESS_THEORIES",
        "LLM_DEMARKATION",
        "BCI_SYSTEMS",
        "QUANTUM_ML",
        "COSMOLOGY",
        "STORAGE_ARCHIVAL",
        "FREE_WILL",
        "EDGES",
        "SYNTHESIS",
    ];
    for (i, name) in expected_names.iter().enumerate() {
        assert_eq!(blocks[i].0, *name);
    }

    let leaf_hashes = compute_leaf_hashes(&blocks);
    assert_eq!(leaf_hashes.len(), 10);

    let tree = build_tree(leaf_hashes.clone());
    assert_eq!(tree.leaf_count(), 16);

    for i in 0..10 {
        let proof = tree.try_generate_proof(i).unwrap();
        assert_eq!(proof.proof_path.len(), 4);
        assert!(verify_proof_hash(proof.leaf_hash, &proof));
    }
}

#[test]
fn test_evidence_package_generation() {
    let dpl_path = find_corpus_path();
    let pkg = EvidencePackage::from_dpl(&dpl_path).unwrap();

    assert_eq!(pkg.leaf_count, 10);
    assert_eq!(pkg.tree_height, 4);
    assert_eq!(pkg.schema, "ct-lab:evidence:v1");
    assert_eq!(pkg.corpus, "comptext_kognitive_grenzwiss.dpl");

    assert_eq!(pkg.leaves.len(), 10);
    for (i, leaf) in pkg.leaves.iter().enumerate() {
        assert_eq!(leaf.idx, i);
        assert_eq!(leaf.proof_path.len(), 4);

        let leaf_hash_bytes = hex::decode(&leaf.hash).unwrap();
        let mut leaf_arr = [0u8; 32];
        leaf_arr.copy_from_slice(&leaf_hash_bytes);

        let root_bytes = hex::decode(&pkg.merkle_root).unwrap();
        let mut root_arr = [0u8; 32];
        root_arr.copy_from_slice(&root_bytes);

        let mut path_hashes = Vec::new();
        for h_str in &leaf.proof_path {
            let h_bytes = hex::decode(h_str).unwrap();
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&h_bytes);
            path_hashes.push(arr);
        }

        let proof = MerkleProof {
            leaf_hash: leaf_arr,
            proof_path: path_hashes,
            root_hash: root_arr,
        };

        assert!(verify_proof_hash(leaf_arr, &proof));
    }
}
