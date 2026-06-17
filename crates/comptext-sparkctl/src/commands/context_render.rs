use crate::context::model::OperationalContext;
use crate::context::render_context;
use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str, output_path: &str) -> Result<()> {
    let run_impl = || -> Result<(String, usize)> {
        let content = fs::read_to_string(input_path)
            .with_context(|| format!("Failed to read context file: {}", input_path))?;

        let context_val: OperationalContext = serde_json::from_str(&content)
            .with_context(|| format!("Failed to parse context JSON: {}", input_path))?;

        let rendered = render_context(&context_val);
        let rendered_bytes = rendered.len();

        fs::write(output_path, &rendered)
            .with_context(|| format!("Failed to write rendered context to: {}", output_path))?;

        Ok((context_val.context_id, rendered_bytes))
    };

    match run_impl() {
        Ok((context_id, rendered_bytes)) => {
            println!("OK: context-render passed");
            println!("context: {}", context_id);
            println!("rendered_bytes: {}", rendered_bytes);
            Ok(())
        }
        Err(e) => {
            eprintln!("ERROR: context-render failed");
            eprintln!("reason: {:#}", e);
            Err(e)
        }
    }
}
