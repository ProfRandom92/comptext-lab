use crate::context::model::OperationalContext;

pub fn validate_context(context: &OperationalContext) -> Result<(), String> {
    // 1. Model Shape Validation
    if let Err(e) = context.validate_model_shape() {
        return Err(format!("validate_model_shape failed: {}", e));
    }

    // 2. Logical Validation
    let missing_empty = context.missing_field_paths.is_empty();
    if context.validation.valid != missing_empty {
        return Err(format!(
            "logical mismatch: validation.valid is {} but missing_field_paths is_empty is {}",
            context.validation.valid, missing_empty
        ));
    }

    if !missing_empty
        && !context
            .validation
            .failure_labels
            .contains(&"MISSING_REQUIRED_FIELD".to_string())
    {
        return Err("context validation invalid: MISSING_REQUIRED_FIELD".to_string());
    }

    // Check that satisfied_field_paths + missing_field_paths matches required_field_paths
    let mut combined = context.satisfied_field_paths.clone();
    combined.extend(context.missing_field_paths.clone());
    combined.sort();
    combined.dedup();

    let mut required_sorted = context.required_field_paths.clone();
    required_sorted.sort();
    required_sorted.dedup();

    if combined != required_sorted {
        return Err(
            "logical mismatch: satisfied + missing field paths do not match required field paths"
                .to_string(),
        );
    }

    // 3. Propagate logical validation failure if validation.valid is false
    if !context.validation.valid {
        return Err("context validation invalid: MISSING_REQUIRED_FIELD".to_string());
    }

    Ok(())
}
