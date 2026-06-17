use anyhow::Result;
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
                agy7rust::commands::compress::run(input, output)?;
            }
            PackageCommands::Inspect { input } => {
                agy7rust::commands::inspect::run(input)?;
            }
            PackageCommands::Verify { input } => {
                agy7rust::commands::verify_cmd::run(input)?;
            }
            PackageCommands::Replay { input } => {
                let options = agy7rust::commands::replay_cmd::ReplayOptions {
                    quiet: cli.quiet,
                    plain: cli.plain,
                    no_color: cli.no_color,
                };
                agy7rust::commands::replay_cmd::run(input, options)?;
            }
            PackageCommands::Adversarial { input } => {
                agy7rust::commands::adversarial::run(input)?;
            }
        },
        Commands::Context { subcommand } => match subcommand {
            ContextCommands::Build {
                input,
                schema,
                output,
            } => {
                agy7rust::commands::context_build::run(input, schema, output)?;
            }
            ContextCommands::Render { input, output } => {
                agy7rust::commands::context_render::run(input, output)?;
            }
            ContextCommands::Validate { input, schema: _ } => {
                agy7rust::commands::context_validate::run(input)?;
            }
            ContextCommands::All => {
                sparkctl::context_all::run_context_all()?;
            }
        },
        Commands::Schema { subcommand } => match subcommand {
            SchemaCommands::Check { input, schema } => {
                agy7rust::commands::schema_check::run(input, schema)?;
            }
        },
        Commands::Report { subcommand } => match subcommand {
            ReportCommands::Export { input, output } => {
                agy7rust::commands::report_export::run(input, output)?;
            }
        },
        Commands::Notebook { subcommand } => match subcommand {
            NotebookCommands::Bundle {
                input_context,
                input_render,
                output,
            } => {
                agy7rust::commands::notebook_bundle::run(
                    input_context,
                    input_render.as_deref(),
                    output,
                )?;
            }
        },
        Commands::Benchmark => {
            sparkctl::benchmark_action::run_benchmark_action()?;
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

    let path = std::path::Path::new("../reports");
    if path.exists() || std::fs::create_dir_all(path).is_ok() {
        let file_path = path.join("latest.json");
        let serialized = serde_json::to_string_pretty(&report_data)?;
        std::fs::write(file_path, serialized)?;
    } else {
        std::fs::create_dir_all("reports")?;
        let file_path = std::path::Path::new("reports/latest.json");
        let serialized = serde_json::to_string_pretty(&report_data)?;
        std::fs::write(file_path, serialized)?;
    }

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
