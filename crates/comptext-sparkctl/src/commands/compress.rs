use crate::codec::package::{build_package_from_value, canonical_json};
use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn run(input_path: &str, output_path: &str) -> Result<()> {
    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read input file: {}", input_path))?;

    let input_value: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse input JSON: {}", input_path))?;

    let package_value = build_package_from_value(&input_value)?;

    let output_path_buf = Path::new(output_path);
    if let Some(parent) = output_path_buf.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create directory: {:?}", parent))?;
        }
    }

    let package_json = canonical_json(&package_value);

    let parent_dir = output_path_buf.parent().unwrap_or_else(|| Path::new("."));
    let file_name = output_path_buf
        .file_name()
        .ok_or_else(|| anyhow::anyhow!("Invalid output path filename"))?
        .to_str()
        .ok_or_else(|| anyhow::anyhow!("Filename contains invalid Unicode"))?;
    let temp_file_name = format!(".{}.tmp", file_name);
    let temp_path = parent_dir.join(temp_file_name);

    fs::write(&temp_path, &package_json)
        .with_context(|| format!("Failed to write to temp file: {:?}", temp_path))?;

    fs::rename(&temp_path, output_path).with_context(|| {
        format!(
            "Failed to rename temp file {:?} to output file {:?}",
            temp_path, output_path_buf
        )
    })?;

    Ok(())
}
