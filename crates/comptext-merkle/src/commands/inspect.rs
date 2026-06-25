use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str) -> Result<()> {
    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read package file: {}", input_path))?;

    let package_val: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse package JSON from: {}", input_path))?;

    let pkg = package_val
        .as_object()
        .ok_or_else(|| anyhow::anyhow!("Package is not a JSON object"))?;

    let schema = pkg
        .get("schema")
        .and_then(|v| v.as_str())
        .unwrap_or("<missing>");
    let version = pkg
        .get("version")
        .and_then(|v| v.as_i64())
        .map(|v| v.to_string())
        .unwrap_or_else(|| "<missing>".to_string());

    let sidecar_val = pkg.get("sidecar");
    let sidecar = sidecar_val.and_then(|v| v.as_object());

    let source_type = sidecar
        .and_then(|s| s.get("source_type"))
        .and_then(|v| v.as_str())
        .unwrap_or("<missing>");
    let payload_sha256 = sidecar
        .and_then(|s| s.get("payload_sha256"))
        .and_then(|v| v.as_str())
        .unwrap_or("<missing>");
    let integrity_hash = pkg
        .get("integrity_hash")
        .and_then(|v| v.as_str())
        .unwrap_or("<missing>");

    let field_paths_count = sidecar
        .and_then(|s| s.get("field_paths"))
        .and_then(|v| v.as_array())
        .map(|a| a.len())
        .unwrap_or(0);
    let commitment_tokens_count = sidecar
        .and_then(|s| s.get("commitment_tokens"))
        .and_then(|v| v.as_array())
        .map(|a| a.len())
        .unwrap_or(0);
    let tool_sequence_count = sidecar
        .and_then(|s| s.get("tool_sequence"))
        .and_then(|v| v.as_array())
        .map(|a| a.len())
        .unwrap_or(0);

    println!("schema: {}", schema);
    println!("version: {}", version);
    println!("source_type: {}", source_type);
    println!("payload_sha256: {}", payload_sha256);
    println!("integrity_hash: {}", integrity_hash);
    println!("field_paths count: {}", field_paths_count);
    println!("commitment_tokens count: {}", commitment_tokens_count);
    println!("tool_sequence count: {}", tool_sequence_count);

    Ok(())
}
