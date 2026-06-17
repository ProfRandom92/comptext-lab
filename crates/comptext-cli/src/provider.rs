use crate::cli::ModelRequest;
use serde::{Deserialize, Serialize};
use std::time::Duration;

const HTTP_TIMEOUT_SECS: u64 = 30;

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
pub struct ModelResponse {
    pub provider: String,
    pub model: String,
    pub content: String,
}

pub trait Provider {
    fn name(&self) -> &str;
    fn execute(&self, request: &ModelRequest) -> Result<ModelResponse, String>;
}

pub struct DummyProvider;

impl Provider for DummyProvider {
    fn name(&self) -> &str {
        "dummy"
    }

    fn execute(&self, request: &ModelRequest) -> Result<ModelResponse, String> {
        let file_count = if let Some(sys_msg) = request.messages.iter().find(|m| m.role == "system")
        {
            sys_msg.content.matches("=== FILE: ").count()
        } else {
            0
        };

        let user_prompt = request
            .messages
            .iter()
            .find(|m| m.role == "user")
            .map(|m| m.content.as_str())
            .unwrap_or("");

        let content = format!(
            "Mock LLM response from CompText Dummy Provider.\n\
             Received prompt: \"{user_prompt}\"\n\
             Workspace context analyzed successfully: {file_count} files included.\n\
             Dummy status: offline-test-provider ok."
        );

        Ok(ModelResponse {
            provider: "dummy".to_string(),
            model: "dummy-model".to_string(),
            content,
        })
    }
}

pub struct OllamaProvider {
    pub name: String,
    pub base_url: String,
    pub model_suffix: Option<String>,
    pub auth_env: Option<String>,
}

impl Provider for OllamaProvider {
    fn name(&self) -> &str {
        &self.name
    }

    fn execute(&self, request: &ModelRequest) -> Result<ModelResponse, String> {
        let base_model = if request.model == "dummy-model" {
            "llama3"
        } else {
            &request.model
        };

        let final_model = if let Some(ref suffix) = self.model_suffix {
            format!("{}{}", base_model, suffix)
        } else {
            base_model.to_string()
        };

        let payload = serde_json::json!({
            "model": final_model,
            "messages": request.messages,
            "stream": false
        });

        let endpoint = format!("{}/api/chat", self.base_url.trim_end_matches('/'));
        let agent: ureq::Agent = ureq::Agent::config_builder()
            .timeout_global(Some(Duration::from_secs(HTTP_TIMEOUT_SECS)))
            .build()
            .into();
        let mut req = agent
            .post(&endpoint)
            .header("Content-Type", "application/json");

        if let Some(ref env_var) = self.auth_env {
            match std::env::var(env_var) {
                Ok(val) => {
                    req = req.header("Authorization", format!("Bearer {val}"));
                }
                Err(_) => {
                    return Err(format!(
                        "Authorization environment variable '{}' is not set.",
                        env_var
                    ));
                }
            }
        }

        let mut response = req
            .send_json(&payload)
            .map_err(|e| format!("HTTP request to Ollama failed: {e}"))?;

        let resp_body = response
            .body_mut()
            .read_json::<serde_json::Value>()
            .map_err(|e| format!("failed to read Ollama JSON response: {e}"))?;

        let assistant_content = resp_body
            .get("message")
            .and_then(|m| m.get("content"))
            .and_then(|c| c.as_str())
            .ok_or_else(|| "Ollama response missing assistant message content".to_string())?;

        Ok(ModelResponse {
            provider: self.name.clone(),
            model: final_model,
            content: assistant_content.to_string(),
        })
    }
}

pub struct OpenaiProvider {
    pub name: String,
    pub base_url: String,
    pub model: Option<String>,
    pub auth_env: Option<String>,
    pub allow_network: bool,
}

impl Provider for OpenaiProvider {
    fn name(&self) -> &str {
        &self.name
    }

    fn execute(&self, request: &ModelRequest) -> Result<ModelResponse, String> {
        if !self.allow_network {
            return Err("Network access denied by security policy. Enable allow_provider_network in config to allow live execution.".to_string());
        }

        let model_name = self.model.clone().unwrap_or_else(|| "gpt-4o".to_string());
        let _ = &self.base_url;
        let _ = &self.auth_env;

        let file_count = if let Some(sys_msg) = request.messages.iter().find(|m| m.role == "system")
        {
            sys_msg.content.matches("=== FILE: ").count()
        } else {
            0
        };

        let user_prompt = request
            .messages
            .iter()
            .find(|m| m.role == "user")
            .map(|m| m.content.as_str())
            .unwrap_or("");

        let content = format!(
            "Mock OpenAI response from CompText OpenAI-compatible Provider (Skeleton).\n\
             Model: {model_name}\n\
             Received prompt: \"{user_prompt}\"\n\
             Workspace context analyzed successfully: {file_count} files included.\n\
             OpenAI status: offline-test-provider ok."
        );

        Ok(ModelResponse {
            provider: self.name.clone(),
            model: model_name,
            content,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cli::Message;

    #[test]
    fn test_ollama_missing_auth_env() {
        let provider = OllamaProvider {
            name: "ollama-cloud-direct".to_string(),
            base_url: "https://ollama.com".to_string(),
            model_suffix: None,
            auth_env: Some("NON_EXISTENT_ENV_VAR_TEST".to_string()),
        };
        let request = ModelRequest {
            provider: "ollama-cloud-direct".to_string(),
            model: "llama3".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "hello".to_string(),
            }],
        };
        let res = provider.execute(&request);
        assert!(res.is_err());
        assert!(res
            .unwrap_err()
            .contains("Authorization environment variable 'NON_EXISTENT_ENV_VAR_TEST' is not set"));
    }

    #[test]
    fn test_ollama_local_offline_error() {
        let provider = OllamaProvider {
            name: "ollama-local".to_string(),
            base_url: "http://127.0.0.1:9999".to_string(),
            model_suffix: None,
            auth_env: None,
        };
        let request = ModelRequest {
            provider: "ollama-local".to_string(),
            model: "llama3".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "hello".to_string(),
            }],
        };
        let res = provider.execute(&request);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("HTTP request to Ollama failed"));
    }

    #[test]
    fn test_openai_fails_closed_without_network() {
        let provider = OpenaiProvider {
            name: "openai-compatible".to_string(),
            base_url: "http://localhost:11434/v1".to_string(),
            model: Some("gpt-4o".to_string()),
            auth_env: None,
            allow_network: false,
        };
        let request = ModelRequest {
            provider: "openai-compatible".to_string(),
            model: "dummy-model".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "hello".to_string(),
            }],
        };
        let res = provider.execute(&request);
        assert!(res.is_err());
        assert!(res
            .unwrap_err()
            .contains("Network access denied by security policy"));
    }

    #[test]
    fn test_openai_request_serialization_shape() {
        let model = Some("gpt-4o".to_string());
        let messages = vec![Message {
            role: "user".to_string(),
            content: "hello".to_string(),
        }];
        let model_name = model.clone().unwrap_or_else(|| "gpt-4o".to_string());
        let payload = serde_json::json!({
            "model": model_name,
            "messages": messages
        });

        let payload_str = serde_json::to_string(&payload).unwrap();
        assert!(payload_str.contains("\"model\":\"gpt-4o\""));
        assert!(payload_str.contains("\"content\":\"hello\""));
        assert!(payload_str.contains("\"role\":\"user\""));
    }

    #[test]
    fn test_openai_no_network_call_made() {
        let provider = OpenaiProvider {
            name: "openai-compatible".to_string(),
            base_url: "http://localhost:11434/v1".to_string(),
            model: Some("gpt-4o".to_string()),
            auth_env: None,
            allow_network: true,
        };
        let request = ModelRequest {
            provider: "openai-compatible".to_string(),
            model: "gpt-4o".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "hello".to_string(),
            }],
        };
        let res = provider.execute(&request);
        assert!(res.is_ok());
        let resp = res.unwrap();
        assert_eq!(resp.provider, "openai-compatible");
        assert_eq!(resp.model, "gpt-4o");
        assert!(resp.content.contains("Mock OpenAI response from CompText"));
    }
}
