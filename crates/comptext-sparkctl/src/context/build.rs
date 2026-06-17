use crate::codec::hash::sha256_hex;
use crate::codec::package::verify_package_value;
use crate::context::model::{ContextDependencyEdge, ContextValidation, OperationalContext};
use serde_json::Value;

pub fn build_context(
    package_val: &Value,
    schema_val: &Value,
) -> Result<OperationalContext, String> {
    // 1. Verify package structure and hashes
    if let Err(e) = verify_package_value(package_val) {
        return Err(format!("package verification failed: {}", e));
    }

    // 2. Extract source_package_hash from integrity_hash of the verified package
    let source_package_hash = package_val
        .get("integrity_hash")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing integrity_hash in package".to_string())?
        .to_string();

    // 3. Verify schema type and version
    let schema_obj = schema_val
        .as_object()
        .ok_or_else(|| "schema is not a JSON object".to_string())?;

    let schema_type = schema_obj
        .get("schema")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing schema type".to_string())?;
    if schema_type != "SPARK-V7-SCHEMA" {
        return Err("schema mismatch".to_string());
    }

    let version = schema_obj
        .get("version")
        .and_then(|v| v.as_i64())
        .ok_or_else(|| "missing schema version".to_string())?;
    if version != 1 {
        return Err("unsupported schema version".to_string());
    }

    let schema_name = schema_obj
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing schema name".to_string())?
        .to_string();

    let schema_version = version as u64;

    // 4. Deterministic context_id from source_package_hash + schema_name + schema_version
    let context_id_preimage = format!("{}{}{}", source_package_hash, schema_name, schema_version);
    let context_id = sha256_hex(context_id_preimage);

    // 5. Ingest required field paths
    let required_paths_val = schema_obj
        .get("required_field_paths")
        .ok_or_else(|| "missing required_field_paths".to_string())?;
    let required_paths_arr = required_paths_val
        .as_array()
        .ok_or_else(|| "required_field_paths is not an array".to_string())?;

    let mut required_field_paths = Vec::new();
    for p in required_paths_arr {
        if let Some(s) = p.as_str() {
            required_field_paths.push(s.to_string());
        } else {
            return Err("required_field_paths contains non-string element".to_string());
        }
    }

    // 6. Ingest satisfied field paths from package sidecar field_paths
    let field_paths_val = package_val
        .get("sidecar")
        .and_then(|s| s.get("field_paths"))
        .ok_or_else(|| "missing sidecar field_paths".to_string())?;
    let field_paths_arr = field_paths_val
        .as_array()
        .ok_or_else(|| "sidecar field_paths is not an array".to_string())?;

    let mut package_field_paths = Vec::new();
    for p in field_paths_arr {
        if let Some(s) = p.as_str() {
            package_field_paths.push(s.to_string());
        }
    }

    let mut satisfied_field_paths = Vec::new();
    let mut missing_field_paths = Vec::new();

    for req_path in &required_field_paths {
        if package_field_paths.contains(req_path) {
            satisfied_field_paths.push(req_path.clone());
        } else {
            missing_field_paths.push(req_path.clone());
        }
    }

    // 7. Non-claims copying and ensuring required defaults exist
    let mut non_claims = Vec::new();
    if let Some(nc_val) = schema_obj.get("non_claims") {
        if let Some(nc_arr) = nc_val.as_array() {
            for nc in nc_arr {
                if let Some(s) = nc.as_str() {
                    non_claims.push(s.to_string());
                }
            }
        }
    }

    let defaults = vec![
        "not_official_spark_schema".to_string(),
        "not_legal_completeness_check".to_string(),
        "not_eu_ai_act_compliance".to_string(),
    ];

    for d in defaults {
        if !non_claims.contains(&d) {
            non_claims.push(d);
        }
    }

    // 8. Constraints, order, dependency edges, blockers, and recovery paths
    let constraints = vec![
        "no_raw_payload_dump".to_string(),
        "schema_required_fields_must_exist".to_string(),
        "deterministic_replay_only".to_string(),
        "synthetic_fixture_only".to_string(),
    ];

    let required_order = vec![
        "package_verified".to_string(),
        "schema_loaded".to_string(),
        "schema_checked".to_string(),
        "context_built".to_string(),
    ];

    let dependency_edges = vec![
        ContextDependencyEdge {
            source: "package_verified".to_string(),
            target: "schema_checked".to_string(),
        },
        ContextDependencyEdge {
            source: "schema_loaded".to_string(),
            target: "schema_checked".to_string(),
        },
        ContextDependencyEdge {
            source: "schema_checked".to_string(),
            target: "context_built".to_string(),
        },
    ];

    let blockers = vec![ContextDependencyEdge {
        source: "missing_required_field".to_string(),
        target: "context_built".to_string(),
    }];

    let recovery_paths = vec![ContextDependencyEdge {
        source: "missing_required_field".to_string(),
        target: "schema_check_failure_reported".to_string(),
    }];

    // 9. Validation
    let valid = missing_field_paths.is_empty();
    let mut failure_labels = Vec::new();
    let mut issues = Vec::new();

    if !valid {
        failure_labels.push("MISSING_REQUIRED_FIELD".to_string());
        for p in &missing_field_paths {
            issues.push(format!("missing required field: {}", p));
        }
    }

    let validation = ContextValidation {
        valid,
        failure_labels,
        issues,
    };

    // 10. Assemble and sort/validate before return
    let mut context = OperationalContext {
        context_id,
        source_package_hash,
        schema_name,
        schema_version,
        required_field_paths,
        satisfied_field_paths,
        missing_field_paths,
        constraints,
        required_order,
        dependency_edges,
        blockers,
        recovery_paths,
        validation,
        non_claims,
    };

    context.sort_stable();

    if let Err(e) = context.validate_model_shape() {
        return Err(format!("validate_model_shape failed: {}", e));
    }

    Ok(context)
}
