use crate::context::build_context;
use anyhow::{Context, Result};
use std::fs;

pub fn run(package_path: &str, schema_path: &str, output_path: &str) -> Result<()> {
    let run_impl = || -> Result<(String, String, usize)> {
        let package_content = fs::read_to_string(package_path)
            .with_context(|| format!("Failed to read package file: {}", package_path))?;
        let package_val: serde_json::Value = serde_json::from_str(&package_content)
            .with_context(|| format!("Failed to parse package JSON: {}", package_path))?;

        let schema_content = fs::read_to_string(schema_path)
            .with_context(|| format!("Failed to read schema file: {}", schema_path))?;
        let schema_val: serde_json::Value = serde_json::from_str(&schema_content)
            .with_context(|| format!("Failed to parse schema JSON: {}", schema_path))?;

        let context = build_context(&package_val, &schema_val).map_err(|e| anyhow::anyhow!(e))?;

        let context_id = context.context_id.clone();
        let schema_name = context.schema_name.clone();
        let missing_fields = context.missing_field_paths.len();

        let mut context_json =
            serde_json::to_string_pretty(&context).context("Failed to serialize context JSON")?;
        context_json.push('\n');

        fs::write(output_path, context_json)
            .with_context(|| format!("Failed to write context output file: {}", output_path))?;

        Ok((context_id, schema_name, missing_fields))
    };

    match run_impl() {
        Ok((context_id, schema_name, missing_fields)) => {
            println!("OK: context-build passed");
            println!("context: {}", context_id);
            println!("schema: {}", schema_name);
            println!("missing_fields: {}", missing_fields);
            Ok(())
        }
        Err(e) => {
            eprintln!("ERROR: context-build failed");
            eprintln!("reason: {:#}", e);
            Err(e)
        }
    }
}
