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
    #[command(about = "Merkle proof generation and verification (BLAKE3)")]
    Merkle {
        #[command(subcommand)]
        command: MerkleCommands,
    },
}

#[derive(Subcommand)]
enum MerkleCommands {
    #[command(about = "Generate a manifest Merkle proof from a SPARK evidence envelope")]
    ManifestProof {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(long = "index")]
        index: usize,
        #[arg(short = 'o', long = "output")]
        output: Option<String>,
    },
    #[command(about = "Verify a manifest Merkle proof")]
    VerifyManifest {
        #[arg(long = "root")]
        root: String,
        #[arg(long = "leaf")]
        leaf: String,
        #[arg(short = 'i', long = "proof")]
        proof: String,
    },
    #[command(about = "Generate a ledger Merkle proof from a SPARK package JSON")]
    LedgerProof {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(long = "index")]
        index: usize,
        #[arg(short = 'o', long = "output")]
        output: Option<String>,
    },
    #[command(about = "Verify a ledger Merkle proof")]
    VerifyLedger {
        #[arg(long = "root")]
        root: String,
        #[arg(long = "entry")]
        entry: String,
        #[arg(short = 'i', long = "proof")]
        proof: String,
    },
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
        Commands::Merkle { command } => match command {
            MerkleCommands::ManifestProof {
                input,
                index,
                output,
            } => sparkctl::merkle::run_manifest_proof(input, *index, output.as_deref())?,
            MerkleCommands::VerifyManifest { root, leaf, proof } => {
                sparkctl::merkle::run_verify_manifest_proof(root, leaf, proof)?
            }
            MerkleCommands::LedgerProof {
                input,
                index,
                output,
            } => sparkctl::merkle::run_ledger_proof(input, *index, output.as_deref())?,
            MerkleCommands::VerifyLedger { root, entry, proof } => {
                sparkctl::merkle::run_verify_ledger_proof(root, entry, proof)?
            }
        },
    }

    Ok(())
}
