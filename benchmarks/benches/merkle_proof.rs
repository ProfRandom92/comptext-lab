use comptext_lab::{generate_manifest_merkle_proof, verify_manifest_merkle_proof, MerkleTree};
use divan::black_box;

#[divan::bench]
fn merkle_tree_from_leaves(bencher: divan::Bencher) {
    let data: Vec<Vec<u8>> = (0..64)
        .map(|i| format!("leaf-{}", i).into_bytes())
        .collect();
    let leaves: Vec<&[u8]> = data.iter().map(|v| v.as_slice()).collect();

    bencher.bench(|| {
        let tree = MerkleTree::from_leaves(black_box(&leaves));
        black_box(tree.root());
    });
}

#[divan::bench]
fn merkle_generate_and_verify_proof(bencher: divan::Bencher) {
    let data: Vec<Vec<u8>> = (0..32)
        .map(|i| format!("bench-leaf-{}", i).into_bytes())
        .collect();
    let leaves: Vec<&[u8]> = data.iter().map(|v| v.as_slice()).collect();
    let tree = MerkleTree::from_leaves(&leaves);

    bencher.bench(|| {
        // Use index 0 which is guaranteed valid
        if let Ok(proof) = tree.try_generate_proof(black_box(0)) {
            let _ok = verify_manifest_merkle_proof(
                &hex::encode(black_box(tree.root())),
                &hex::encode(black_box(proof.leaf_hash)),
                &proof,
            );
            black_box(_ok);
        }
    });
}

fn main() {
    divan::main();
}
