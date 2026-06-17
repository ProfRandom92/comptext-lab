use std::fs;
use std::path::Path;
use std::process::Command;

#[test]
fn test_agy_ct_benchmark_execution() {
    // Get the path to the compiled agy-ct binary directly without cargo run overhead
    let binary_path = env!("CARGO_BIN_EXE_agy-ct");

    // Run agy-ct benchmark subcommand
    let output = Command::new(binary_path)
        .arg("benchmark")
        .output()
        .expect("failed to execute agy-ct benchmark");

    let stdout_str = String::from_utf8_lossy(&output.stdout);
    let stderr_str = String::from_utf8_lossy(&output.stderr);
    println!("stdout: {}", stdout_str);
    println!("stderr: {}", stderr_str);

    assert!(output.status.success(), "agy-ct benchmark command failed");

    // performance_baseline.json should be created/updated at ../reports/performance_baseline.json
    // Relative to the test running directory (which is agy7rust/), it is at ../reports/performance_baseline.json
    let baseline_path = Path::new("../reports/performance_baseline.json");
    assert!(
        baseline_path.exists(),
        "performance_baseline.json does not exist"
    );

    // Read and parse JSON
    let content =
        fs::read_to_string(baseline_path).expect("failed to read performance_baseline.json");
    let json: serde_json::Value =
        serde_json::from_str(&content).expect("failed to parse performance_baseline.json JSON");

    // Assert JSON fields
    assert_eq!(json["phase"], "6J");
    assert_eq!(json["status"], "PASS");

    let run_ms = json["run_ms"]
        .as_u64()
        .expect("run_ms is missing or invalid");
    let context_all_ms = json["context_all_ms"]
        .as_u64()
        .expect("context_all_ms is missing or invalid");
    let context_render_bytes = json["context_render_bytes"]
        .as_u64()
        .expect("context_render_bytes is missing or invalid");

    assert!(run_ms > 0, "run_ms should be positive");
    assert!(context_all_ms > 0, "context_all_ms should be positive");
    assert!(
        context_render_bytes > 0,
        "context_render_bytes should be positive"
    );
}
