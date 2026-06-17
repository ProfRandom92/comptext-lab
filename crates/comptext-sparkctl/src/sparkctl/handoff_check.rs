use anyhow::{anyhow, Result};
use std::path::Path;
use std::process::Command;

pub fn run_handoff_check() -> Result<()> {
    let file_checks = vec![
        ("../AGENTS.md", "AGENTS.md"),
        (
            "../.agent/skills/00_project_system.md",
            ".agent/skills/00_project_system.md",
        ),
        (
            "../.agent/skills/01_phase_gate.md",
            ".agent/skills/01_phase_gate.md",
        ),
        (
            "../.agent/skills/02_rust_validation.md",
            ".agent/skills/02_rust_validation.md",
        ),
        (
            "../.agent/skills/03_artifact_validation.md",
            ".agent/skills/03_artifact_validation.md",
        ),
        (
            "../.agent/skills/04_spark_context_layer.md",
            ".agent/skills/04_spark_context_layer.md",
        ),
        (
            "../.agent/skills/05_claim_hygiene.md",
            ".agent/skills/05_claim_hygiene.md",
        ),
        (
            "../.agent/skills/06_git_handoff.md",
            ".agent/skills/06_git_handoff.md",
        ),
        (
            "../PHASE3_CONTEXT_LAYER_FINAL_SNAPSHOT.md",
            "PHASE3_CONTEXT_LAYER_FINAL_SNAPSHOT.md",
        ),
        (
            "../PHASE4A_SPARKCTL_PLANNING_HANDBOOK.md",
            "PHASE4A_SPARKCTL_PLANNING_HANDBOOK.md",
        ),
        (
            "../PHASE4B_SPARKCTL_DOCTOR_SNAPSHOT.md",
            "PHASE4B_SPARKCTL_DOCTOR_SNAPSHOT.md",
        ),
        (
            "../PHASE4C_SPARKCTL_RUST_VALIDATE_SNAPSHOT.md",
            "PHASE4C_SPARKCTL_RUST_VALIDATE_SNAPSHOT.md",
        ),
        (
            "../PHASE4D_SPARKCTL_CONTEXT_ALL_SNAPSHOT.md",
            "PHASE4D_SPARKCTL_CONTEXT_ALL_SNAPSHOT.md",
        ),
        (
            "../PHASE4E_SPARKCTL_SPARK_DEMO_SNAPSHOT.md",
            "PHASE4E_SPARKCTL_SPARK_DEMO_SNAPSHOT.md",
        ),
        (
            "../PHASE4F_SPARKCTL_HANDOFF_CHECK_HANDBOOK.md",
            "PHASE4F_SPARKCTL_HANDOFF_CHECK_HANDBOOK.md",
        ),
        ("PHASE4D_STATUS.md", "agy7rust/PHASE4D_STATUS.md"),
        ("PHASE4E_STATUS.md", "agy7rust/PHASE4E_STATUS.md"),
        (
            "../artifacts/spark/extraction.spkg",
            "artifacts/spark/extraction.spkg",
        ),
        (
            "../artifacts/spark/context.json",
            "artifacts/spark/context.json",
        ),
        (
            "../artifacts/spark/context_render.txt",
            "artifacts/spark/context_render.txt",
        ),
        (
            "../examples/spark/extraction.json",
            "examples/spark/extraction.json",
        ),
        (
            "../schemas/genehmigung_v1.json",
            "schemas/genehmigung_v1.json",
        ),
    ];

    println!("=== sparkctl handoff-check ===");
    println!("--- File Presence Checks ---");

    for &(path_str, display_name) in &file_checks {
        let path = Path::new(path_str);
        if path.exists() {
            println!("  [OK] {} exists", display_name);
        } else {
            println!("  [FAIL] {} does not exist", display_name);
            return Err(anyhow!("Handoff check failed: {} is missing", display_name));
        }
    }

    println!("--- Command Surface Checks ---");

    let commands = vec![
        (
            "cargo run --bin sparkctl -- doctor",
            vec!["run", "--bin", "sparkctl", "--", "doctor"],
        ),
        (
            "cargo run --bin sparkctl -- context-all",
            vec!["run", "--bin", "sparkctl", "--", "context-all"],
        ),
        (
            "cargo run --bin sparkctl -- spark-demo",
            vec!["run", "--bin", "sparkctl", "--", "spark-demo"],
        ),
    ];

    for &(display_name, ref args) in &commands {
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
            return Err(anyhow!("Command check '{}' failed", display_name));
        } else {
            println!("  [PASS] {}", display_name);
        }
    }

    println!("handoff-check result: PASS");
    Ok(())
}
