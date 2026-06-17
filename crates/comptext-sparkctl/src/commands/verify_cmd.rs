use crate::codec::package::verify_package_value;
use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str) -> Result<()> {
    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read package file: {}", input_path))?;

    let package_val: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse package JSON from: {}", input_path))?;

    match verify_package_value(&package_val) {
        Ok(()) => {
            println!("OK: package verified");
            Ok(())
        }
        Err(e) => {
            eprintln!("verification failed: {}", e);
            Err(e)
        }
    }
}
