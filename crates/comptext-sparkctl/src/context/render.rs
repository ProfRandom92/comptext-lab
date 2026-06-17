use crate::context::model::OperationalContext;

pub fn render_context(context: &OperationalContext) -> String {
    // 1. Create a clone and ensure stable sorted order for lists and edges
    let mut sorted_ctx = context.clone();
    sorted_ctx.sort_stable();

    // 2. Render structured, token-light layout
    let mut out = String::new();
    out.push_str(
        "================================================================================\n",
    );
    out.push_str("SPARK OPERATIONAL CONTEXT\n");
    out.push_str(
        "================================================================================\n",
    );
    out.push_str(&format!("Context ID: {}\n", sorted_ctx.context_id));
    out.push_str(&format!(
        "Source Package Hash: {}\n",
        sorted_ctx.source_package_hash
    ));
    out.push_str(&format!(
        "Schema Name: {} (v{})\n",
        sorted_ctx.schema_name, sorted_ctx.schema_version
    ));
    out.push_str(&format!(
        "Validation Status: {}\n",
        if sorted_ctx.validation.valid {
            "valid"
        } else {
            "invalid"
        }
    ));
    out.push_str(
        "--------------------------------------------------------------------------------\n",
    );

    out.push_str(&format!(
        "Required field paths ({}):\n",
        sorted_ctx.required_field_paths.len()
    ));
    for path in &sorted_ctx.required_field_paths {
        out.push_str(&format!("- {}\n", path));
    }

    out.push_str(&format!(
        "Satisfied field paths ({}):\n",
        sorted_ctx.satisfied_field_paths.len()
    ));
    for path in &sorted_ctx.satisfied_field_paths {
        out.push_str(&format!("- {}\n", path));
    }

    out.push_str(&format!(
        "Missing field paths ({}):\n",
        sorted_ctx.missing_field_paths.len()
    ));
    for path in &sorted_ctx.missing_field_paths {
        out.push_str(&format!("- {}\n", path));
    }

    out.push_str(&format!(
        "Constraints ({}):\n",
        sorted_ctx.constraints.len()
    ));
    for c in &sorted_ctx.constraints {
        out.push_str(&format!("- {}\n", c));
    }

    out.push_str(&format!(
        "Required order ({}):\n",
        sorted_ctx.required_order.len()
    ));
    for o in &sorted_ctx.required_order {
        out.push_str(&format!("- {}\n", o));
    }

    out.push_str(&format!(
        "Dependency graph ({}):\n",
        sorted_ctx.dependency_edges.len()
    ));
    for edge in &sorted_ctx.dependency_edges {
        out.push_str(&format!("- {} -> {}\n", edge.source, edge.target));
    }

    out.push_str(&format!("Blockers ({}):\n", sorted_ctx.blockers.len()));
    for edge in &sorted_ctx.blockers {
        out.push_str(&format!("- {} -> {}\n", edge.source, edge.target));
    }

    out.push_str(&format!(
        "Recovery paths ({}):\n",
        sorted_ctx.recovery_paths.len()
    ));
    for edge in &sorted_ctx.recovery_paths {
        out.push_str(&format!("- {} -> {}\n", edge.source, edge.target));
    }

    out.push_str(&format!(
        "Validation issues ({}):\n",
        sorted_ctx.validation.issues.len()
    ));
    for issue in &sorted_ctx.validation.issues {
        out.push_str(&format!("- {}\n", issue));
    }

    out.push_str(&format!("Non-claims ({}):\n", sorted_ctx.non_claims.len()));
    for nc in &sorted_ctx.non_claims {
        out.push_str(&format!("- {}\n", nc));
    }
    out.push_str(
        "================================================================================\n",
    );

    out
}
