use clap::{Parser, Subcommand};

pub mod adversarial;
pub mod compress;
pub mod context_build;
pub mod context_render;
pub mod context_validate;
pub mod inspect;
pub mod notebook_bundle;
pub mod replay_cmd;
pub mod report_export;
pub mod schema_check;
pub mod verify_cmd;

#[derive(Parser)]
#[command(name = "agy7rust")]
#[command(
    about = "Hardened Rust CLI for deterministic SPARK-style package management",
    version
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    Compress {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(short = 'o', long = "output")]
        output: String,
    },
    Inspect {
        #[arg(short = 'i', long = "input")]
        input: String,
    },
    Verify {
        #[arg(short = 'i', long = "input")]
        input: String,
    },
    Replay {
        #[arg(short = 'i', long = "input")]
        input: String,
    },
    Adversarial {
        #[arg(short = 'i', long = "input")]
        input: String,
    },
    SchemaCheck {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(short = 's', long = "schema")]
        schema: String,
    },
    ContextBuild {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(short = 's', long = "schema")]
        schema: String,
        #[arg(short = 'o', long = "output")]
        output: String,
    },
    ContextRender {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(short = 'o', long = "output")]
        output: String,
    },
    ContextValidate {
        #[arg(short = 'i', long = "input")]
        input: String,
        #[arg(short = 's', long = "schema")]
        schema: Option<String>,
    },
}
