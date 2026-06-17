use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn run(input_path: &str, output_path: &str) -> Result<()> {
    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read report file: {}", input_path))?;

    let value: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse report JSON: {}", input_path))?;

    let mut md = String::new();
    md.push_str("# CompText-Sparkctl Execution Report\n\n");

    md.push_str("## Metadata\n");
    let tool = value.get("tool").and_then(|v| v.as_str()).unwrap_or("n/a");
    let project = value
        .get("project")
        .and_then(|v| v.as_str())
        .unwrap_or("n/a");
    let phase = value.get("phase").and_then(|v| v.as_str()).unwrap_or("n/a");
    let result = value
        .get("result")
        .and_then(|v| v.as_str())
        .unwrap_or("n/a");

    md.push_str(&format!("- **Tool**: {}\n", tool));
    md.push_str(&format!("- **Project**: {}\n", project));
    md.push_str(&format!("- **Phase**: {}\n", phase));
    md.push_str(&format!("- **Result/Status**: {}\n\n", result));

    if let Some(stages) = value.get("stages").and_then(|v| v.as_array()) {
        md.push_str("## Stages\n");
        for stage in stages {
            let index = stage.get("index").and_then(|v| v.as_u64());
            let name = stage.get("name").and_then(|v| v.as_str()).unwrap_or("n/a");
            let status = stage
                .get("status")
                .and_then(|v| v.as_str())
                .unwrap_or("n/a");

            if let Some(idx) = index {
                md.push_str(&format!("{}. **{}**: {}\n", idx, name, status));
            } else {
                md.push_str(&format!("- **{}**: {}\n", name, status));
            }
        }
        md.push('\n');
    }

    if let Some(artifacts) = value.get("artifacts").and_then(|v| v.as_array()) {
        md.push_str("## Artifacts\n");
        for artifact in artifacts {
            if let Some(art_str) = artifact.as_str() {
                md.push_str(&format!("- {}\n", art_str));
            }
        }
        md.push('\n');
    }

    // Atomic write pattern
    let output_path_buf = Path::new(output_path);
    if let Some(parent) = output_path_buf.parent() {
        if !parent.as_os_str().is_empty() && !parent.exists() {
            fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create directory: {:?}", parent))?;
        }
    }

    let parent_dir = output_path_buf
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let file_name = output_path_buf
        .file_name()
        .ok_or_else(|| anyhow::anyhow!("Invalid output path filename"))?
        .to_str()
        .ok_or_else(|| anyhow::anyhow!("Filename contains invalid Unicode"))?;
    let pid = std::process::id();
    let time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let temp_file_name = format!(".{}_{}_{}.tmp", file_name, pid, time);
    let temp_path = parent_dir.join(temp_file_name);

    fs::write(&temp_path, &md)
        .with_context(|| format!("Failed to write to temp file: {:?}", temp_path))?;

    if let Err(e) = fs::rename(&temp_path, output_path) {
        let _ = fs::remove_file(&temp_path);
        return Err(anyhow::anyhow!(e).context(format!(
            "Failed to rename temp file {:?} to output file {:?}",
            temp_path, output_path_buf
        )));
    }

    Ok(())
}
