use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct ContextDependencyEdge {
    pub source: String,
    pub target: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContextValidation {
    pub valid: bool,
    pub failure_labels: Vec<String>,
    pub issues: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct OperationalContext {
    pub context_id: String,
    pub source_package_hash: String,
    pub schema_name: String,
    pub schema_version: u64,
    pub required_field_paths: Vec<String>,
    pub satisfied_field_paths: Vec<String>,
    pub missing_field_paths: Vec<String>,
    pub constraints: Vec<String>,
    pub required_order: Vec<String>,
    pub dependency_edges: Vec<ContextDependencyEdge>,
    pub blockers: Vec<ContextDependencyEdge>,
    pub recovery_paths: Vec<ContextDependencyEdge>,
    pub validation: ContextValidation,
    pub non_claims: Vec<String>,
}

impl OperationalContext {
    pub fn sort_stable(&mut self) {
        self.required_field_paths.sort();
        self.satisfied_field_paths.sort();
        self.missing_field_paths.sort();
        self.constraints.sort();
        self.required_order.sort();
        self.dependency_edges.sort();
        self.blockers.sort();
        self.recovery_paths.sort();
        self.validation.failure_labels.sort();
        self.validation.issues.sort();
        self.non_claims.sort();
    }

    pub fn validate_model_shape(&self) -> Result<(), String> {
        if self.context_id.is_empty() {
            return Err("missing context_id".to_string());
        }
        if self.source_package_hash.is_empty() {
            return Err("missing source_package_hash".to_string());
        }
        if self.schema_name.is_empty() {
            return Err("missing schema_name".to_string());
        }
        if self.schema_version == 0 {
            return Err("unsupported schema_version".to_string());
        }
        if self.required_field_paths.is_empty() {
            return Err("missing required_field_paths".to_string());
        }
        if self.non_claims.is_empty() {
            return Err("missing non_claims".to_string());
        }
        for path in &self.required_field_paths {
            if path.is_empty() {
                return Err("empty required_field_path".to_string());
            }
        }
        for edge in &self.dependency_edges {
            if edge.source.is_empty() || edge.target.is_empty() {
                return Err("empty dependency edge".to_string());
            }
        }
        for blocker in &self.blockers {
            if blocker.source.is_empty() || blocker.target.is_empty() {
                return Err("empty blocker edge".to_string());
            }
        }
        for path in &self.recovery_paths {
            if path.source.is_empty() || path.target.is_empty() {
                return Err("empty recovery edge".to_string());
            }
        }
        Ok(())
    }
}
