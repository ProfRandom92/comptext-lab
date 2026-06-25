//! Challenge 3 benchmark runner — emits a copy-paste-ready Markdown report on stdout.

use std::process::Command;
use std::time::{Duration, Instant};
use std::{
    env,
    fmt::Write as _,
    path::{Path, PathBuf},
};

const DOCLING_BASELINE_SECS: f64 = 4.230;
const LLM_BASELINE_SECS: f64 = 4.750;

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("workspace root")
}

fn crate_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn runtime_stamp() -> String {
    Command::new("powershell")
        .args([
            "-NoProfile",
            "-Command",
            "Get-Date -Format 'yyyy-MM-dd HH:mm'",
        ])
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "runtime".to_string())
}

fn run_timed(mut cmd: Command) -> (Duration, String, String, bool) {
    let start = Instant::now();
    let output = cmd.output().expect("failed to spawn process");
    let elapsed = start.elapsed();
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    (elapsed, stdout, stderr, output.status.success())
}

fn format_duration(d: Duration) -> String {
    let nanos = d.as_nanos();
    if nanos < 1_000 {
        format!("{nanos} ns")
    } else if nanos < 1_000_000 {
        format!("{:.1} µs", nanos as f64 / 1_000.0)
    } else if nanos < 1_000_000_000 {
        format!("{:.2} ms", nanos as f64 / 1_000_000.0)
    } else {
        format!("{:.3} s", nanos as f64 / 1_000_000_000.0)
    }
}

fn format_secs(secs: f64) -> String {
    if secs < 0.000_001 {
        format!("{:.0} ns", secs * 1_000_000_000.0)
    } else if secs < 0.001 {
        format!("{:.1} µs", secs * 1_000_000.0)
    } else if secs < 1.0 {
        format!("{:.2} ms", secs * 1_000.0)
    } else {
        format!("{:.3} s", secs)
    }
}

fn strip_cargo_noise(text: &str) -> String {
    text.lines()
        .filter(|line| {
            let t = line.trim();
            !t.is_empty()
                && !t.starts_with("Finished `")
                && !t.starts_with("Compiling ")
                && !t.starts_with("Running `")
                && !t.starts_with("Blocking waiting")
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn bar(secs: f64, max_secs: f64, width: usize) -> String {
    if max_secs <= 0.0 {
        return String::new();
    }
    let filled = ((secs / max_secs) * width as f64).round() as usize;
    "■".repeat(filled.min(width))
}

fn parse_bench_value(line: &str) -> Option<String> {
    let (_, rhs) = line.rsplit_once(':')?;
    Some(rhs.trim().to_string())
}

fn parse_merkle_matrix(stdout: &str) -> Vec<(usize, String, String, String)> {
    let mut rows = Vec::new();
    let sizes = [8, 64, 1024, 8192];

    for &size in &sizes {
        let mut build = String::from("n/a");
        let mut generate = String::from("n/a");
        let mut verify = String::from("n/a");

        for line in stdout.lines() {
            if line.contains(&format!("bench from_leaves({size})")) {
                if let Some(v) = parse_bench_value(line) {
                    build = v;
                }
            } else if line.contains(&format!("bench generate_proof({size})")) {
                if let Some(v) = parse_bench_value(line) {
                    generate = v;
                }
            } else if line.contains(&format!("bench verify_proof({size})")) {
                if let Some(v) = parse_bench_value(line) {
                    verify = v;
                }
            }
        }

        rows.push((size, build, generate, verify));
    }

    rows
}

fn benchmark_overhead(root: &Path, stamp: &str) -> String {
    let evidence_out = root.join("artifacts/spark/evidence-envelope.json");
    if let Some(parent) = evidence_out.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    let mut cmd = Command::new("cargo");
    cmd.current_dir(crate_dir()).args([
        "run",
        "--release",
        "--bin",
        "sparkctl",
        "--",
        "spark-evidence-demo",
        "-o",
        "../../artifacts/spark/evidence-envelope.json",
    ]);

    let (elapsed, stdout, _stderr, ok) = run_timed(cmd);
    let evidence_secs = elapsed.as_secs_f64();
    let baseline_total = DOCLING_BASELINE_SECS + LLM_BASELINE_SECS;
    let overhead_pct = (evidence_secs / baseline_total) * 100.0;

    let max_bar = baseline_total.max(evidence_secs);
    let docling_bar = bar(DOCLING_BASELINE_SECS, max_bar, 40);
    let llm_bar = bar(LLM_BASELINE_SECS, max_bar, 40);
    let evidence_bar = bar(evidence_secs, max_bar, 40);

    let status = if ok { "PASS" } else { "FAIL" };

    let mut section = String::new();
    writeln!(section, "## Benchmark 1 — Evidence Overhead (Challenge 3)").unwrap();
    writeln!(section).unwrap();
    writeln!(
        section,
        "**Baseline (fest):** Docling `{DOCLING_BASELINE_SECS:.3}s` · LLM `{LLM_BASELINE_SECS:.3}s` · Summe `{baseline_total:.3}s`"
    )
    .unwrap();
    writeln!(
        section,
        "**Gemessen:** `spark-evidence-demo` → `{}` ({status})",
        format_duration(elapsed)
    )
    .unwrap();
    writeln!(
        section,
        "**Overhead vs. Baseline:** `{overhead_pct:.2}%` der SPARK-Pipeline-Zeit"
    )
    .unwrap();
    writeln!(section).unwrap();
    writeln!(section, "```text").unwrap();
    writeln!(
        section,
        "Docling (baseline)     {docling_bar} {DOCLING_BASELINE_SECS:.3}s"
    )
    .unwrap();
    writeln!(
        section,
        "LLM (baseline)       {llm_bar} {LLM_BASELINE_SECS:.3}s"
    )
    .unwrap();
    writeln!(
        section,
        "CompText Evidence    {evidence_bar} {}",
        format_secs(evidence_secs)
    )
    .unwrap();
    writeln!(section, "```").unwrap();
    writeln!(section).unwrap();
    writeln!(
        section,
        "<details><summary>spark-evidence-demo stdout</summary>"
    )
    .unwrap();
    writeln!(section).unwrap();
    writeln!(section, "```text").unwrap();
    let clean_stdout = strip_cargo_noise(&stdout);
    if clean_stdout.trim().is_empty() {
        writeln!(section, "(empty)").unwrap();
    } else {
        section.push_str(clean_stdout.trim_end());
        section.push('\n');
    }
    writeln!(section, "```").unwrap();
    writeln!(section, "</details>").unwrap();
    writeln!(section).unwrap();
    let _ = stamp;
    section
}

fn benchmark_scaling(root: &Path) -> String {
    let mut cmd = Command::new("cargo");
    cmd.current_dir(root).args([
        "test",
        "-p",
        "comptext_lab",
        "bench_merkle_various_sizes",
        "--release",
        "--",
        "--nocapture",
    ]);

    let (elapsed, stdout, stderr, ok) = run_timed(cmd);
    let rows = parse_merkle_matrix(&stdout);
    let status = if ok { "PASS" } else { "FAIL" };

    let mut section = String::new();
    writeln!(section, "## Benchmark 2 — Merkle Skalierung (Challenge 3)").unwrap();
    writeln!(section).unwrap();
    writeln!(
        section,
        "**Befehl:** `cargo test -p comptext_lab bench_merkle_various_sizes --release -- --nocapture`"
    )
    .unwrap();
    writeln!(
        section,
        "**Laufzeit:** `{}` · Status: **{status}**",
        format_duration(elapsed)
    )
    .unwrap();
    writeln!(section).unwrap();
    writeln!(
        section,
        "| Leaves | Build Tree | Generate Proof | Verify Proof |"
    )
    .unwrap();
    writeln!(
        section,
        "|--------|------------|----------------|--------------|"
    )
    .unwrap();

    for (leaves, build, generate, verify) in &rows {
        writeln!(section, "| {leaves} | {build} | {generate} | {verify} |").unwrap();
    }

    if rows
        .iter()
        .all(|(_, b, g, v)| b == "n/a" && g == "n/a" && v == "n/a")
    {
        writeln!(section).unwrap();
        writeln!(
            section,
            "> Warnung: Keine `bench *_` Zeilen im Test-Output gefunden."
        )
        .unwrap();
    }

    writeln!(section).unwrap();
    writeln!(
        section,
        "**Interpretation:** Proof-Verifikation skaliert für Artifact-Manifeste (typisch ≪ 1024 Leaves)."
    )
    .unwrap();
    writeln!(section).unwrap();

    if !ok {
        let clean_stderr = strip_cargo_noise(&stderr);
        if !clean_stderr.trim().is_empty() {
            writeln!(section, "<details><summary>stderr</summary>").unwrap();
            writeln!(section).unwrap();
            writeln!(section, "```text").unwrap();
            section.push_str(clean_stderr.trim_end());
            section.push('\n');
            writeln!(section, "```").unwrap();
            writeln!(section, "</details>").unwrap();
            writeln!(section).unwrap();
        }
    }

    section
}

fn benchmark_zero_trust(root: &Path) -> String {
    let fixture = "crates/examples/spark/extraction.json";
    let ps_cmd = format!("cargo run --release --bin agy-ct -- package adversarial -i {fixture}");

    let mut cmd = Command::new("cargo");
    cmd.current_dir(root).args([
        "run",
        "--release",
        "--bin",
        "agy-ct",
        "--",
        "package",
        "adversarial",
        "-i",
        fixture,
    ]);

    let (elapsed, stdout, _stderr, ok) = run_timed(cmd);
    let detected = stdout.contains("5/5 detected");
    let status = if ok && detected {
        "PASS — 5/5 detected"
    } else if ok {
        "FAIL — expected 5/5 detected"
    } else {
        "FAIL — command error"
    };

    let mut section = String::new();
    writeln!(
        section,
        "## Benchmark 3 — Zero-Trust / Adversarial (Challenge 3)"
    )
    .unwrap();
    writeln!(section).unwrap();
    writeln!(section, "**Ergebnis:** `{status}`").unwrap();
    writeln!(section, "**Laufzeit:** `{}`", format_duration(elapsed)).unwrap();
    writeln!(section).unwrap();
    writeln!(section, "```powershell").unwrap();
    writeln!(
        section,
        "Set-Location {}",
        root.display().to_string().replace('\\', "/")
    )
    .unwrap();
    writeln!(section, "{ps_cmd}").unwrap();
    writeln!(section, "```").unwrap();
    writeln!(section).unwrap();
    writeln!(section, "```text").unwrap();
    let clean_stdout = strip_cargo_noise(&stdout);
    if clean_stdout.trim().is_empty() {
        writeln!(section, "(empty stdout)").unwrap();
    } else {
        section.push_str(clean_stdout.trim_end());
        section.push('\n');
    }
    writeln!(section, "```").unwrap();
    writeln!(section).unwrap();
    section
}

fn build_report() -> String {
    let root = workspace_root();
    let stamp = runtime_stamp();

    let mut report = String::new();
    writeln!(
        report,
        "# Challenge 3 „Safe and Stable!“ — Automated Benchmark Report"
    )
    .unwrap();
    writeln!(report).unwrap();
    writeln!(report, "**Datum:** {stamp}").unwrap();
    writeln!(
        report,
        "**Worktree:** `{}`",
        root.file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("workspace")
    )
    .unwrap();
    writeln!(
        report,
        "**Runner:** `cargo run --release --bin spark-bench`"
    )
    .unwrap();
    writeln!(report).unwrap();
    writeln!(report, "---").unwrap();
    writeln!(report).unwrap();

    report.push_str(&benchmark_overhead(&root, &stamp));
    report.push_str(&benchmark_scaling(&root));
    report.push_str(&benchmark_zero_trust(&root));

    writeln!(report).unwrap();
    writeln!(report, "---").unwrap();
    writeln!(report).unwrap();
    writeln!(
        report,
        "*Generiert von `spark-bench` — reine stdout-Markdown-Ausgabe für Copy-Paste.*"
    )
    .unwrap();

    report
}

fn main() {
    print!("{}", build_report());
}
