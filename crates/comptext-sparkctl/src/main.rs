use agy7rust::commands::{Cli, Commands};
use clap::Parser;

fn main() -> anyhow::Result<()> {
    let args = Cli::parse();

    match args.command {
        Commands::Compress { input, output } => {
            agy7rust::commands::compress::run(&input, &output)?;
        }
        Commands::Inspect { input } => {
            agy7rust::commands::inspect::run(&input)?;
        }
        Commands::Verify { input } => {
            agy7rust::commands::verify_cmd::run(&input)?;
        }
        Commands::Replay { input } => {
            agy7rust::commands::replay_cmd::run(&input, Default::default())?;
        }
        Commands::Adversarial { input } => {
            agy7rust::commands::adversarial::run(&input)?;
        }
        Commands::SchemaCheck { input, schema } => {
            agy7rust::commands::schema_check::run(&input, &schema)?;
        }
        Commands::ContextBuild {
            input,
            schema,
            output,
        } => {
            agy7rust::commands::context_build::run(&input, &schema, &output)?;
        }
        Commands::ContextRender { input, output } => {
            agy7rust::commands::context_render::run(&input, &output)?;
        }
        Commands::ContextValidate { input, schema } => {
            agy7rust::commands::context_validate::run(&input)?;

            if let Some(schema_path) = schema {
                let context_content = std::fs::read_to_string(&input)?;
                let context_json: serde_json::Value = serde_json::from_str(&context_content)?;

                let schema_content = std::fs::read_to_string(&schema_path)?;
                let schema_json: serde_json::Value = serde_json::from_str(&schema_content)?;

                // Verify schema name
                if let (Some(ctx_name), Some(sch_name)) =
                    (context_json.get("schema_name"), schema_json.get("name"))
                {
                    if ctx_name != sch_name {
                        return Err(anyhow::anyhow!(
                            "Schema name mismatch: context has '{}', schema has '{}'",
                            ctx_name,
                            sch_name
                        ));
                    }
                }

                // Verify required field paths match
                if let (Some(ctx_paths), Some(sch_paths)) = (
                    context_json.get("required_field_paths"),
                    schema_json.get("required_field_paths"),
                ) {
                    let mut ctx_paths_vec: Vec<String> = serde_json::from_value(ctx_paths.clone())?;
                    let mut sch_paths_vec: Vec<String> = serde_json::from_value(sch_paths.clone())?;
                    ctx_paths_vec.sort();
                    sch_paths_vec.sort();
                    if ctx_paths_vec != sch_paths_vec {
                        return Err(anyhow::anyhow!(
                            "Required field paths mismatch between context and schema"
                        ));
                    }
                }
                println!("OK: schema verification passed");
            }
        }
    }

    Ok(())
}
