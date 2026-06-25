use anyhow::{anyhow, Result};
use std::process::Command;

pub fn run_rust_validate() -> Result<()> {
    let in_test = std::env::var("SPARKCTL_IN_TEST").is_ok();

    let steps = if in_test {
        println!("  (Subcommand cargo test is bypassed to prevent recursive loop during integration test runs)");
        vec![
            ("cargo fmt --all --check", vec!["fmt", "--all", "--check"]),
            (
                "cargo check -p comptext-lab",
                vec!["check", "-p", "comptext-lab"],
            ),
            (
                "cargo clippy -p comptext-lab -- -D warnings",
                vec!["clippy", "-p", "comptext-lab", "--", "-D", "warnings"],
            ),
        ]
    } else {
        vec![
            ("cargo fmt --all --check", vec!["fmt", "--all", "--check"]),
            (
                "cargo check -p comptext-lab",
                vec!["check", "-p", "comptext-lab"],
            ),
            (
                "cargo test -p comptext-lab",
                vec!["test", "-p", "comptext-lab"],
            ),
            (
                "cargo clippy -p comptext-lab -- -D warnings",
                vec!["clippy", "-p", "comptext-lab", "--", "-D", "warnings"],
            ),
        ]
    };

    println!("=== sparkctl rust-validate ===");

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

    println!("rust-validate result: PASS");
    Ok(())
}
