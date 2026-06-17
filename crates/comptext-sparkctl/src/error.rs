use std::fmt;

#[derive(Debug)]
pub enum SparkError {
    ValidationError(String),
    SerializationError(String),
    EvidenceLoss(String),
    ConstraintDrift(String),
}

impl fmt::Display for SparkError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ValidationError(msg) => write!(f, "Validation Error: {}", msg),
            Self::SerializationError(msg) => write!(f, "Serialization Error: {}", msg),
            Self::EvidenceLoss(msg) => write!(f, "EVIDENCE_LOSS: {}", msg),
            Self::ConstraintDrift(msg) => write!(f, "CONSTRAINT_DRIFT: {}", msg),
        }
    }
}

impl std::error::Error for SparkError {}
