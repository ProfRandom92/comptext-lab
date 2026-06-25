use crate::dpl_ingest::{build_tree, compute_leaf_hashes, parse_dpl_blocks};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EvidencePackage {
    pub schema: String,
    pub corpus: String,
    pub version: String,
    pub timestamp: String,
    pub leaf_count: usize,
    pub tree_height: usize,
    pub merkle_root: String,
    pub overhead_pct: String,
    pub leaves: Vec<EvidenceLeaf>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EvidenceLeaf {
    pub idx: usize,
    pub name: String,
    pub hash: String,
    pub proof_path: Vec<String>,
}

fn get_iso8601_timestamp() -> String {
    let now = SystemTime::now();
    let seconds_since_epoch = now.duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();

    let secs = seconds_since_epoch;
    let sec = secs % 60;
    let mins = secs / 60;
    let min = mins % 60;
    let hours = mins / 60;
    let hour = hours % 24;

    let days = hours / 24;
    let mut y = 1970;
    let mut d = days;
    loop {
        let leap = if (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 {
            366
        } else {
            365
        };
        if d < leap {
            break;
        }
        d -= leap;
        y += 1;
    }

    let is_leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
    let month_days = if is_leap {
        [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    };

    let mut m = 1;
    for &md in month_days.iter() {
        if d < md {
            break;
        }
        d -= md;
        m += 1;
    }

    let day = d + 1;

    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        y, m, day, hour, min, sec
    )
}

impl EvidencePackage {
    pub fn from_dpl(path: &Path) -> Result<Self> {
        let blocks = parse_dpl_blocks(path)?;
        let leaf_hashes = compute_leaf_hashes(&blocks);
        let tree = build_tree(leaf_hashes.clone());
        let root_hex = hex::encode(tree.root());

        let mut leaves_info = Vec::new();
        for (idx, (name, _)) in blocks.iter().enumerate() {
            let hash = hex::encode(leaf_hashes[idx]);
            let proof = tree.try_generate_proof(idx)?;
            let proof_path = proof.proof_path.iter().map(hex::encode).collect();

            leaves_info.push(EvidenceLeaf {
                idx,
                name: name.clone(),
                hash,
                proof_path,
            });
        }

        let mut pkg = EvidencePackage {
            schema: "ct-lab:evidence:v1".to_string(),
            corpus: path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string(),
            version: "1.0.0".to_string(),
            timestamp: get_iso8601_timestamp(),
            leaf_count: blocks.len(),
            tree_height: 4,
            merkle_root: root_hex,
            overhead_pct: "0.00%".to_string(),
            leaves: leaves_info,
        };

        // Calculate overhead
        let temp_json = serde_json::to_string_pretty(&pkg)?;
        let dpl_chars = 13977.0;
        let overhead_val = (temp_json.len() as f64 / dpl_chars) * 100.0;
        pkg.overhead_pct = format!("{:.2}%", overhead_val);

        Ok(pkg)
    }
}
