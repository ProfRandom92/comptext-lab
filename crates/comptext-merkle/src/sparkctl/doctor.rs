use anyhow::{anyhow, Result};
use std::path::Path;

pub fn run_doctor() -> Result<()> {
    let checks = [
        ("Cargo.toml", true),
        ("src/lib.rs", true),
        ("src/main.rs", true),
        ("../examples/spark/extraction.json", true),
        ("../schemas/genehmigung_v1.json", true),
        ("../artifacts/spark/extraction.spkg", true),
        ("../artifacts/spark/context.json", true),
        ("../artifacts/spark/context_render.txt", true),
    ];

    println!("=== sparkctl doctor report ===");
    let mut all_passed = true;

    for &(path_str, required) in &checks {
        let path = Path::new(path_str);
        let exists = path.exists();
        let status = if exists { "OK" } else { "MISSING" };
        println!("  - {}: {}", path_str, status);
        if required && !exists {
            all_passed = false;
        }
    }

    if all_passed {
        println!("doctor result: PASS");
        Ok(())
    } else {
        println!("doctor result: FAIL (Required files are missing)");
        Err(anyhow!("Required files are missing"))
    }
}
