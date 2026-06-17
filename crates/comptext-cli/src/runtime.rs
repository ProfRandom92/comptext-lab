use serde::{Deserialize, Serialize};
use serde_json::json;
use std::io::{self, BufRead, Read, Write};
use std::path::{Component, Path};

const DEFAULT_MAX_FILE_BYTES: u64 = 64 * 1024;

#[derive(Debug, Clone)]
struct McpError {
    code: i64,
    message: &'static str,
    kind: &'static str,
    detail: String,
}

impl McpError {
    fn new(code: i64, message: &'static str, kind: &'static str, detail: &str) -> Self {
        Self {
            code,
            message,
            kind,
            detail: bounded_mcp_detail(detail),
        }
    }

    fn parse_error(detail: &str) -> Self {
        Self::new(-32700, "parse error", "parse_error", detail)
    }

    fn method_not_found(detail: &str) -> Self {
        Self::new(-32601, "method not found", "method_not_found", detail)
    }

    fn invalid_request(detail: &str) -> Self {
        Self::new(-32600, "invalid request", "invalid_request", detail)
    }

    fn invalid_params(detail: &str) -> Self {
        Self::new(-32602, "invalid params", "invalid_params", detail)
    }

    fn access_denied(detail: &str) -> Self {
        Self::new(-32000, "access denied", "access_denied", detail)
    }

    fn denied_sensitive_path(detail: &str) -> Self {
        Self::new(
            -32000,
            "denied sensitive path",
            "denied_sensitive_path",
            detail,
        )
    }

    fn outside_allowed_root(detail: &str) -> Self {
        Self::new(
            -32000,
            "outside allowed root",
            "outside_allowed_root",
            detail,
        )
    }

    fn file_too_large(detail: &str) -> Self {
        Self::new(-32000, "file too large", "file_too_large", detail)
    }
}

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

pub fn try_run(argv: &[String], json_output: bool) -> Option<i32> {
    let first = argv.first()?;
    let result = match first.as_str() {
        "parse" => run_parse(&argv[1..], json_output),
        "encode" => run_encode(&argv[1..], json_output),
        "batch" => run_batch(&argv[1..], json_output),
        "dsl" => run_dsl(&argv[1..], json_output),
        "evidence" => run_evidence(&argv[1..], json_output),
        "mcp" => run_mcp(&argv[1..], json_output),
        "detect-illegible-cot" => run_detect(&argv[1..], json_output),
        _ => return None,
    };

    Some(match result {
        Ok(()) => 0,
        Err(message) => {
            emit_error(json_output, &message);
            1
        }
    })
}

fn run_parse(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 1 {
        return Err("usage: ctxt parse <symbolic-command> [--json]".to_string());
    }
    let command = parse_symbolic(&argv[0])?;
    if json_output {
        println!("{}", serde_json::to_string_pretty(&command).unwrap());
    } else {
        println!(
            "command={} language={} task={}",
            command.command,
            command.language.as_deref().unwrap_or("none"),
            command.task
        );
    }
    Ok(())
}

fn run_encode(argv: &[String], json_output: bool) -> Result<(), String> {
    let mut command = None;
    let mut language = None;
    let mut task = None;
    let mut modifiers = Vec::new();
    let mut i = 0;
    while i < argv.len() {
        match argv[i].as_str() {
            "--command" => {
                command = Some(required_value(argv, i, "--command")?);
                i += 2;
            }
            "--language" => {
                language = Some(required_value(argv, i, "--language")?);
                i += 2;
            }
            "--task" => {
                task = Some(required_value(argv, i, "--task")?);
                i += 2;
            }
            "--modifier" => {
                modifiers.push(required_value(argv, i, "--modifier")?);
                i += 2;
            }
            other => return Err(format!("unexpected argument '{other}' for 'encode'")),
        }
    }

    let command = command.ok_or_else(|| "encode requires --command <name>".to_string())?;
    let task = task.ok_or_else(|| "encode requires --task <task>".to_string())?;
    let encoded = encode_symbolic(&command, language.as_deref(), &task, &modifiers)?;
    if json_output {
        let parsed = parse_symbolic(&encoded)?;
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "ok": true,
                "encoded": encoded,
                "parsed": parsed
            }))
            .unwrap()
        );
    } else {
        println!("{encoded}");
    }
    Ok(())
}

fn run_batch(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 1 {
        return Err("usage: ctxt batch <batch-expression> [--json]".to_string());
    }
    let batch = parse_batch(&argv[0])?;
    if json_output {
        println!("{}", serde_json::to_string_pretty(&batch).unwrap());
    } else {
        println!(
            "batch mode={} items={}",
            batch["mode"],
            batch["items"].as_array().unwrap().len()
        );
    }
    Ok(())
}

fn run_dsl(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 2 || argv[0] != "validate" {
        return Err("usage: ctxt dsl validate <path> [--json]".to_string());
    }
    let text = read_runtime_text(&argv[1], "DSL file")?;
    let report = validate_dsl(&text);
    if json_output {
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
    } else if report["valid"] == true {
        println!("DSL valid: {}", argv[1]);
    } else {
        println!("DSL invalid: {}", report["errors"]);
    }
    if report["valid"] == true {
        Ok(())
    } else {
        Err("DSL validation failed".to_string())
    }
}

fn run_evidence(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 2 || argv[0] != "hash" {
        return Err("usage: ctxt evidence hash <path> [--json]".to_string());
    }
    let bytes = read_runtime_bytes(&argv[1], "evidence file")?;
    let digest = sha256_hex(&bytes);
    let normalized_path = argv[1].replace('\\', "/");
    if json_output {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "ok": true,
                "algorithm": "sha256",
                "path": normalized_path,
                "bytes": bytes.len(),
                "sha256": digest
            }))
            .unwrap()
        );
    } else {
        println!("{digest}  {normalized_path}");
    }
    Ok(())
}

fn run_mcp(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 3 || argv[0] != "serve" || argv[1] != "--allowed-root" {
        return Err("usage: ctxt mcp serve --allowed-root <path>".to_string());
    }
    let allowed_root = std::fs::canonicalize(&argv[2])
        .map_err(|e| format!("failed to canonicalize allowed root '{}': {e}", argv[2]))?;
    serve_mcp(&allowed_root).map_err(|e| {
        if json_output {
            e
        } else {
            format!("mcp serve failed: {e}")
        }
    })
}

fn run_detect(argv: &[String], json_output: bool) -> Result<(), String> {
    if argv.len() != 1 {
        return Err("usage: ctxt detect-illegible-cot <path> [--json]".to_string());
    }
    let text = read_runtime_text(&argv[0], "trace file")?;
    let report = detect_illegible_cot(&text);
    if json_output {
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
    } else {
        println!(
            "illegible_cot_detected={} findings={}",
            report["detected"],
            report["findings"].as_array().unwrap().len()
        );
    }
    Ok(())
}

fn required_value(argv: &[String], i: usize, flag: &str) -> Result<String, String> {
    if i + 1 >= argv.len() {
        return Err(format!("missing value after {flag}"));
    }
    Ok(argv[i + 1].clone())
}

fn parse_symbolic(raw: &str) -> Result<SymbolicCommand, String> {
    if raw.trim().is_empty() {
        return Err("symbolic command must not be empty".to_string());
    }
    let mut command_code = None;
    let mut language_code = None;
    let mut task = None;
    let mut modifiers = Vec::new();

    for (idx, part) in raw.split(';').enumerate() {
        if part.is_empty() {
            return Err("empty command segment".to_string());
        }
        if idx == 0 && !part.contains(':') {
            command_code = Some(part.to_string());
            continue;
        }
        let (key, value) = part
            .split_once(':')
            .ok_or_else(|| format!("invalid segment '{part}'"))?;
        match key {
            "P" | "R" | "J" | "T" | "G" | "S" | "M" | "Q" => {
                if language_code.is_some() {
                    return Err("duplicate language segment".to_string());
                }
                if task.is_some() {
                    return Err("ambiguous task segments".to_string());
                }
                language_code = Some(key.to_string());
                task = Some(value.to_string());
            }
            "MOD" => modifiers.push(validate_modifier(value)?.to_string()),
            code if idx == 0 => {
                command_code = Some(code.to_string());
                task = Some(value.to_string());
            }
            other => return Err(format!("invalid modifier or segment '{other}'")),
        }
    }

    let command_code = command_code.ok_or_else(|| "missing command code".to_string())?;
    let command = decode_command(&command_code)?;
    let language = match language_code.as_deref() {
        Some(code) => Some(decode_language(code)?.to_string()),
        None => None,
    };
    let task = task.ok_or_else(|| "missing task".to_string())?;
    validate_task(&task)?;

    Ok(SymbolicCommand {
        command,
        command_code,
        language,
        language_code,
        task,
        modifiers,
        raw: raw.to_string(),
    })
}

fn encode_symbolic(
    command: &str,
    language: Option<&str>,
    task: &str,
    modifiers: &[String],
) -> Result<String, String> {
    let command_code = encode_command(command)?;
    validate_task(task)?;
    let mut out = command_code.to_string();
    if let Some(language) = language {
        out.push(';');
        out.push_str(encode_language(language)?);
        out.push(':');
        out.push_str(task);
    } else {
        out.push(':');
        out.push_str(task);
    }
    for modifier in modifiers {
        out.push_str(";MOD:");
        out.push_str(validate_modifier(modifier)?);
    }
    Ok(out)
}

fn parse_batch(raw: &str) -> Result<serde_json::Value, String> {
    let body = raw
        .strip_prefix("B:")
        .ok_or_else(|| "batch expression must start with 'B:'".to_string())?;
    let mut items = Vec::new();
    for part in body.split('|') {
        let item = part.trim();
        if !item.starts_with('[') || !item.ends_with(']') {
            return Err(format!("batch item '{item}' must be wrapped in []"));
        }
        items.push(parse_symbolic(&item[1..item.len() - 1])?);
    }
    if items.is_empty() {
        return Err("batch must include at least one item".to_string());
    }
    Ok(json!({
        "ok": true,
        "mode": "SEQ",
        "items": items
    }))
}

fn encode_command(command: &str) -> Result<&'static str, String> {
    match command.to_ascii_uppercase().as_str() {
        "CODE" => Ok("C"),
        "DATA" => Ok("D"),
        "DOC" | "DOCUMENT" => Ok("O"),
        "TEST" => Ok("TST"),
        other => Err(format!("invalid command '{other}'")),
    }
}

fn decode_command(code: &str) -> Result<String, String> {
    match code {
        "C" => Ok("CODE".to_string()),
        "D" => Ok("DATA".to_string()),
        "O" => Ok("DOC".to_string()),
        "TST" => Ok("TEST".to_string()),
        other => Err(format!("invalid command code '{other}'")),
    }
}

fn encode_language(language: &str) -> Result<&'static str, String> {
    match language.to_ascii_uppercase().as_str() {
        "PYTHON" | "PY" => Ok("P"),
        "RUST" | "RS" => Ok("R"),
        "JAVASCRIPT" | "JS" => Ok("J"),
        "TYPESCRIPT" | "TS" => Ok("T"),
        "GO" => Ok("G"),
        "SHELL" | "SH" => Ok("S"),
        "MARKDOWN" | "MD" => Ok("M"),
        "SQL" => Ok("Q"),
        other => Err(format!("invalid language '{other}'")),
    }
}

fn decode_language(code: &str) -> Result<&'static str, String> {
    match code {
        "P" => Ok("PYTHON"),
        "R" => Ok("RUST"),
        "J" => Ok("JAVASCRIPT"),
        "T" => Ok("TYPESCRIPT"),
        "G" => Ok("GO"),
        "S" => Ok("SHELL"),
        "M" => Ok("MARKDOWN"),
        "Q" => Ok("SQL"),
        other => Err(format!("invalid language code '{other}'")),
    }
}

fn validate_task(task: &str) -> Result<(), String> {
    if task.is_empty() {
        return Err("task must not be empty".to_string());
    }
    if !task
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || matches!(c, '_' | '-' | '.'))
    {
        return Err(format!("invalid task '{task}'"));
    }
    Ok(())
}

fn validate_modifier(modifier: &str) -> Result<&str, String> {
    match modifier {
        "SAFE" | "FAST" | "AUDIT" | "DRYRUN" => Ok(modifier),
        other => Err(format!("invalid modifier '{other}'")),
    }
}

fn validate_dsl(text: &str) -> serde_json::Value {
    let mut errors = Vec::new();
    let mut counts = json!({
        "use_directives": 0,
        "skills": 0,
        "resources": 0,
        "symbolic_commands": 0
    });

    let lines: Vec<&str> = text.lines().collect();
    let mut i = 0;
    while i < lines.len() {
        let line = lines[i].trim();
        if line.is_empty() || line.starts_with('#') {
            i += 1;
            continue;
        }
        if line.starts_with("use:") {
            if valid_use_directive(line) {
                counts["use_directives"] = json!(counts["use_directives"].as_u64().unwrap() + 1);
            } else {
                errors.push(format!("invalid use directive on line {}", i + 1));
            }
            i += 1;
            continue;
        }
        if line.starts_with('$') {
            if valid_prefixed_identifier(line, '$') {
                counts["skills"] = json!(counts["skills"].as_u64().unwrap() + 1);
            } else {
                errors.push(format!("invalid skill invocation on line {}", i + 1));
            }
            i += 1;
            continue;
        }
        if line.starts_with('@') {
            if valid_resource_ref(line) {
                counts["resources"] = json!(counts["resources"].as_u64().unwrap() + 1);
            } else {
                errors.push(format!("invalid resource reference on line {}", i + 1));
            }
            i += 1;
            continue;
        }
        if line.starts_with("tool ") || line.starts_with("task ") {
            let kind = if line.starts_with("tool ") {
                "tool"
            } else {
                "task"
            };
            let start_line = i + 1;
            let mut block = line.to_string();
            while !block.contains('}') && i + 1 < lines.len() {
                i += 1;
                block.push('\n');
                block.push_str(lines[i]);
            }
            errors.push(format!(
                "unsupported executable legacy {kind} block starting on line {start_line}"
            ));
            i += 1;
            continue;
        }
        if looks_like_block_legacy_semantic(line) {
            errors.push(format!(
                "unsupported executable legacy statement on line {}",
                i + 1
            ));
            i += 1;
            continue;
        }
        if parse_symbolic(line).is_ok() {
            counts["symbolic_commands"] = json!(counts["symbolic_commands"].as_u64().unwrap() + 1);
            i += 1;
            continue;
        }
        errors.push(format!("unsupported DSL statement on line {}", i + 1));
        i += 1;
    }

    json!({
        "ok": errors.is_empty(),
        "valid": errors.is_empty(),
        "subset": "local-fixture-v1",
        "accepted_syntax": [
            "use:<identifier>",
            "$skill-name",
            "@workspace/path",
            "symbolic command lines"
        ],
        "rejected_semantics": [
            "tool blocks",
            "task blocks",
            "OAuth or network resources",
            "shell execution",
            "provider calls",
            "automatic skill invocation"
        ],
        "counts": counts,
        "errors": errors
    })
}

fn valid_use_directive(line: &str) -> bool {
    line.strip_prefix("use:").is_some_and(valid_identifier_body)
}

fn valid_prefixed_identifier(line: &str, prefix: char) -> bool {
    let name = line.trim_start_matches(prefix);
    valid_identifier_body(name)
}

fn valid_identifier_body(name: &str) -> bool {
    !name.is_empty()
        && name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_'))
}

fn valid_resource_ref(line: &str) -> bool {
    let value = line.trim_start_matches('@');
    if value.contains("://") || value.contains(':') {
        return false;
    }
    let path = Path::new(value);
    !value.is_empty()
        && !value.starts_with('/')
        && !value.starts_with('\\')
        && !path.is_absolute()
        && !value.split('/').any(|part| part == "..")
        && !value.split('\\').any(|part| part == "..")
        && reject_sensitive_path(path).is_ok()
        && value
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '/' | '.'))
}

fn looks_like_block_legacy_semantic(line: &str) -> bool {
    let starts_with_ignore_case = |prefix: &str| {
        line.get(..prefix.len())
            .is_some_and(|head| head.eq_ignore_ascii_case(prefix))
    };

    starts_with_ignore_case("oauth")
        || starts_with_ignore_case("provider")
        || starts_with_ignore_case("shell ")
        || starts_with_ignore_case("exec ")
        || starts_with_ignore_case("run ")
        || starts_with_ignore_case("http://")
        || starts_with_ignore_case("https://")
        || starts_with_ignore_case("resource://")
}

fn serve_mcp(allowed_root: &Path) -> Result<(), String> {
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    for line in stdin.lock().lines() {
        let line = line.map_err(|e| format!("failed to read MCP request: {e}"))?;
        if line.trim().is_empty() {
            continue;
        }
        let response = match serde_json::from_str::<serde_json::Value>(&line) {
            Ok(request) => handle_mcp_request(allowed_root, &request),
            Err(_) => Some(mcp_error_response(
                json!(null),
                McpError::parse_error("malformed JSON"),
            )),
        };
        if let Some(response) = response {
            writeln!(stdout, "{}", response)
                .map_err(|e| format!("failed to write MCP response: {e}"))?;
            stdout
                .flush()
                .map_err(|e| format!("failed to flush MCP response: {e}"))?;
        }
    }
    Ok(())
}

fn handle_mcp_request(
    allowed_root: &Path,
    request: &serde_json::Value,
) -> Option<serde_json::Value> {
    let id = request.get("id").cloned().unwrap_or(json!(null));
    if !request.is_object() {
        return Some(mcp_error_response(
            id,
            McpError::invalid_request("request must be a JSON object"),
        ));
    }
    let Some(method) = request.get("method").and_then(|method| method.as_str()) else {
        return Some(mcp_error_response(
            id,
            McpError::invalid_request("request method must be a string"),
        ));
    };
    request.get("id")?;
    let result = match method {
        "initialize" => Ok(json!({
            "protocolVersion": "2025-06-18",
            "serverInfo": {"name": "ctxt-runtime", "version": env!("CARGO_PKG_VERSION")},
            "capabilities": {"tools": {}}
        })),
        "tools/list" => Ok(json!({
            "tools": [{
                "name": "ctxt.read_file",
                "description": "Read a file under the explicit allowed root.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "max_bytes": {"type": "integer"}
                    },
                    "required": ["path"]
                }
            }]
        })),
        "tools/call" => {
            let params = request
                .get("params")
                .and_then(|params| params.as_object())
                .ok_or_else(|| McpError::invalid_params("params must be an object"));
            params.and_then(|params| {
                if params.get("name").and_then(|name| name.as_str()) != Some("ctxt.read_file") {
                    return Err(McpError::invalid_params("unsupported tool name"));
                }
                let args = params
                    .get("arguments")
                    .and_then(|arguments| arguments.as_object())
                    .ok_or_else(|| McpError::invalid_params("arguments must be an object"))?;
                let path = args
                    .get("path")
                    .and_then(|path| path.as_str())
                    .ok_or_else(|| McpError::invalid_params("path must be a string"))?;
                let max_bytes = match args.get("max_bytes") {
                    Some(value) => value
                        .as_u64()
                        .ok_or_else(|| McpError::invalid_params("max_bytes must be an integer"))?
                        .min(DEFAULT_MAX_FILE_BYTES),
                    None => DEFAULT_MAX_FILE_BYTES,
                };
                read_allowed_file(allowed_root, path, max_bytes).map(|payload| {
                    json!({
                        "content": [{"type": "text", "text": payload["text"]}],
                        "structuredContent": payload
                    })
                })
            })
        }
        _ => Err(McpError::method_not_found("unsupported MCP method")),
    };

    match result {
        Ok(result) => Some(json!({"jsonrpc": "2.0", "id": id, "result": result})),
        Err(error) => Some(mcp_error_response(id, error)),
    }
}

fn mcp_error_response(id: serde_json::Value, error: McpError) -> serde_json::Value {
    json!({
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": error.code,
            "message": error.message,
            "data": {
                "kind": error.kind,
                "detail": error.detail
            }
        }
    })
}

fn bounded_mcp_detail(detail: &str) -> String {
    detail
        .chars()
        .filter(|ch| !matches!(ch, '\r' | '\n'))
        .take(200)
        .collect()
}

fn read_allowed_file(
    allowed_root: &Path,
    requested: &str,
    max_bytes: u64,
) -> Result<serde_json::Value, McpError> {
    let allowed_root = std::fs::canonicalize(allowed_root)
        .map_err(|_| McpError::access_denied("allowed root could not be resolved"))?;
    let requested_path = Path::new(requested);
    if requested_path.is_absolute() {
        return Err(McpError::access_denied(
            "absolute paths are blocked for MCP file inputs",
        ));
    }
    if requested_path
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err(McpError::access_denied("path traversal is blocked"));
    }
    reject_sensitive_path(requested_path)
        .map_err(|_| McpError::denied_sensitive_path("sensitive path is blocked"))?;
    let candidate = allowed_root.join(requested_path);
    let canonical = std::fs::canonicalize(&candidate)
        .map_err(|_| McpError::access_denied("requested path could not be resolved"))?;
    reject_sensitive_path(&canonical)
        .map_err(|_| McpError::denied_sensitive_path("sensitive path is blocked"))?;
    if !canonical.starts_with(&allowed_root) {
        return Err(McpError::outside_allowed_root(
            "resolved path is outside allowed root",
        ));
    }
    let metadata = std::fs::metadata(&canonical)
        .map_err(|_| McpError::access_denied("file metadata denied"))?;
    if !metadata.is_file() {
        return Err(McpError::invalid_params("requested path is not a file"));
    }
    if metadata.len() > DEFAULT_MAX_FILE_BYTES {
        return Err(McpError::file_too_large(&format!(
            "file size {} exceeds max {}",
            metadata.len(),
            DEFAULT_MAX_FILE_BYTES
        )));
    }
    let mut file =
        std::fs::File::open(&canonical).map_err(|_| McpError::access_denied("file open denied"))?;
    let mut bytes = Vec::new();
    std::io::Read::by_ref(&mut file)
        .take(max_bytes)
        .read_to_end(&mut bytes)
        .map_err(|_| McpError::access_denied("file read denied"))?;
    let rel = canonical
        .strip_prefix(&allowed_root)
        .unwrap_or(&canonical)
        .to_string_lossy()
        .replace('\\', "/");
    Ok(json!({
        "file": rel,
        "path": rel,
        "bytes": bytes.len(),
        "file_bytes": metadata.len(),
        "returned_bytes": bytes.len(),
        "truncated": metadata.len() > bytes.len() as u64,
        "sha256": sha256_hex(&bytes),
        "sha256_scope": "returned_bytes",
        "text": String::from_utf8_lossy(&bytes)
    }))
}

fn read_runtime_text(path: &str, label: &str) -> Result<String, String> {
    let bytes = read_runtime_bytes(path, label)?;
    String::from_utf8(bytes).map_err(|e| format!("{label} is not valid UTF-8: {e}"))
}

fn read_runtime_bytes(path: &str, label: &str) -> Result<Vec<u8>, String> {
    let requested_path = Path::new(path);
    validate_local_input_path(requested_path)?;
    let canonical = canonical_runtime_input_path(requested_path)?;
    let metadata = std::fs::metadata(&canonical)
        .map_err(|e| format!("failed to stat {label} '{}': {e}", requested_path.display()))?;
    if !metadata.is_file() {
        return Err(format!("{label} is not a file"));
    }
    if metadata.len() > DEFAULT_MAX_FILE_BYTES {
        return Err(format!(
            "{label} is too large: {} bytes exceeds max {}",
            metadata.len(),
            DEFAULT_MAX_FILE_BYTES
        ));
    }
    std::fs::read(&canonical)
        .map_err(|e| format!("failed to read {label} '{}': {e}", requested_path.display()))
}

fn canonical_runtime_input_path(path: &Path) -> Result<std::path::PathBuf, String> {
    let root = std::env::current_dir()
        .map_err(|e| format!("failed to determine current worktree root: {e}"))
        .and_then(|cwd| {
            std::fs::canonicalize(&cwd)
                .map_err(|e| format!("failed to resolve current worktree root: {e}"))
        })?;
    let canonical = std::fs::canonicalize(path).map_err(|e| {
        format!(
            "failed to resolve runtime file input '{}': {e}",
            path.display()
        )
    })?;
    reject_sensitive_path(&canonical)?;
    if !canonical.starts_with(&root) {
        return Err("resolved path is outside current worktree".to_string());
    }
    Ok(canonical)
}

fn validate_local_input_path(path: &Path) -> Result<(), String> {
    if path.is_absolute() {
        return Err("absolute paths are blocked for runtime file inputs".to_string());
    }
    if path
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err("path traversal is blocked for runtime file inputs".to_string());
    }
    reject_sensitive_path(path)
}

fn reject_sensitive_path(path: &Path) -> Result<(), String> {
    for component in path.components() {
        if let Component::Normal(part) = component {
            let name = part.to_string_lossy().to_ascii_lowercase();
            if is_sensitive_name(&name) {
                return Err("sensitive path is blocked".to_string());
            }
        }
    }
    Ok(())
}

fn is_sensitive_name(name: &str) -> bool {
    name == ".env"
        || name.starts_with(".env.")
        || name == ".envrc"
        || name == ".netrc"
        || name == ".git-credentials"
        || name == "id_rsa"
        || name == "id_ed25519"
        || name.ends_with(".pem")
        || name.ends_with(".key")
        || name.contains("token")
        || name.contains("secret")
}

fn detect_illegible_cot(text: &str) -> serde_json::Value {
    let patterns = [
        ("hidden_chain_of_thought", "hidden chain of thought"),
        ("private_reasoning", "private reasoning"),
        ("unverifiable_leap", "unverifiable leap"),
        ("scratchpad_leak", "scratchpad"),
        ("opaque_reasoning", "cannot explain why"),
    ];
    let lower = text.to_ascii_lowercase();
    let findings: Vec<_> = patterns
        .iter()
        .filter(|(_, needle)| lower.contains(*needle))
        .map(|(id, needle)| json!({"id": id, "pattern": needle}))
        .collect();
    json!({
        "ok": true,
        "detected": !findings.is_empty(),
        "findings": findings,
        "scope": "deterministic phrase heuristic for trace review triage"
    })
}

fn emit_error(json_output: bool, message: &str) {
    if json_output {
        eprintln!("{}", json!({"ok": false, "error": message}));
    } else {
        eprintln!("error: {message}");
    }
}

fn sha256_hex(input: &[u8]) -> String {
    let digest = sha256(input);
    let mut out = String::with_capacity(64);
    for byte in digest {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn sha256(input: &[u8]) -> [u8; 32] {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h = [
        0x6a09e667u32,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    ];
    let bit_len = (input.len() as u64) * 8;
    let mut data = input.to_vec();
    data.push(0x80);
    while (data.len() % 64) != 56 {
        data.push(0);
    }
    data.extend_from_slice(&bit_len.to_be_bytes());

    for chunk in data.chunks(64) {
        let mut w = [0u32; 64];
        for (i, word) in w.iter_mut().take(16).enumerate() {
            let j = i * 4;
            *word = u32::from_be_bytes([chunk[j], chunk[j + 1], chunk[j + 2], chunk[j + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha256_matches_known_vector() {
        assert_eq!(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn parser_roundtrip() {
        let encoded = encode_symbolic("CODE", Some("PYTHON"), "FIB", &[]).unwrap();
        assert_eq!(encoded, "C;P:FIB");
        let parsed = parse_symbolic(&encoded).unwrap();
        assert_eq!(parsed.command, "CODE");
        assert_eq!(parsed.language.as_deref(), Some("PYTHON"));
        assert_eq!(parsed.task, "FIB");
    }

    #[test]
    fn rejects_invalid_modifier() {
        assert!(parse_symbolic("C;P:FIB;MOD:UNSAFE").is_err());
    }
}
