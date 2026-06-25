use crate::context::model::OperationalContext;
use crate::context::validate_context;
use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str) -> Result<()> {
    let run_impl = || -> Result<String> {
        let content = fs::read_to_string(input_path)
            .with_context(|| format!("Failed to read context file: {}", input_path))?;

        let context_val: OperationalContext = serde_json::from_str(&content)
            .with_context(|| format!("Failed to parse context JSON: {}", input_path))?;

        validate_context(&context_val).map_err(|e| anyhow::anyhow!(e))?;

        Ok(context_val.context_id)
    };

    match run_impl() {
        Ok(context_id) => {
            println!("OK: context-validate passed");
            println!("context: {}", context_id);
            println!("valid: true");
            Ok(())
        }
        Err(e) => {
            eprintln!("ERROR: context-validate failed");
            eprintln!("reason: {:#}", e);
            Err(e)
        }
    }
}
