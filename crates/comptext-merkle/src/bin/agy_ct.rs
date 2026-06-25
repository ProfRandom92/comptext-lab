use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::Serialize;

#[path = "../sparkctl/mod.rs"]
mod sparkctl;

#[derive(Parser)]
#[command(name = "agy-ct")]
#[command(about = "Antigravity-CompText SPARK CLI", long_about = None)]
struct Cli {
    #[arg(
        long,
        global = true,
        help = "Plain text output without animations/progress indicators"
    )]
    plain: bool,

    #[arg(long, global = true, help = "Structured JSON output on stdout")]
    json: bool,

    #[arg(long, global = true, help = "Output format (e.g. json)")]
    output: Option<String>,

    #[arg(
        long,
        short,
        global = true,
        help = "Verbose step-by-step diagnostic statements"
    )]
    verbose: bool,

    #[arg(
        long,
        short,
        global = true,
        help = "Quiet mode: suppress non-error output"
    )]
    quiet: bool,

    #[arg(long, global = true, help = "Disable ANSI color escapes")]
    no_color: bool,

    #[arg(
        long,
        global = true,
        help = "Disable interactive prompts and abort immediately if input required"
    )]
    non_interactive: bool,

    #[arg(long, global = true, help = "Explain a specific error code")]
    explain: Option<String>,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    #[command(about = "Automatically coordinate the full local step sequence")]
    Run,
    #[command(about = "Run a predefined end-to-end trace workflow")]
    Demo,
    #[command(about = "Diagnose local project readiness")]
    Doctor,
    #[command(about = "Validate current project formatting, tests, and clippy rules")]
    Validate,
    #[command(about = "Verify local repository handoff readiness")]
    Handoff,
    #[command(about = "Package commands")]
    Package {
        #[command(subcommand)]
        subcommand: PackageCommands,
    },
    #[command(about = "Context commands")]
    Context {
        #[command(subcommand)]
        subcommand: ContextCommands,
    },
    #[command(about = "Schema commands")]
    Schema {
        #[command(subcommand)]
        subcommand: SchemaCommands,
    },
    #[command(about = "Report commands")]
    Report {
        #[command(subcommand)]
        subcommand: ReportCommands,
    },
    #[command(about = "Notebook commands")]
    Notebook {
        #[command(subcommand)]
        subcommand: NotebookCommands,
    },
    #[command(about = "Run local performance benchmark and validation checks")]
    Benchmark,
    #[command(about = "Ingest a DPL corpus file and compute Merkle proofs")]
    Ingest { path: String },
    #[command(about = "Retrieve inclusion proof for a leaf")]
    Proof {
        #[arg(long)]
        leaf: String,
    },
    #[command(about = "Verify leaf hash against Merkle root and proof")]
    Verify {
        #[arg(long)]
        root: String,
        #[arg(long)]
        leaf: String,
        #[arg(long)]
        proof: Option<Vec<String>>,
    },
    #[command(about = "List all DPL leaves")]
    List,
}

#[derive(Subcommand)]
enum PackageCommands {
    #[command(about = "Compress raw extraction files to .spkg")]
    Compress {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        output: String,
    },
    #[command(about = "Read sidecar properties and headers from .spkg")]
    Inspect {
        #[arg(long, short)]
        input: String,
    },
    #[command(about = "Run SHA-256 cryptographic verification of .spkg")]
    Verify {
        #[arg(long, short)]
        input: String,
    },
    #[command(about = "Deterministically reconstruct and replay the sidecar trace")]
    Replay {
        #[arg(long, short)]
        input: String,
    },
    #[command(about = "Verify robustness against tampered payload attributes")]
    Adversarial {
        #[arg(long, short)]
        input: String,
    },
}

#[derive(Subcommand)]
enum ContextCommands {
    #[command(about = "Generate structured operational context from a package")]
    Build {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        schema: String,
        #[arg(long, short)]
        output: String,
    },
    #[command(about = "Render operational context into token-light text")]
    Render {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        output: String,
    },
    #[command(about = "Run structural validation and leak checks on a context")]
    Validate {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        schema: Option<String>,
    },
    #[command(about = "Execute context build, render, and validate tasks in sequence")]
    All,
}

#[derive(Subcommand)]
enum SchemaCommands {
    #[command(about = "Validate raw trace files against target JSON schemas")]
    Check {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        schema: String,
    },
}

#[derive(Subcommand)]
enum ReportCommands {
    #[command(about = "Exporter for generated pipeline JSON reports")]
    Export {
        #[arg(long, short)]
        input: String,
        #[arg(long, short)]
        output: String,
    },
}

#[derive(Subcommand)]
enum NotebookCommands {
    #[command(
        about = "Bundles context state and text renderings into a unified documentation payload"
    )]
    Bundle {
        #[arg(
            short = 'c',
            long = "input-context",
            help = "Path to input context JSON"
        )]
        input_context: String,

        #[arg(
            short = 'r',
            long = "input-render",
            help = "Path to optional input render text"
        )]
        input_render: Option<String>,

        #[arg(short = 'o', long = "output", help = "Path to output bundle .ipynb")]
        output: String,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Run => {
            run_orchestrator()?;
        }
        Commands::Demo => {
            sparkctl::spark_demo::run_spark_demo()?;
        }
        Commands::Doctor => {
            sparkctl::doctor::run_doctor()?;
        }
        Commands::Validate => {
            sparkctl::rust_validate::run_rust_validate()?;
        }
        Commands::Handoff => {
            sparkctl::handoff_check::run_handoff_check()?;
        }
        Commands::Package { subcommand } => match subcommand {
            PackageCommands::Compress { input, output } => {
                comptext_lab::commands::compress::run(input, output)?;
            }
            PackageCommands::Inspect { input } => {
                comptext_lab::commands::inspect::run(input)?;
            }
            PackageCommands::Verify { input } => {
                comptext_lab::commands::verify_cmd::run(input)?;
            }
            PackageCommands::Replay { input } => {
                let options = comptext_lab::commands::replay_cmd::ReplayOptions {
                    quiet: cli.quiet,
                    plain: cli.plain,
                    no_color: cli.no_color,
                };
                comptext_lab::commands::replay_cmd::run(input, options)?;
            }
            PackageCommands::Adversarial { input } => {
                comptext_lab::commands::adversarial::run(input)?;
            }
        },
        Commands::Context { subcommand } => match subcommand {
            ContextCommands::Build {
                input,
                schema,
                output,
            } => {
                comptext_lab::commands::context_build::run(input, schema, output)?;
            }
            ContextCommands::Render { input, output } => {
                comptext_lab::commands::context_render::run(input, output)?;
            }
            ContextCommands::Validate { input, schema: _ } => {
                comptext_lab::commands::context_validate::run(input)?;
            }
            ContextCommands::All => {
                sparkctl::context_all::run_context_all()?;
            }
        },
        Commands::Schema { subcommand } => match subcommand {
            SchemaCommands::Check { input, schema } => {
                comptext_lab::commands::schema_check::run(input, schema)?;
            }
        },
        Commands::Report { subcommand } => match subcommand {
            ReportCommands::Export { input, output } => {
                comptext_lab::commands::report_export::run(input, output)?;
            }
        },
        Commands::Notebook { subcommand } => match subcommand {
            NotebookCommands::Bundle {
                input_context,
                input_render,
                output,
            } => {
                comptext_lab::commands::notebook_bundle::run(
                    input_context,
                    input_render.as_deref(),
                    output,
                )?;
            }
        },
        Commands::Benchmark => {
            sparkctl::benchmark_action::run_benchmark_action()?;
        }
        Commands::Ingest { path } => {
            let path_buf = std::path::Path::new(path);
            let pkg = comptext_lab::evidence::EvidencePackage::from_dpl(path_buf)?;
            let serialized = serde_json::to_string_pretty(&pkg)?;

            let output_dir = std::path::Path::new("evidence");
            std::fs::create_dir_all(output_dir)?;
            let output_file = output_dir.join("comptext_kognitive_grenzwiss_proof.json");
            std::fs::write(&output_file, &serialized)?;

            println!("Ingestion successful.");
            println!("  Leaf count: {}", pkg.leaf_count);
            println!("  Merkle Root: {}", pkg.merkle_root);
            println!("  Overhead: {}", pkg.overhead_pct);
            println!("  Saved proof to {:?}", output_file);

            let dpl_chars = 13977.0;
            let overhead_val = (serialized.len() as f64 / dpl_chars) * 100.0;
            if overhead_val > 8.0 {
                println!(
                    "  [WARNING] Overhead ({:.2}%) exceeds the 8.0% target.",
                    overhead_val
                );
                let log_entry = format!(
                    "[OPTIMIZATION PENDING] {}\nFile: {:?}\nOverhead: {:.2}% (> 8.0% target)\nDescription: Merkle proof JSON payload exceeds the size threshold relative to DPL source.\n\n",
                    chrono_utc_now_iso(),
                    output_file,
                    overhead_val
                );
                use std::fs::OpenOptions;
                use std::io::Write;
                let mut file = OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open("meta_optimizations_pending.log")?;
                file.write_all(log_entry.as_bytes())?;
            } else {
                println!("  Overhead target met: {:.2}% (< 8.0%)", overhead_val);
            }
        }
        Commands::Proof { leaf } => {
            let proof_file =
                std::path::Path::new("evidence/comptext_kognitive_grenzwiss_proof.json");
            if !proof_file.exists() {
                anyhow::bail!("Proof file not found. Please run 'ingest' first.");
            }
            let data = std::fs::read_to_string(proof_file)?;
            let pkg: comptext_lab::evidence::EvidencePackage = serde_json::from_str(&data)?;
            if let Some(l) = pkg.leaves.iter().find(|l| l.name == *leaf) {
                let serialized = serde_json::to_string_pretty(l)?;
                println!("{}", serialized);
            } else {
                anyhow::bail!("Leaf with name '{}' not found in proof package.", leaf);
            }
        }
        Commands::Verify { root, leaf, proof } => {
            let dpl_path = std::path::Path::new("corpus/comptext_kognitive_grenzwiss.dpl");
            if !dpl_path.exists() {
                anyhow::bail!("DPL file not found at {:?}", dpl_path);
            }
            let blocks = comptext_lab::dpl_ingest::parse_dpl_blocks(dpl_path)?;
            let Some((_, content)) = blocks.iter().find(|(name, _)| name == leaf) else {
                anyhow::bail!("Leaf '{}' not found in DPL.", leaf);
            };
            let calculated_leaf_hash = comptext_lab::dpl_ingest::leaf_hash(leaf, content);

            let path_hashes: Vec<[u8; 32]> = if let Some(p_list) = proof {
                if p_list.is_empty() {
                    anyhow::bail!("Proof list is empty.");
                }
                let mut hashes = Vec::new();
                for h_str in p_list {
                    let h_bytes = hex::decode(h_str.trim_start_matches("0x"))?;
                    if h_bytes.len() != 32 {
                        anyhow::bail!("Invalid proof hash length (must be 32 bytes): {}", h_str);
                    }
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(&h_bytes);
                    hashes.push(arr);
                }
                hashes
            } else {
                let proof_file =
                    std::path::Path::new("evidence/comptext_kognitive_grenzwiss_proof.json");
                if !proof_file.exists() {
                    anyhow::bail!(
                        "Proof file not found. Please run 'ingest' first or provide --proof."
                    );
                }
                let data = std::fs::read_to_string(proof_file)?;
                let pkg: comptext_lab::evidence::EvidencePackage = serde_json::from_str(&data)?;
                let Some(l) = pkg.leaves.iter().find(|l| l.name == *leaf) else {
                    anyhow::bail!("Leaf '{}' not found in proof package.", leaf);
                };
                let mut hashes = Vec::new();
                for h_str in &l.proof_path {
                    let h_bytes = hex::decode(h_str)?;
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(&h_bytes);
                    hashes.push(arr);
                }
                hashes
            };

            let parsed_root = hex::decode(root.trim_start_matches("0x"))?;
            if parsed_root.len() != 32 {
                anyhow::bail!("Invalid root length (must be 32 bytes).");
            }
            let mut root_arr = [0u8; 32];
            root_arr.copy_from_slice(&parsed_root);

            let merkle_proof = comptext_lab::MerkleProof {
                leaf_hash: calculated_leaf_hash,
                proof_path: path_hashes,
                root_hash: root_arr,
            };

            let ok = comptext_lab::verify_proof_hash(calculated_leaf_hash, &merkle_proof);
            if ok {
                println!("VERIFY: PASS");
            } else {
                println!("VERIFY: FAIL");
                anyhow::bail!("Merkle proof verification failed.");
            }
        }
        Commands::List => {
            let dpl_path = std::path::Path::new("corpus/comptext_kognitive_grenzwiss.dpl");
            if !dpl_path.exists() {
                anyhow::bail!("DPL file not found at {:?}", dpl_path);
            }
            let blocks = comptext_lab::dpl_ingest::parse_dpl_blocks(dpl_path)?;
            for (idx, (name, _)) in blocks.iter().enumerate() {
                println!("{}: {}", idx, name);
            }
        }
    }

    Ok(())
}

#[derive(Serialize)]
struct Report {
    tool: String,
    project: String,
    phase: String,
    result: String,
    stages: Vec<StageReport>,
    artifacts: Vec<String>,
    report: String,
}

#[derive(Serialize)]
struct StageReport {
    index: usize,
    name: String,
    status: String,
}

fn write_report(stages: Vec<StageReport>, result: &str) -> Result<()> {
    let report_data = Report {
        tool: "agy-ct".to_string(),
        project: "CompText-Sparkctl".to_string(),
        phase: "6E".to_string(),
        result: result.to_string(),
        stages,
        artifacts: vec![
            "artifacts/spark/extraction.spkg".to_string(),
            "artifacts/spark/context.json".to_string(),
            "artifacts/spark/context_render.txt".to_string(),
        ],
        report: "reports/latest.json".to_string(),
    };

    let reports_dir = std::env::current_dir()
        .context("failed to determine current directory")?
        .join("reports");
    std::fs::create_dir_all(&reports_dir)
        .with_context(|| format!("failed to create reports dir {:?}", reports_dir))?;
    let file_path = reports_dir.join("latest.json");
    let serialized = serde_json::to_string_pretty(&report_data)?;
    std::fs::write(file_path, serialized)?;

    Ok(())
}

fn run_orchestrator() -> Result<()> {
    println!("CompText-Sparkctl run");
    println!();
    println!("plan");
    println!("  1 workspace doctor");
    println!("  2 context pipeline");
    println!("  3 spark demo");
    println!("  4 handoff check");
    println!();
    println!("run");

    let mut stages = vec![
        StageReport {
            index: 1,
            name: "workspace doctor".to_string(),
            status: "SKIPPED".to_string(),
        },
        StageReport {
            index: 2,
            name: "context pipeline".to_string(),
            status: "SKIPPED".to_string(),
        },
        StageReport {
            index: 3,
            name: "spark demo".to_string(),
            status: "SKIPPED".to_string(),
        },
        StageReport {
            index: 4,
            name: "handoff check".to_string(),
            status: "SKIPPED".to_string(),
        },
    ];

    // Stage 1: workspace doctor
    stages[0].status = "RUNNING".to_string();
    if let Err(e) = sparkctl::doctor::run_doctor() {
        stages[0].status = "FAIL".to_string();
        println!("  [1/4] workspace doctor   FAIL");
        println!();
        println!("result FAIL");
        let _ = write_report(stages, "FAIL");
        return Err(e);
    }
    stages[0].status = "PASS".to_string();
    println!("  [1/4] workspace doctor   PASS");

    // Stage 2: context pipeline
    stages[1].status = "RUNNING".to_string();
    if let Err(e) = sparkctl::context_all::run_context_all() {
        stages[1].status = "FAIL".to_string();
        println!("  [2/4] context pipeline   FAIL");
        println!();
        println!("result FAIL");
        let _ = write_report(stages, "FAIL");
        return Err(e);
    }
    stages[1].status = "PASS".to_string();
    println!("  [2/4] context pipeline   PASS");

    // Stage 3: spark demo
    stages[2].status = "RUNNING".to_string();
    if let Err(e) = sparkctl::spark_demo::run_spark_demo() {
        stages[2].status = "FAIL".to_string();
        println!("  [3/4] spark demo         FAIL");
        println!();
        println!("result FAIL");
        let _ = write_report(stages, "FAIL");
        return Err(e);
    }
    stages[2].status = "PASS".to_string();
    println!("  [3/4] spark demo         PASS");

    // Stage 4: handoff check
    stages[3].status = "RUNNING".to_string();
    if let Err(e) = sparkctl::handoff_check::run_handoff_check() {
        stages[3].status = "FAIL".to_string();
        println!("  [4/4] handoff check      FAIL");
        println!();
        println!("result FAIL");
        let _ = write_report(stages, "FAIL");
        return Err(e);
    }
    stages[3].status = "PASS".to_string();
    println!("  [4/4] handoff check      PASS");

    println!();
    println!("result PASS");

    write_report(stages, "PASS")?;

    Ok(())
}

fn chrono_utc_now_iso() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now();
    let seconds_since_epoch = now.duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();

    let secs = seconds_since_epoch;
    let sec = secs % 60;
    let mins = secs / 60;
    let min = mins % 60;
    let hours = mins / 60;
    let hour = hours % 24;

    let days = hours / 24;
    let mut y = 1970;
    let mut d = days;
    loop {
        let leap = if (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 {
            366
        } else {
            365
        };
        if d < leap {
            break;
        }
        d -= leap;
        y += 1;
    }

    let is_leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
    let month_days = if is_leap {
        [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    };

    let mut m = 1;
    for &md in month_days.iter() {
        if d < md {
            break;
        }
        d -= md;
        m += 1;
    }

    let day = d + 1;
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        y, m, day, hour, min, sec
    )
}
