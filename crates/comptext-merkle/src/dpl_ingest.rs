use crate::codec::merkle::MerkleTree;
use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn parse_dpl_blocks(path: &Path) -> Result<Vec<(String, String)>> {
    let text = fs::read_to_string(path)
        .with_context(|| format!("Failed to read DPL file from {:?}", path))?;

    let mut blocks = Vec::new();
    let mut current_name = String::new();
    let mut current_lines = Vec::new();
    let mut in_block = false;
    let mut depth = 0;

    for line in text.lines() {
        if !in_block {
            let line_trimmed = line.trim_start();
            if line_trimmed.starts_with("§DOM:") && line_trimmed.contains('{') {
                if let Some(rest) = line_trimmed.strip_prefix("§DOM:") {
                    if let Some(brace_idx) = rest.find('{') {
                        let name = rest[..brace_idx].trim().to_string();
                        current_name = name;
                        current_lines.push(line.to_string());
                        in_block = true;
                        depth = 0;
                        for ch in line.chars() {
                            if ch == '{' {
                                depth += 1;
                            }
                            if ch == '}' {
                                depth -= 1;
                            }
                        }
                        if depth == 0 {
                            let content = current_lines.join("\n");
                            blocks.push((current_name.clone(), content));
                            current_lines.clear();
                            in_block = false;
                        }
                    }
                }
            } else if line_trimmed.starts_with("§EDGES") && line_trimmed.contains('{') {
                current_name = "EDGES".to_string();
                current_lines.push(line.to_string());
                in_block = true;
                depth = 0;
                for ch in line.chars() {
                    if ch == '{' {
                        depth += 1;
                    }
                    if ch == '}' {
                        depth -= 1;
                    }
                }
                if depth == 0 {
                    let content = current_lines.join("\n");
                    blocks.push((current_name.clone(), content));
                    current_lines.clear();
                    in_block = false;
                }
            } else if line_trimmed.starts_with("§SYNTHESIS") && line_trimmed.contains('{') {
                current_name = "SYNTHESIS".to_string();
                current_lines.push(line.to_string());
                in_block = true;
                depth = 0;
                for ch in line.chars() {
                    if ch == '{' {
                        depth += 1;
                    }
                    if ch == '}' {
                        depth -= 1;
                    }
                }
                if depth == 0 {
                    let content = current_lines.join("\n");
                    blocks.push((current_name.clone(), content));
                    current_lines.clear();
                    in_block = false;
                }
            }
        } else {
            current_lines.push(line.to_string());
            for ch in line.chars() {
                if ch == '{' {
                    depth += 1;
                }
                if ch == '}' {
                    depth -= 1;
                }
            }
            if depth == 0 {
                let content = current_lines.join("\n");
                blocks.push((current_name.clone(), content));
                current_lines.clear();
                in_block = false;
            }
        }
    }

    Ok(blocks)
}

pub fn leaf_hash(name: &str, content: &str) -> [u8; 32] {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"ct-lab:dpl:leaf:");
    hasher.update(name.as_bytes());
    hasher.update(b":");
    hasher.update(content.trim().as_bytes());
    hasher.finalize().into()
}

pub fn compute_leaf_hashes(blocks: &[(String, String)]) -> Vec<[u8; 32]> {
    blocks
        .iter()
        .map(|(name, content)| leaf_hash(name, content))
        .collect()
}

pub fn build_tree(mut leaf_hashes: Vec<[u8; 32]>) -> MerkleTree {
    while leaf_hashes.len() < 16 {
        leaf_hashes.push([0u8; 32]);
    }
    MerkleTree::from_hashes(leaf_hashes)
}

pub fn generate_inclusion_proof(tree: &MerkleTree, leaf_idx: usize) -> Result<Vec<[u8; 32]>> {
    let proof = tree.try_generate_proof(leaf_idx)?;
    Ok(proof.proof_path)
}
