use anyhow::{anyhow, Result};
use std::process::Command;

pub fn run_spark_demo() -> Result<()> {
    let steps = vec![
        (
            "cargo run -- compress -i ../examples/spark/extraction.json -o ../artifacts/spark/extraction.spkg",
            vec![
                "run",
                "--bin",
                "agy7rust",
                "--",
                "compress",
                "-i",
                "../examples/spark/extraction.json",
                "-o",
                "../artifacts/spark/extraction.spkg",
            ],
        ),
        (
            "cargo run -- context-build -i ../artifacts/spark/extraction.spkg -s ../schemas/genehmigung_v1.json -o ../artifacts/spark/context.json",
            vec![
                "run",
                "--bin",
                "agy7rust",
                "--",
                "context-build",
                "-i",
                "../artifacts/spark/extraction.spkg",
                "-s",
                "../schemas/genehmigung_v1.json",
                "-o",
                "../artifacts/spark/context.json",
            ],
        ),
        (
            "cargo run -- context-render -i ../artifacts/spark/context.json -o ../artifacts/spark/context_render.txt",
            vec![
                "run",
                "--bin",
                "agy7rust",
                "--",
                "context-render",
                "-i",
                "../artifacts/spark/context.json",
                "-o",
                "../artifacts/spark/context_render.txt",
            ],
        ),
        (
            "cargo run -- context-validate -i ../artifacts/spark/context.json -s ../schemas/genehmigung_v1.json",
            vec![
                "run",
                "--bin",
                "agy7rust",
                "--",
                "context-validate",
                "-i",
                "../artifacts/spark/context.json",
                "-s",
                "../schemas/genehmigung_v1.json",
            ],
        ),
    ];

    println!("=== sparkctl spark-demo ===");

    for &(display_name, ref args) in &steps {
        println!("  - running: {}...", display_name);

        let status = Command::new("cargo")
            .args(args)
            .status()
            .map_err(|e| anyhow!("Failed to execute '{}': {}", display_name, e))?;

        if !status.success() {
            println!(
                "  [FAIL] {} failed with exit status: {}",
                display_name, status
            );
            return Err(anyhow!("Check '{}' failed", display_name));
        } else {
            println!("  [PASS] {}", display_name);
        }
    }

    println!("spark-demo result: PASS");
    Ok(())
}
