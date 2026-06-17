use crate::codec::package::{build_package_from_value, verify_package_value};
use anyhow::{Context, Result};
use std::fs;

pub fn run(input_path: &str) -> Result<()> {
    let content = fs::read_to_string(input_path)
        .with_context(|| format!("Failed to read input file: {}", input_path))?;

    let input_value: serde_json::Value = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse input JSON: {}", input_path))?;

    let package = build_package_from_value(&input_value)?;

    let mut detected_count = 0;

    // --- Case 01: Payload field mutation ---
    {
        let mut tampered = package.clone();
        let parcel_id_val = tampered
            .get_mut("payload")
            .and_then(|p| p.get_mut("extraction"))
            .and_then(|e| e.get_mut("fields"))
            .and_then(|f| f.get_mut("parcel_id"));
        if let Some(val) = parcel_id_val {
            *val = serde_json::Value::String(format!("{}-MUTATED", val.as_str().unwrap_or("")));
        } else {
            return Err(anyhow::anyhow!(
                "Target field parcel_id not found in payload"
            ));
        }
        if verify_package_value(&tampered).is_err() {
            println!("case 01/05 payload field mutation: ok");
            detected_count += 1;
        } else {
            println!("case 01/05 payload field mutation: FAILED (tamper not detected)");
        }
    }

    // --- Case 02: Payload field deletion ---
    {
        let mut tampered = package.clone();
        let fields_map = tampered
            .get_mut("payload")
            .and_then(|p| p.get_mut("extraction"))
            .and_then(|e| e.get_mut("fields"))
            .and_then(|f| f.as_object_mut());
        if let Some(map) = fields_map {
            if map.remove("decision_recommendation").is_none() {
                return Err(anyhow::anyhow!(
                    "Target field decision_recommendation not found in payload"
                ));
            }
        } else {
            return Err(anyhow::anyhow!("Fields object not found in payload"));
        }
        if verify_package_value(&tampered).is_err() {
            println!("case 02/05 payload field deletion: ok");
            detected_count += 1;
        } else {
            println!("case 02/05 payload field deletion: FAILED (tamper not detected)");
        }
    }

    // --- Case 03: payload_sha256 mutation ---
    {
        let mut tampered = package.clone();
        let hash_val = tampered
            .get_mut("sidecar")
            .and_then(|s| s.get_mut("payload_sha256"));
        if let Some(val) = hash_val {
            let s = val.as_str().unwrap_or("");
            *val = serde_json::Value::String(format!("{}0", &s[..s.len().saturating_sub(1)]));
        } else {
            return Err(anyhow::anyhow!("payload_sha256 not found in sidecar"));
        }
        if verify_package_value(&tampered).is_err() {
            println!("case 03/05 payload_sha256 mutation: ok");
            detected_count += 1;
        } else {
            println!("case 03/05 payload_sha256 mutation: FAILED (tamper not detected)");
        }
    }

    // --- Case 04: integrity_hash mutation ---
    {
        let mut tampered = package.clone();
        let hash_val = tampered.get_mut("integrity_hash");
        if let Some(val) = hash_val {
            let s = val.as_str().unwrap_or("");
            *val = serde_json::Value::String(format!("{}0", &s[..s.len().saturating_sub(1)]));
        } else {
            return Err(anyhow::anyhow!("integrity_hash not found in package"));
        }
        if verify_package_value(&tampered).is_err() {
            println!("case 04/05 integrity_hash mutation: ok");
            detected_count += 1;
        } else {
            println!("case 04/05 integrity_hash mutation: FAILED (tamper not detected)");
        }
    }

    // --- Case 05: tool sequence mutation ---
    {
        let mut tampered = package.clone();
        let seq_val = tampered
            .get_mut("sidecar")
            .and_then(|s| s.get_mut("tool_sequence"));
        if let Some(val) = seq_val {
            if let serde_json::Value::Array(ref mut arr) = val {
                arr.push(serde_json::Value::String("malicious.tool".to_string()));
            } else {
                return Err(anyhow::anyhow!("tool_sequence is not an array"));
            }
        } else {
            return Err(anyhow::anyhow!("tool_sequence not found in sidecar"));
        }
        if verify_package_value(&tampered).is_err() {
            println!("case 05/05 tool sequence mutation: ok");
            detected_count += 1;
        } else {
            println!("case 05/05 tool sequence mutation: FAILED (tamper not detected)");
        }
    }

    println!("adversarial: {}/5 detected", detected_count);

    if detected_count == 5 {
        Ok(())
    } else {
        Err(anyhow::anyhow!(
            "Adversarial suite did not detect all tamper cases (detected {}/5)",
            detected_count
        ))
    }
}
