use anyhow::{Context, Result};
use comptext_lab::codec::merkle::{proof_from_hex, proof_to_hex};
use comptext_lab::codec::package::{
    generate_ledger_merkle_proof, generate_manifest_merkle_proof, verify_ledger_merkle_proof,
    verify_manifest_merkle_proof, SparkEvidencePacketEnvelope,
};
use std::fs;
use std::path::Path;

#[allow(dead_code)]
pub fn run_manifest_proof(input_path: &str, index: usize, output_path: Option<&str>) -> Result<()> {
    let bytes = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read envelope: {input_path}"))?;
    let envelope: SparkEvidencePacketEnvelope =
        serde_json::from_str(&bytes).context("Failed to parse SPARK evidence envelope JSON")?;

    let proof = generate_manifest_merkle_proof(&envelope.preimage.artifact_manifest, index)?;
    let proof_hex = proof_to_hex(&proof);
    let proof_json = serde_json::to_string_pretty(&proof_hex)?;

    if let Some(path) = output_path {
        if let Some(parent) = Path::new(path).parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create directory: {:?}", parent))?;
        }
        fs::write(path, &proof_json).with_context(|| format!("Failed to write proof: {path}"))?;
        println!("merkle manifest-proof result: PASS");
        println!("  output: {path}");
    } else {
        println!("{proof_json}");
    }

    if let Some(root) = &envelope.manifest_merkle_root {
        let leaf_hex = hex::encode(proof.leaf_hash);
        let ok = verify_manifest_merkle_proof(root, &leaf_hex, &proof);
        println!("  manifest_merkle_root: {root}");
        println!("  verify: {}", if ok { "PASS" } else { "FAIL" });
    }

    Ok(())
}

#[allow(dead_code)]
pub fn run_verify_manifest_proof(root_hex: &str, leaf_hex: &str, proof_path: &str) -> Result<()> {
    let bytes = fs::read_to_string(proof_path)
        .with_context(|| format!("Failed to read proof: {proof_path}"))?;
    let proof_hex: comptext_lab::MerkleProofHex =
        serde_json::from_str(&bytes).context("Failed to parse MerkleProofHex JSON")?;
    let proof = proof_from_hex(&proof_hex)?;
    let ok = verify_manifest_merkle_proof(root_hex, leaf_hex, &proof);

    println!(
        "merkle verify-manifest result: {}",
        if ok { "PASS" } else { "FAIL" }
    );
    if !ok {
        anyhow::bail!("manifest merkle proof verification failed");
    }
    Ok(())
}

#[allow(dead_code)]
pub fn run_ledger_proof(input_path: &str, index: usize, output_path: Option<&str>) -> Result<()> {
    let bytes = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read package: {input_path}"))?;
    let package: serde_json::Value =
        serde_json::from_str(&bytes).context("Failed to parse package JSON")?;
    let ledger = package
        .get("ledger")
        .context("package JSON missing ledger field")?;

    let proof = generate_ledger_merkle_proof(ledger, index)?;
    let proof_hex = proof_to_hex(&proof);
    let proof_json = serde_json::to_string_pretty(&proof_hex)?;

    if let Some(path) = output_path {
        if let Some(parent) = Path::new(path).parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create directory: {:?}", parent))?;
        }
        fs::write(path, &proof_json).with_context(|| format!("Failed to write proof: {path}"))?;
        println!("merkle ledger-proof result: PASS");
        println!("  output: {path}");
    } else {
        println!("{proof_json}");
    }

    if let Some(root) = package.get("ledger_merkle_root").and_then(|v| v.as_str()) {
        let entry_hex = hex::encode(proof.leaf_hash);
        let ok = verify_ledger_merkle_proof(root, &entry_hex, &proof);
        println!("  ledger_merkle_root: {root}");
        println!("  verify: {}", if ok { "PASS" } else { "FAIL" });
    }

    Ok(())
}

#[allow(dead_code)]
pub fn run_verify_ledger_proof(root_hex: &str, entry_hex: &str, proof_path: &str) -> Result<()> {
    let bytes = fs::read_to_string(proof_path)
        .with_context(|| format!("Failed to read proof: {proof_path}"))?;
    let proof_hex: comptext_lab::MerkleProofHex =
        serde_json::from_str(&bytes).context("Failed to parse MerkleProofHex JSON")?;
    let proof = proof_from_hex(&proof_hex)?;
    let ok = verify_ledger_merkle_proof(root_hex, entry_hex, &proof);

    println!(
        "merkle verify-ledger result: {}",
        if ok { "PASS" } else { "FAIL" }
    );
    if !ok {
        anyhow::bail!("ledger merkle proof verification failed");
    }
    Ok(())
}
