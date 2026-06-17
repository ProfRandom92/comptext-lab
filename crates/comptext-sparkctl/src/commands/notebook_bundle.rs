use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn run(
    input_context_path: &str,
    input_render_path: Option<&str>,
    output_path: &str,
) -> Result<()> {
    let context_content = fs::read_to_string(input_context_path)
        .with_context(|| format!("Failed to read context file: {}", input_context_path))?;

    let value: serde_json::Value = serde_json::from_str(&context_content)
        .with_context(|| format!("Failed to parse context JSON: {}", input_context_path))?;

    let render_text = if let Some(render_path) = input_render_path {
        let txt = fs::read_to_string(render_path)
            .with_context(|| format!("Failed to read render file: {}", render_path))?;
        Some(txt)
    } else {
        None
    };

    let context_id = value
        .get("context_id")
        .and_then(|v| v.as_str())
        .unwrap_or("n/a");
    let source_hash = value
        .get("source_package_hash")
        .and_then(|v| v.as_str())
        .unwrap_or("n/a");
    let schema_name = value
        .get("schema_name")
        .and_then(|v| v.as_str())
        .unwrap_or("n/a");
    let schema_version = value
        .get("schema_version")
        .and_then(|v| v.as_u64())
        .map(|v| v.to_string())
        .unwrap_or_else(|| "n/a".to_string());

    let (valid_status, failure_labels_str, issues_str) =
        if let Some(validation) = value.get("validation") {
            let valid = validation
                .get("valid")
                .and_then(|v| v.as_bool())
                .unwrap_or(false);
            let valid_str = if valid { "PASS" } else { "FAIL" };

            let labels = validation
                .get("failure_labels")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|x| x.as_str())
                        .collect::<Vec<_>>()
                        .join(", ")
                })
                .unwrap_or_else(|| "none".to_string());

            let issues = validation
                .get("issues")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|x| x.as_str())
                        .collect::<Vec<_>>()
                        .join(", ")
                })
                .unwrap_or_else(|| "none".to_string());

            (valid_str, labels, issues)
        } else {
            ("n/a", "n/a".to_string(), "n/a".to_string())
        };

    let non_claims_str = value
        .get("non_claims")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|x| x.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        })
        .unwrap_or_else(|| "none".to_string());

    let mut metadata_md = String::new();
    metadata_md.push_str("## Context Metadata\n");
    metadata_md.push_str(&format!("- **Context ID**: {}\n", context_id));
    metadata_md.push_str(&format!("- **Source Package Hash**: {}\n", source_hash));
    metadata_md.push_str(&format!(
        "- **Schema**: {} (v{})\n",
        schema_name, schema_version
    ));
    metadata_md.push_str(&format!("- **Validation Status**: {}\n", valid_status));
    metadata_md.push_str(&format!("- **Failure Labels**: {}\n", failure_labels_str));
    metadata_md.push_str(&format!("- **Issues**: {}\n", issues_str));
    metadata_md.push_str(&format!("- **Non-Claims**: {}\n", non_claims_str));

    let mut cells = serde_json::json!([]);

    let cell1 = serde_json::json!({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# CompText-Sparkctl Operational Notebook Bundle\n",
            "\n",
            "This notebook contains the bundled context state and text renderings for review.\n"
        ]
    });
    cells.as_array_mut().unwrap().push(cell1);

    let cell2_source: Vec<String> = metadata_md.lines().map(|l| format!("{}\n", l)).collect();
    let cell2 = serde_json::json!({
        "cell_type": "markdown",
        "metadata": {},
        "source": cell2_source
    });
    cells.as_array_mut().unwrap().push(cell2);

    if let Some(txt) = render_text {
        let cell3_content = format!("## Text Rendering\n\n{}", txt);
        let cell3_source: Vec<String> = cell3_content.lines().map(|l| format!("{}\n", l)).collect();
        let cell3 = serde_json::json!({
            "cell_type": "markdown",
            "metadata": {},
            "source": cell3_source
        });
        cells.as_array_mut().unwrap().push(cell3);
    }

    let code_source = vec![
        "# Raw Context JSON representation\n".to_string(),
        "import json\n".to_string(),
        "raw_context = json.loads(\"\"\"".to_string(),
        serde_json::to_string_pretty(&value)?,
        "\"\"\")\n".to_string(),
        "print(f\"Loaded Context ID: {raw_context.get('context_id', 'n/a')}\")\n".to_string(),
    ];
    let cell4 = serde_json::json!({
        "cell_type": "code",
        "execution_count": null,
        "metadata": {},
        "outputs": [],
        "source": code_source
    });
    cells.as_array_mut().unwrap().push(cell4);

    let ipynb = serde_json::json!({
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    });

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

    let serialized = serde_json::to_string_pretty(&ipynb)?;
    fs::write(&temp_path, &serialized)
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
