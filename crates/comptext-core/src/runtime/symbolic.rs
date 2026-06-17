use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SymbolicCommand {
    pub command: String,
    pub command_code: String,
    pub language: Option<String>,
    pub language_code: Option<String>,
    pub task: String,
    pub modifiers: Vec<String>,
    pub raw: String,
}
