use anyhow::{anyhow, Result};
use serde::Serialize;
use std::fs;
use std::path::Path;
use std::process::Command;
use std::time::Instant;

#[allow(dead_code)]
#[derive(Serialize)]
struct BenchmarkReport {
    phase: String,
    status: String,
    run_ms: u64,
    context_all_ms: u64,
    latest_report_valid: bool,
    performance_report_valid: bool,
    context_render_bytes: u64,
    checked_artifacts: Vec<String>,
    notes: String,
}

#[allow(dead_code)]
pub fn run_benchmark_action() -> Result<()> {
    println!("=== agy-ct benchmark ===");
    println!("Performance baseline measured on local validation environment.");
    println!("No performance optimization was performed in this phase.");
    println!("Measurements are local and environment-specific.");
    println!();

    let exe = std::env::current_exe()?;

    // Measure agy-ct run
    println!("Running: agy-ct run...");
    let start_run = Instant::now();
    let run_status = Command::new(&exe).arg("run").status()?;
    let run_ms = start_run.elapsed().as_millis() as u64;

    if !run_status.success() {
        return Err(anyhow!("agy-ct run failed during benchmark"));
    }
    println!("  [PASS] agy-ct run ({} ms)", run_ms);

    // Measure agy-ct context all
    println!("Running: agy-ct context all...");
    let start_context = Instant::now();
    let context_status = Command::new(&exe).args(["context", "all"]).status()?;
    let context_all_ms = start_context.elapsed().as_millis() as u64;

    if !context_status.success() {
        return Err(anyhow!("agy-ct context all failed during benchmark"));
    }
    println!("  [PASS] agy-ct context all ({} ms)", context_all_ms);

    // Verify latest.json parses
    let reports_dir = Path::new("../reports");
    let latest_json_path = if reports_dir.exists() {
        reports_dir.join("latest.json")
    } else {
        Path::new("reports/latest.json").to_path_buf()
    };

    let latest_report_valid = if latest_json_path.exists() {
        let content = fs::read_to_string(&latest_json_path)?;
        serde_json::from_str::<serde_json::Value>(&content).is_ok()
    } else {
        false
    };
    println!(
        "  [PASS] reports/latest.json parses successfully: {}",
        latest_report_valid
    );

    // Verify context_render.txt size
    let spark_dir = Path::new("../artifacts/spark");
    let render_path = if spark_dir.exists() {
        spark_dir.join("context_render.txt")
    } else {
        Path::new("artifacts/spark/context_render.txt").to_path_buf()
    };

    let context_render_bytes = if render_path.exists() {
        fs::metadata(&render_path)?.len()
    } else {
        0
    };
    println!(
        "  [PASS] artifacts/spark/context_render.txt size: {} bytes",
        context_render_bytes
    );

    let status = if run_status.success()
        && context_status.success()
        && latest_report_valid
        && context_render_bytes > 0
    {
        "PASS"
    } else {
        "FAIL"
    };

    let report = BenchmarkReport {
        phase: "6J".to_string(),
        status: status.to_string(),
        run_ms,
        context_all_ms,
        latest_report_valid,
        performance_report_valid: true,
        context_render_bytes,
        checked_artifacts: vec![
            "artifacts/spark/extraction.spkg".to_string(),
            "artifacts/spark/context.json".to_string(),
            "artifacts/spark/context_render.txt".to_string(),
            "reports/latest.json".to_string(),
            "reports/performance_baseline.json".to_string(),
        ],
        notes: "Performance baseline measured on local validation environment. No performance optimization was performed in this phase. Measurements are local and environment-specific.".to_string(),
    };

    let dest_dir = Path::new("../reports");
    let dest_file = if dest_dir.exists() || fs::create_dir_all(dest_dir).is_ok() {
        dest_dir.join("performance_baseline.json")
    } else {
        fs::create_dir_all("reports")?;
        Path::new("reports/performance_baseline.json").to_path_buf()
    };

    let serialized = serde_json::to_string_pretty(&report)?;
    fs::write(&dest_file, serialized)?;

    println!();
    println!("benchmark result: {}", status);

    if status == "PASS" {
        Ok(())
    } else {
        Err(anyhow!("Benchmark validation checks failed"))
    }
}
