use crate::codec::package::{replay_package_value, sort_json_value};
use anyhow::{Context, Result};
use std::fs;

#[derive(Default)]
pub struct ReplayOptions {
    pub quiet: bool,
    pub plain: bool,
    pub no_color: bool,
}

pub fn run(input_path: &str, options: ReplayOptions) -> Result<()> {
    if !options.quiet {
        if !options.plain && !options.no_color {
            eprintln!(
                "\x1b[36mReplaying sidecar trace from {}...\x1b[0m",
                input_path
            );
        } else {
            eprintln!("Replaying sidecar trace from {}...", input_path);
        }
    }

    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read package file: {}", input_path))?;

    let package_val: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse package JSON from: {}", input_path))?;

    match replay_package_value(&package_val) {
        Ok(replay_val) => {
            if !options.quiet {
                if !options.plain && !options.no_color {
                    eprintln!(
                        "\x1b[32mOK: package verified and trace replayed successfully\x1b[0m"
                    );
                } else {
                    eprintln!("OK: package verified and trace replayed successfully");
                }
            }
            let sorted_replay = sort_json_value(&replay_val);
            let pretty_str = serde_json::to_string_pretty(&sorted_replay)?;
            println!("{}", pretty_str);
            Ok(())
        }
        Err(e) => {
            if !options.plain && !options.no_color {
                eprintln!("\x1b[31mreplay failed: {}\x1b[0m", e);
            } else {
                eprintln!("replay failed: {}", e);
            }
            Err(e)
        }
    }
}
