use crate::codec::package::validate_schema;
use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str, schema_path: &str) -> Result<()> {
    let input_content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read input file: {}", input_path))?;

    let input_val: serde_json::Value = serde_json::from_str(&input_content)
        .with_context(|| format!("Failed to parse input JSON: {}", input_path))?;

    let schema_content = fs::read_to_string(schema_path)
        .with_context(|| format!("Failed to read schema file: {}", schema_path))?;

    let schema_val: serde_json::Value = serde_json::from_str(&schema_content)
        .with_context(|| format!("Failed to parse schema JSON: {}", schema_path))?;

    match validate_schema(&input_val, &schema_val) {
        Ok((name, required, checked)) => {
            println!("OK: schema-check passed");
            println!("schema: {}", name);
            println!("required_fields: {}", required);
            println!("checked_fields: {}", checked);
            Ok(())
        }
        Err(e) => {
            eprintln!("{}", e);
            Err(e)
        }
    }
}
