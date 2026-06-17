use anyhow::Result;
use clap::{Parser, Subcommand};

#[path = "../sparkctl/mod.rs"]
mod sparkctl;

#[derive(Parser)]
#[command(name = "sparkctl")]
#[command(about = "SPARK Operational Context Layer CLI", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    #[command(about = "Diagnose local project readiness")]
    Doctor,
    #[command(about = "Run local Rust quality checks (fmt, check, test, clippy)")]
    RustValidate,
    #[command(about = "Run complete context lifecycle (build, render, validate)")]
    ContextAll,
    #[command(about = "Run complete end-to-end demo pipeline (compress, build, render, validate)")]
    SparkDemo,
    #[command(about = "Write a deterministic SPARK Evidence Packet v1 demo envelope")]
    SparkEvidenceDemo {
        #[arg(short = 'o', long = "output")]
        output: String,
    },
    #[command(about = "Validate a SPARK Evidence Packet v1 envelope")]
    SparkEvidenceValidate {
        #[arg(short = 'i', long = "input")]
        input: String,
    },
    #[command(about = "Verify local repository handoff readiness")]
    HandoffCheck,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Doctor => {
            sparkctl::doctor::run_doctor()?;
        }
        Commands::RustValidate => {
            sparkctl::rust_validate::run_rust_validate()?;
        }
        Commands::ContextAll => {
            sparkctl::context_all::run_context_all()?;
        }
        Commands::SparkDemo => {
            sparkctl::spark_demo::run_spark_demo()?;
        }
        Commands::SparkEvidenceDemo { output } => {
            sparkctl::spark_evidence::run_spark_evidence_demo(output)?;
        }
        Commands::SparkEvidenceValidate { input } => {
            sparkctl::spark_evidence::run_spark_evidence_validate(input)?;
        }
        Commands::HandoffCheck => {
            sparkctl::handoff_check::run_handoff_check()?;
        }
    }

    Ok(())
}
