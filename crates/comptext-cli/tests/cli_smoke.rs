use std::io::Write;
use std::process::Command;
use std::process::Stdio;
use std::sync::{Mutex, MutexGuard, OnceLock};

static TEST_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

fn test_lock() -> MutexGuard<'static, ()> {
    TEST_LOCK
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

struct FileGuard {
    path: std::path::PathBuf,
    original: Option<Vec<u8>>,
}

impl FileGuard {
    fn new(path: impl Into<std::path::PathBuf>) -> Self {
        let path = path.into();
        let original = std::fs::read(&path).ok();
        Self { path, original }
    }
}

impl Drop for FileGuard {
    fn drop(&mut self) {
        if let Some(ref content) = self.original {
            let _ = std::fs::write(&self.path, content);
        } else if self.path.exists() {
            let _ = std::fs::remove_file(&self.path);
        }
    }
}

struct DirGuard {
    path: std::path::PathBuf,
    backup: std::path::PathBuf,
    moved: bool,
}

impl DirGuard {
    fn new(path: impl Into<std::path::PathBuf>) -> Self {
        let path = path.into();
        let backup = path.with_extension(format!("smoke-backup-{}", std::process::id()));
        let moved = if path.exists() {
            let _ = std::fs::remove_dir_all(&backup);
            std::fs::rename(&path, &backup).is_ok()
        } else {
            false
        };
        Self {
            path,
            backup,
            moved,
        }
    }
}

impl Drop for DirGuard {
    fn drop(&mut self) {
        if self.path.exists() {
            let _ = std::fs::remove_dir_all(&self.path);
        }
        if self.moved && self.backup.exists() {
            let _ = std::fs::rename(&self.backup, &self.path);
        }
    }
}

fn run(args: &[&str]) -> String {
    let output = Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(args)
        .output()
        .expect("ctxt binary should run");
    assert!(output.status.success(), "command failed: {args:?}");
    String::from_utf8(output.stdout).expect("stdout should be UTF-8")
}

fn run_fail(args: &[&str]) -> serde_json::Value {
    let output = Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(args)
        .output()
        .expect("ctxt binary should run");
    assert!(!output.status.success(), "command should fail: {args:?}");
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    serde_json::from_str(&stderr).expect("error JSON should parse")
}

fn run_fail_in_dir(args: &[&str], current_dir: &std::path::Path) -> serde_json::Value {
    let output = Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .current_dir(current_dir)
        .args(args)
        .output()
        .expect("ctxt binary should run");
    assert!(!output.status.success(), "command should fail: {args:?}");
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    serde_json::from_str(&stderr).expect("error JSON should parse")
}

fn run_with_stdin(args: &[&str], stdin: &str) -> String {
    run_with_stdin_in_dir(args, stdin, std::path::Path::new("."))
}

fn run_with_stdin_in_dir(args: &[&str], stdin: &str, current_dir: &std::path::Path) -> String {
    let mut child = Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .current_dir(current_dir)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("ctxt binary should spawn");
    child
        .stdin
        .as_mut()
        .expect("stdin should be piped")
        .write_all(stdin.as_bytes())
        .expect("stdin write should succeed");
    let output = child.wait_with_output().expect("ctxt should exit");
    assert!(output.status.success(), "command failed: {args:?}");
    String::from_utf8(output.stdout).expect("stdout should be UTF-8")
}

fn assert_mcp_error(value: &serde_json::Value, id: serde_json::Value, code: i64, kind: &str) {
    assert_eq!(value["jsonrpc"], "2.0");
    assert_eq!(value["id"], id);
    assert_eq!(value["error"]["code"], code);
    assert!(value["error"]["message"].as_str().unwrap().len() > 0);
    assert_eq!(value["error"]["data"]["kind"], kind);
    assert!(value["error"]["data"]["detail"].as_str().unwrap().len() > 0);
}

#[cfg(unix)]
fn create_file_link(target: &std::path::Path, link: &std::path::Path) -> std::io::Result<()> {
    std::os::unix::fs::symlink(target, link)
}

#[cfg(windows)]
fn create_file_link(target: &std::path::Path, link: &std::path::Path) -> std::io::Result<()> {
    std::os::windows::fs::symlink_file(target, link)
}

fn symlink_escape_fixture(
    root_name: &str,
    outside_name: &str,
    outside_file_name: &str,
    outside_content: &[u8],
    link_name: &str,
) -> Option<(DirGuard, DirGuard, std::path::PathBuf)> {
    let root = std::path::PathBuf::from(root_name);
    let outside = std::path::PathBuf::from(outside_name);
    let root_guard = DirGuard::new(&root);
    let outside_guard = DirGuard::new(&outside);

    std::fs::create_dir(&root).expect("fixture root should be created");
    std::fs::create_dir(&outside).expect("outside fixture should be created");
    let outside_file = outside.join(outside_file_name);
    std::fs::write(&outside_file, outside_content).expect("outside fixture file should be written");

    let outside_file =
        std::fs::canonicalize(&outside_file).expect("outside fixture file should canonicalize");
    let link = root.join(link_name);
    match create_file_link(&outside_file, &link) {
        Ok(()) => Some((root_guard, outside_guard, root)),
        Err(_) => None,
    }
}

fn valid_phase_4f_proposal(id: &str) -> serde_json::Value {
    serde_json::json!({
        "schema_version": "proposal.v1",
        "id": id,
        "created_at": "2026-06-13T12:00:00Z",
        "phase": "Phase 4f",
        "title": "Proposal Artifact Contract",
        "summary": "Read-only proposal artifact contract.",
        "intent": "Prepare proposal-before-apply inspection without applying changes.",
        "allowed_files": ["src/cli.rs"],
        "forbidden_scope": ["proposal apply"],
        "changes": [
            {
                "path": "src/cli.rs",
                "action": "modify",
                "summary": "Add read-only proposal commands."
            }
        ],
        "validation": ["cargo test"],
        "network": "offline-only",
        "secrets": "no secrets read",
        "status": "draft"
    })
}

fn valid_phase_5b_review(id: &str, role_id: &str) -> serde_json::Value {
    serde_json::json!({
        "schema_version": "review.v1",
        "id": id,
        "created_at": "2026-06-13T15:00:00Z",
        "phase": "Phase 5b",
        "role_id": role_id,
        "target": "ctxt --json subagents list",
        "summary": "Static contract review fixture.",
        "findings": [
            {
                "id": "finding-1",
                "severity": "info",
                "summary": "The contract is static."
            }
        ],
        "risks": [
            {
                "id": "risk-1",
                "severity": "low",
                "summary": "No runtime execution is represented."
            }
        ],
        "recommendations": [
            {
                "id": "recommendation-1",
                "action": "keep",
                "summary": "Keep review artifacts contract-only."
            }
        ],
        "validation_refs": ["cargo test"],
        "safety_flags": {
            "network_used": false,
            "external_agents_invoked": false,
            "subagents_executed": false,
            "apply_performed": false,
            "git_write_performed": false,
            "secrets_accessed": false
        },
        "status": "draft"
    })
}

#[test]
fn ctxt_parse_json_roundtrips_symbolic_command() {
    let _guard = test_lock();
    let stdout = run(&["parse", "C;P:FIB", "--json"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("parse JSON should parse");
    assert_eq!(value["command"], "CODE");
    assert_eq!(value["command_code"], "C");
    assert_eq!(value["language"], "PYTHON");
    assert_eq!(value["task"], "FIB");
}

#[test]
fn ctxt_encode_emits_expected_symbolic_command() {
    let _guard = test_lock();
    let stdout = run(&[
        "encode",
        "--command",
        "CODE",
        "--language",
        "PYTHON",
        "--task",
        "FIB",
    ]);
    assert_eq!(stdout.trim(), "C;P:FIB");
}

#[test]
fn ctxt_encode_json_reports_stable_shape() {
    let _guard = test_lock();
    let stdout = run(&[
        "encode",
        "--command",
        "CODE",
        "--language",
        "PYTHON",
        "--task",
        "FIB",
        "--json",
    ]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("encode JSON should parse");
    assert_eq!(value["ok"], true);
    assert_eq!(value["encoded"], "C;P:FIB");
    assert_eq!(value["parsed"]["command"], "CODE");
    assert_eq!(value["parsed"]["command_code"], "C");
    assert_eq!(value["parsed"]["language"], "PYTHON");
    assert_eq!(value["parsed"]["language_code"], "P");
    assert_eq!(value["parsed"]["task"], "FIB");
    assert_eq!(value["parsed"]["modifiers"].as_array().unwrap().len(), 0);
    assert_eq!(value["parsed"]["raw"], "C;P:FIB");
}

#[test]
fn ctxt_batch_parses_items() {
    let _guard = test_lock();
    let stdout = run(&["batch", "B:[D:SUM]|[C;P:FIB]", "--json"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("batch JSON should parse");
    assert_eq!(value["mode"], "SEQ");
    assert_eq!(value["items"].as_array().unwrap().len(), 2);
    assert_eq!(value["items"][0]["command"], "DATA");
    assert_eq!(value["items"][1]["language"], "PYTHON");
}

#[test]
fn ctxt_rejects_invalid_command_language_and_modifier() {
    let _guard = test_lock();
    let invalid_command = run_fail(&["parse", "Z:FIB", "--json"]);
    assert!(invalid_command["error"]
        .as_str()
        .unwrap()
        .contains("invalid command"));

    let invalid_language = run_fail(&[
        "encode",
        "--command",
        "CODE",
        "--language",
        "KLINGON",
        "--task",
        "FIB",
        "--json",
    ]);
    assert!(invalid_language["error"]
        .as_str()
        .unwrap()
        .contains("invalid language"));

    let invalid_modifier = run_fail(&["parse", "C;P:FIB;MOD:UNSAFE", "--json"]);
    assert!(invalid_modifier["error"]
        .as_str()
        .unwrap()
        .contains("invalid modifier"));
}

#[test]
fn ctxt_rejects_ambiguous_and_malformed_symbolic_commands() {
    let _guard = test_lock();
    let cases = [
        ("C;;P:FIB", "empty command segment"),
        ("C;P:FIB;R:ALT", "duplicate language segment"),
        ("C", "missing task"),
        ("C;P:BAD TASK", "invalid task"),
        ("C:FIB;P:BAR", "ambiguous task segments"),
    ];

    for (input, expected) in cases {
        let error = run_fail(&["parse", input, "--json"]);
        assert!(
            error["error"].as_str().unwrap().contains(expected),
            "expected {input} to fail with {expected}, got {error}"
        );
    }
}

#[test]
fn ctxt_batch_rejects_malformed_items() {
    let _guard = test_lock();
    let cases = [
        ("[C:FIB]", "batch expression must start"),
        ("B:C:FIB", "must be wrapped"),
        ("B:[C:FIB]|", "must be wrapped"),
        ("B:[Z:FIB]", "invalid command"),
    ];

    for (input, expected) in cases {
        let error = run_fail(&["batch", input, "--json"]);
        assert!(
            error["error"].as_str().unwrap().contains(expected),
            "expected {input} to fail with {expected}, got {error}"
        );
    }
}

#[test]
fn ctxt_dsl_validate_accepts_basic_fixture() {
    let _guard = test_lock();
    let stdout = run(&["dsl", "validate", "examples/basic.ctxt", "--json"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("DSL validate JSON should parse");
    assert_eq!(value["valid"], true);
    assert_eq!(value["subset"], "local-fixture-v1");
    assert_eq!(value["counts"]["use_directives"], 1);
    assert_eq!(value["counts"]["skills"], 1);
    assert_eq!(value["counts"]["resources"], 1);
    assert_eq!(value["counts"]["symbolic_commands"], 1);
    assert!(value["accepted_syntax"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "use:<identifier>"));
    assert!(value["rejected_semantics"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "tool blocks"));
}

#[test]
fn ctxt_dsl_validate_rejects_invalid_fixture() {
    let _guard = test_lock();
    let fixture = std::path::Path::new("examples/invalid-smoke.ctxt");
    let _fixture_guard = FileGuard::new(fixture);
    std::fs::write(
        fixture,
        "$bad skill\n@../secret\nuse:bad value\nnot-a-symbolic command\n",
    )
    .unwrap();

    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["dsl", "validate", "examples/invalid-smoke.ctxt", "--json"])
        .output()
        .expect("ctxt binary should run");
    assert!(!output.status.success());
    let stdout = String::from_utf8(output.stdout).expect("stdout should be UTF-8");
    let report: serde_json::Value =
        serde_json::from_str(&stdout).expect("DSL invalid report should parse");
    assert_eq!(report["valid"], false);
    assert!(report["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("invalid skill")));
    assert!(report["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("invalid resource")));
    assert!(report["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("invalid use directive")));
}

#[test]
fn ctxt_dsl_validate_rejects_executable_legacy_semantics() {
    let _guard = test_lock();
    let fixture = std::path::Path::new("examples/invalid-executable-semantics.ctxt");
    let _fixture_guard = FileGuard::new(fixture);
    std::fs::write(
        fixture,
        [
            "tool read_context {",
            "  name: \"read_context\"",
            "  description: \"Read context from an allowed root.\"",
            "}",
            "task validate_basic {",
            "  name: \"validate_basic\"",
            "  handler: validate_basic",
            "}",
            "@https://example.com/resource",
            "@resource://database/users",
            "provider openai",
            "shell echo hi",
        ]
        .join("\n"),
    )
    .unwrap();

    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args([
            "dsl",
            "validate",
            "examples/invalid-executable-semantics.ctxt",
            "--json",
        ])
        .output()
        .expect("ctxt binary should run");
    assert!(!output.status.success());
    let stdout = String::from_utf8(output.stdout).expect("stdout should be UTF-8");
    let report: serde_json::Value =
        serde_json::from_str(&stdout).expect("DSL invalid report should parse");
    assert_eq!(report["valid"], false);
    assert_eq!(report["subset"], "local-fixture-v1");
    let errors = report["errors"].as_array().unwrap();
    assert!(errors.iter().any(|error| error
        .as_str()
        .unwrap()
        .contains("unsupported executable legacy tool block")));
    assert!(errors.iter().any(|error| error
        .as_str()
        .unwrap()
        .contains("unsupported executable legacy task block")));
    assert!(errors.iter().any(|error| error
        .as_str()
        .unwrap()
        .contains("invalid resource reference")));
    assert!(errors.iter().any(|error| error
        .as_str()
        .unwrap()
        .contains("unsupported executable legacy statement")));
}

#[test]
fn ctxt_evidence_hash_is_stable_sha256() {
    let _guard = test_lock();
    let stdout = run(&["evidence", "hash", "examples/trace.txt", "--json"]);
    let first: serde_json::Value =
        serde_json::from_str(&stdout).expect("evidence hash JSON should parse");
    let stdout_again = run(&["evidence", "hash", "examples/trace.txt", "--json"]);
    let second: serde_json::Value =
        serde_json::from_str(&stdout_again).expect("evidence hash JSON should parse");
    assert_eq!(first["sha256"], second["sha256"]);
    assert_eq!(first["algorithm"], "sha256");
}

#[test]
fn ctxt_evidence_hash_rejects_sensitive_and_traversal_paths() {
    let _guard = test_lock();
    let sensitive = run_fail(&["evidence", "hash", "token-note.txt", "--json"]);
    assert!(sensitive["error"]
        .as_str()
        .unwrap()
        .contains("sensitive path"));

    let traversal = run_fail(&["evidence", "hash", "../README.md", "--json"]);
    assert!(traversal["error"]
        .as_str()
        .unwrap()
        .contains("path traversal"));
}

#[test]
fn ctxt_evidence_hash_rejects_symlink_escape_when_supported() {
    let _guard = test_lock();
    let Some((_root_guard, _outside_guard, root)) = symlink_escape_fixture(
        "canonical-evidence-root-smoke",
        "canonical-evidence-outside-smoke",
        "outside.txt",
        b"outside evidence",
        "linked-evidence.txt",
    ) else {
        return;
    };

    let error = run_fail_in_dir(
        &["evidence", "hash", "linked-evidence.txt", "--json"],
        &root,
    );
    assert!(error["error"]
        .as_str()
        .unwrap()
        .contains("outside current worktree"));
}

#[test]
fn ctxt_dsl_validate_rejects_symlink_escape_when_supported() {
    let _guard = test_lock();
    let Some((_root_guard, _outside_guard, root)) = symlink_escape_fixture(
        "canonical-dsl-root-smoke",
        "canonical-dsl-outside-smoke",
        "outside.ctxt",
        b"$ctxt-runtime\n@workspace/README.md\n",
        "linked.ctxt",
    ) else {
        return;
    };

    let error = run_fail_in_dir(&["dsl", "validate", "linked.ctxt", "--json"], &root);
    assert!(error["error"]
        .as_str()
        .unwrap()
        .contains("outside current worktree"));
}

#[test]
fn ctxt_evidence_hash_matches_empty_file_vector() {
    let _guard = test_lock();
    let fixture = std::path::Path::new("empty-hash-smoke.txt");
    let _fixture_guard = FileGuard::new(fixture);
    std::fs::write(fixture, b"").unwrap();

    let stdout = run(&["evidence", "hash", "empty-hash-smoke.txt", "--json"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("evidence hash JSON should parse");
    assert_eq!(
        value["sha256"],
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    );
    assert_eq!(value["bytes"], 0);
}

#[test]
fn ctxt_mcp_allows_rooted_file_read() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "README.md", "max_bytes": 4096}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");
    assert_eq!(value["id"], 1);
    assert_eq!(value["result"]["structuredContent"]["path"], "README.md");
    assert!(
        value["result"]["structuredContent"]["sha256"]
            .as_str()
            .unwrap()
            .len()
            == 64
    );
}

#[test]
fn ctxt_mcp_returns_structured_parse_error_for_malformed_json() {
    let _guard = test_lock();
    let stdout = run_with_stdin(&["mcp", "serve", "--allowed-root", "."], "{not json\n");
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP error response should parse");

    assert_mcp_error(&value, serde_json::json!(null), -32700, "parse_error");
}

#[test]
fn ctxt_mcp_returns_structured_invalid_request_for_missing_method() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 8
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP error response should parse");

    assert_mcp_error(&value, serde_json::json!(8), -32600, "invalid_request");
}

#[test]
fn ctxt_mcp_returns_structured_invalid_request_for_non_string_method() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 9,
        "method": 7
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP error response should parse");

    assert_mcp_error(&value, serde_json::json!(9), -32600, "invalid_request");
}

#[test]
fn ctxt_mcp_notification_with_no_id_produces_no_response() {
    let _guard = test_lock();
    let notification = serde_json::json!({
        "jsonrpc": "2.0",
        "method": "tools/list"
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(notification.to_string() + "\n"),
    );

    assert_eq!(stdout, "");
}

#[test]
fn ctxt_mcp_returns_structured_method_not_found() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": "missing",
        "method": "missing/method"
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP error response should parse");

    assert_mcp_error(
        &value,
        serde_json::json!("missing"),
        -32601,
        "method_not_found",
    );
}

#[test]
fn ctxt_mcp_returns_structured_invalid_params() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"max_bytes": "large"}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP error response should parse");

    assert_mcp_error(&value, serde_json::json!(6), -32602, "invalid_params");
}

#[test]
fn ctxt_mcp_blocks_traversal() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "../legacy-codex/README.md"}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");
    assert_mcp_error(&value, serde_json::json!(2), -32000, "access_denied");
    assert!(value["error"]["data"]["detail"]
        .as_str()
        .unwrap()
        .contains("traversal"));
}

#[test]
fn ctxt_mcp_blocks_sensitive_paths_without_reading_content() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "token-note.txt"}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");
    assert_mcp_error(
        &value,
        serde_json::json!(3),
        -32000,
        "denied_sensitive_path",
    );
    assert!(!value["error"]["data"]["detail"]
        .as_str()
        .unwrap()
        .contains("token-note.txt"));
}

#[test]
fn ctxt_mcp_blocks_symlink_escape_when_supported() {
    let _guard = test_lock();
    let Some((_root_guard, _outside_guard, root)) = symlink_escape_fixture(
        "canonical-mcp-root-smoke",
        "canonical-mcp-outside-smoke",
        "outside.txt",
        b"outside mcp",
        "linked.txt",
    ) else {
        return;
    };
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "linked.txt"}
        }
    });

    let stdout = run_with_stdin_in_dir(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
        &root,
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");
    assert_mcp_error(&value, serde_json::json!(5), -32000, "outside_allowed_root");
}

#[test]
fn ctxt_mcp_reports_returned_byte_hash_scope() {
    let _guard = test_lock();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "README.md", "max_bytes": 16}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");
    let payload = &value["result"]["structuredContent"];
    assert_eq!(payload["sha256_scope"], "returned_bytes");
    assert_eq!(payload["returned_bytes"], 16);
    assert!(payload["file_bytes"].as_u64().unwrap() >= 16);
}

#[test]
fn ctxt_mcp_blocks_file_too_large() {
    let _guard = test_lock();
    let fixture = std::path::Path::new("large-mcp-smoke.txt");
    let _fixture_guard = FileGuard::new(fixture);
    std::fs::write(fixture, vec![b'x'; 64 * 1024 + 1]).unwrap();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "ctxt.read_file",
            "arguments": {"path": "large-mcp-smoke.txt"}
        }
    });
    let stdout = run_with_stdin(
        &["mcp", "serve", "--allowed-root", "."],
        &(request.to_string() + "\n"),
    );
    let value: serde_json::Value =
        serde_json::from_str(stdout.trim()).expect("MCP response should parse");

    assert_mcp_error(&value, serde_json::json!(7), -32000, "file_too_large");
}

#[test]
fn ctxt_detect_illegible_cot_flags_trace_fixture() {
    let _guard = test_lock();
    let stdout = run(&["detect-illegible-cot", "examples/trace.txt", "--json"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("detect JSON should parse");
    assert_eq!(value["detected"], true);
    assert_eq!(value["findings"].as_array().unwrap().len(), 1);
}

#[test]
fn ctxt_detect_illegible_cot_reports_clean_trace() {
    let _guard = test_lock();
    let stdout = run(&["detect-illegible-cot", "examples/trace-clean.txt", "--json"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("detect JSON should parse");
    assert_eq!(value["ok"], true);
    assert_eq!(value["detected"], false);
    assert_eq!(value["findings"].as_array().unwrap().len(), 0);
    assert_eq!(
        value["scope"],
        "deterministic phrase heuristic for trace review triage"
    );
}

#[test]
fn help_mentions_safety_defaults() {
    let _guard = test_lock();
    let stdout = run(&["--help"]);
    assert!(stdout.contains("SAFETY DEFAULTS"));
    assert!(stdout.contains("network_default=deny"));
    assert!(stdout.contains("parse"));
    assert!(stdout.contains("evidence hash"));
    assert!(stdout.contains("detect-illegible-cot"));
}

#[test]
fn doctor_is_local_and_deterministic() {
    let _guard = test_lock();
    let stdout = run(&["doctor"]);
    assert!(stdout.contains("status: ok"));
    assert!(stdout.contains("provider_default: dummy"));
}

#[test]
fn doctor_json_is_machine_readable() {
    let _guard = test_lock();
    let stdout = run(&["--json", "doctor"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("doctor JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "doctor");
    assert_eq!(value["status"], "ok");
    assert_eq!(value["provider_default"], "dummy");
    assert_eq!(value["network_default"], "deny");
    assert_eq!(value["auth"]["required"], false);
}

#[test]
fn providers_include_dummy_and_ollama_variants() {
    let _guard = test_lock();
    let stdout = run(&["providers", "list"]);
    assert!(stdout.contains("dummy"));
    assert!(stdout.contains("ollama-local"));
    assert!(stdout.contains("ollama-cloud-direct"));
}

#[test]
fn providers_json_lists_stable_provider_objects() {
    let _guard = test_lock();
    let stdout = run(&["--json", "providers", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("providers JSON should parse");
    let providers = value["providers"]
        .as_array()
        .expect("providers should be an array");

    assert_eq!(value["ok"], true);
    assert!(providers.iter().any(|provider| {
        provider["name"] == "dummy" && provider["kind"] == "dummy" && provider["network"] == false
    }));
    assert!(providers
        .iter()
        .any(|provider| provider["name"] == "openai-compatible"));
}

#[test]
fn init_json_dry_run_reports_target_without_write() {
    let _guard = test_lock();
    let target_path = std::path::Path::new("comptext.smoke.toml");
    let _target_guard = FileGuard::new(target_path);
    if target_path.exists() {
        let _ = std::fs::remove_file(target_path);
    }

    let stdout = run(&[
        "--json",
        "init",
        "--dry-run",
        "--out",
        "comptext.smoke.toml",
    ]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("init JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "init");
    assert_eq!(value["dry_run"], true);
    assert_eq!(value["source"], "comptext.example.toml");
    assert_eq!(value["target"], "comptext.smoke.toml");
    assert!(!target_path.exists());
}

#[test]
fn init_json_writes_explicit_local_config_without_overwrite() {
    let _guard = test_lock();
    let target_path = std::path::Path::new("comptext.smoke.toml");
    let _target_guard = FileGuard::new(target_path);
    if target_path.exists() {
        let _ = std::fs::remove_file(target_path);
    }

    let stdout = run(&["--json", "init", "--out", "comptext.smoke.toml"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("init JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "init");
    assert_eq!(value["dry_run"], false);
    assert_eq!(value["target"], "comptext.smoke.toml");
    assert!(target_path.exists());

    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "init", "--out", "comptext.smoke.toml"])
        .output()
        .expect("ctxt binary should run");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let error: serde_json::Value =
        serde_json::from_str(&stderr).expect("overwrite error should be JSON");
    assert!(error["error"]["message"]
        .as_str()
        .unwrap()
        .contains("refusing to overwrite"));
}

#[test]
fn context_inspect_json_reports_pack_shape() {
    let _guard = test_lock();
    let stdout = run(&["--json", "context", "inspect"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("context inspect JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "context inspect");
    assert_eq!(value["schema_version"], "0.1");
    assert!(value["included_file_count"].as_u64().unwrap() > 0);
    assert!(value["included_files"]
        .as_array()
        .unwrap()
        .iter()
        .any(|file| { file.as_str().unwrap().ends_with("src/cli.rs") }));
    assert_eq!(value["policy"]["secrets_redacted"], true);
}

#[test]
fn context_pack_json_writes_latest_artifact() {
    let _guard = test_lock();
    let stdout = run(&["--json", "context", "pack", "--task", "JSON smoke pack"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("context pack JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "context pack");
    assert_eq!(value["path"], ".comptext/context_pack.latest.json");
    assert_eq!(value["task"], "JSON smoke pack");
    assert!(std::path::Path::new(".comptext/context_pack.latest.json").exists());
}

#[test]
fn artifacts_json_lists_and_reads_local_evidence() {
    let _guard = test_lock();
    let artifact_path = std::path::Path::new(".comptext/context_pack.latest.json");
    let _artifact_guard = FileGuard::new(artifact_path);
    run(&["--json", "context", "pack", "--task", "Artifact smoke"]);

    let list_stdout = run(&["--json", "artifacts", "list"]);
    let list_value: serde_json::Value =
        serde_json::from_str(&list_stdout).expect("artifacts list JSON should parse");
    let artifacts = list_value["artifacts"]
        .as_array()
        .expect("artifacts should be an array");
    assert_eq!(list_value["ok"], true);
    assert!(artifacts
        .iter()
        .any(|artifact| artifact["path"] == ".comptext/context_pack.latest.json"));

    let read_stdout = run(&[
        "--json",
        "artifacts",
        "read",
        ".comptext/context_pack.latest.json",
        "--max-bytes",
        "512",
    ]);
    let read_value: serde_json::Value =
        serde_json::from_str(&read_stdout).expect("artifacts read JSON should parse");
    assert_eq!(read_value["ok"], true);
    assert_eq!(read_value["command"], "artifacts read");
    assert_eq!(read_value["kind"], "runtime");
    assert!(read_value["content"]
        .as_str()
        .unwrap()
        .contains("Artifact smoke"));
}

#[test]
fn ask_json_dry_run_reports_artifacts_without_provider_call() {
    let _guard = test_lock();
    let stdout = run(&["--json", "ask", "--dry-run", "Summarize JSON contract"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("ask JSON should parse");
    let artifacts = value["artifacts"]
        .as_array()
        .expect("artifacts should be an array");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "ask");
    assert_eq!(value["dry_run"], true);
    assert_eq!(value["provider"], "dummy");
    assert!(artifacts
        .iter()
        .any(|path| path == ".comptext/context_pack.latest.json"));
}

#[test]
fn json_errors_are_machine_readable() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "unknown-command"])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value =
        serde_json::from_str(&stderr).expect("error JSON should parse from stderr");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("unsupported command"));
}

#[test]
fn ask_dummy_provider_succeeds() {
    let _guard = test_lock();
    let stdout = run(&["ask", "--provider", "dummy", "How do I test this repo?"]);
    assert!(stdout.contains("Response from dummy provider:"));
    assert!(stdout.contains("Mock LLM response from CompText Dummy Provider."));
    assert!(stdout.contains("Received prompt: \"How do I test this repo?\""));

    // Verify response file was written
    let response_path = std::path::Path::new(".comptext/model_response.latest.json");
    assert!(response_path.exists());
    let response_content = std::fs::read_to_string(response_path).unwrap();
    assert!(response_content.contains("\"provider\": \"dummy\""));
}

#[test]
fn ask_ollama_provider_respects_network_deny_policy() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["ask", "--provider", "ollama-local", "hello"])
        .output()
        .expect("ctxt binary should run");

    assert!(
        !output.status.success(),
        "command should fail because network is denied by policy"
    );
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let stderr_lower = stderr.to_ascii_lowercase();
    assert!(
        stderr_lower.contains("network access denied") && stderr_lower.contains("ollama-local"),
        "unexpected stderr from network-denied ollama run: {stderr}"
    );
}

#[test]
fn propose_dummy_provider_succeeds() {
    let _guard = test_lock();
    let latest_path = std::path::Path::new("proposals/proposal.latest.json");
    let _latest_guard = FileGuard::new(latest_path);
    let task = "Smoke temporary proposal";
    let slugified_path = std::path::Path::new("proposals/proposal_smoke_temporary_proposal.json");
    let _slugified_guard = FileGuard::new(slugified_path);
    if slugified_path.exists() {
        let _ = std::fs::remove_file(slugified_path);
    }

    let stdout = run(&["propose", "--provider", "dummy", task]);
    assert!(stdout.contains("Proposal generated successfully."));
    assert!(stdout.contains("Proposal file: proposals/proposal_smoke_temporary_proposal.json"));
    assert!(stdout.contains("Latest reference: proposals/proposal.latest.json"));

    assert!(slugified_path.exists());
    assert!(latest_path.exists());

    let proposal_content = std::fs::read_to_string(latest_path).unwrap();
    assert!(proposal_content.contains("\"task\": \"Smoke temporary proposal\""));
    assert!(proposal_content.contains("\"schema_version\": \"0.1\""));
    assert!(proposal_content.contains("Mock patch generated by dummy provider:"));
}

#[test]
fn propose_json_reports_proposal_artifacts() {
    let _guard = test_lock();
    let latest_path = std::path::Path::new("proposals/proposal.latest.json");
    let _latest_guard = FileGuard::new(latest_path);
    let task = "JSON proposal smoke";
    let slugified_path = std::path::Path::new("proposals/proposal_json_proposal_smoke.json");
    let _slugified_guard = FileGuard::new(slugified_path);
    if slugified_path.exists() {
        let _ = std::fs::remove_file(slugified_path);
    }

    let stdout = run(&["--json", "propose", "--provider", "dummy", task]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("propose JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "propose");
    assert_eq!(value["provider"], "dummy");
    assert_eq!(
        value["proposal_file"],
        "proposals/proposal_json_proposal_smoke.json"
    );
    assert_eq!(value["latest_reference"], "proposals/proposal.latest.json");
    assert_eq!(value["operation_count"], 1);
    assert!(slugified_path.exists());
}

#[test]
fn proposals_list_missing_root_returns_empty() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");

    let stdout = run(&["--json", "proposals", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals list JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "proposals list");
    assert_eq!(value["count"], 0);
    assert!(value["proposals"].as_array().unwrap().is_empty());
}

#[test]
fn proposals_list_shows_valid_proposal() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(id)).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals list JSON should parse");
    let proposals = value["proposals"].as_array().unwrap();

    assert_eq!(value["ok"], true);
    assert_eq!(value["count"], 1);
    assert_eq!(proposals[0]["id"], id);
    assert_eq!(
        proposals[0]["path"],
        "proposals/20260613T120000Z-phase-4f-example.json"
    );
    assert_eq!(proposals[0]["valid"], true);
}

#[test]
fn proposals_inspect_latest_reads_proposal_object() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let older_id = "20260613T110000Z-phase-4f-example";
    let latest_id = "20260613T120000Z-phase-4f-example";
    std::fs::write(
        format!("proposals/{older_id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(older_id)).unwrap(),
    )
    .unwrap();
    std::fs::write(
        format!("proposals/{latest_id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(latest_id)).unwrap(),
    )
    .unwrap();

    let stdout = run(&[
        "--json",
        "proposals",
        "inspect",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals inspect JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "proposals inspect");
    assert_eq!(value["id"], latest_id);
    assert_eq!(value["proposal"]["id"], latest_id);
    assert_eq!(value["truncated"], false);
}

#[test]
fn proposals_inspect_latest_flag_id_matches_positional() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(id)).unwrap(),
    )
    .unwrap();

    let positional_stdout = run(&[
        "--json",
        "proposals",
        "inspect",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let flag_stdout = run(&[
        "--json",
        "proposals",
        "inspect",
        "--id",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let positional: serde_json::Value =
        serde_json::from_str(&positional_stdout).expect("positional JSON should parse");
    let flag: serde_json::Value =
        serde_json::from_str(&flag_stdout).expect("flag JSON should parse");

    assert_eq!(positional["id"], flag["id"]);
    assert_eq!(positional["path"], flag["path"]);
}

#[test]
fn proposals_validate_latest_accepts_valid_contract() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(id)).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals validate JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "proposals validate");
    assert_eq!(value["valid"], true);
    assert!(value["errors"].as_array().unwrap().is_empty());
}

#[test]
fn proposals_validate_latest_flag_id_accepts_valid_contract() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&valid_phase_4f_proposal(id)).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "validate", "--id", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals validate JSON should parse");

    assert_eq!(value["id"], id);
    assert_eq!(value["valid"], true);
}

#[test]
fn proposals_validate_missing_required_field_returns_invalid() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    let mut proposal = valid_phase_4f_proposal(id);
    proposal.as_object_mut().unwrap().remove("intent");
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&proposal).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("intent")));
}

#[test]
fn proposals_validate_id_mismatch_returns_invalid() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    let id = "20260613T120000Z-phase-4f-example";
    let mut proposal = valid_phase_4f_proposal(id);
    proposal["id"] = serde_json::json!("20260613T120000Z-other");
    std::fs::write(
        format!("proposals/{id}.json"),
        serde_json::to_string_pretty(&proposal).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("match filename stem")));
}

#[test]
fn proposals_validate_malformed_json_returns_invalid() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    std::fs::create_dir_all("proposals").unwrap();
    std::fs::write(
        "proposals/20260613T120000Z-phase-4f-example.json",
        "{not valid json",
    )
    .unwrap();

    let stdout = run(&["--json", "proposals", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("proposals validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("malformed")));
}

#[test]
fn proposals_reject_path_traversal_id_with_json_error() {
    let _guard = test_lock();
    let _proposal_dir_guard = DirGuard::new("proposals");
    let value = run_fail(&["--json", "proposals", "inspect", "--id", "../outside"]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("invalid proposal id"));
}

#[test]
fn proposals_reject_invalid_max_bytes_with_json_error() {
    let _guard = test_lock();
    let value = run_fail(&[
        "--json",
        "proposals",
        "inspect",
        "latest",
        "--max-bytes",
        "nope",
    ]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("invalid --max-bytes"));
}

#[test]
fn proposals_reject_duplicate_id_with_json_error() {
    let _guard = test_lock();
    let value = run_fail(&[
        "--json",
        "proposals",
        "validate",
        "--id",
        "latest",
        "--id",
        "latest",
    ]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("duplicate --id"));
}

#[test]
fn reviews_list_missing_root_returns_empty() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");

    let stdout = run(&["--json", "reviews", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews list JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "reviews list");
    assert_eq!(value["count"], 0);
    assert!(value["reviews"].as_array().unwrap().is_empty());
}

#[test]
fn reviews_list_shows_valid_review() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(id, "safety-reviewer")).unwrap(),
    )
    .unwrap();
    std::fs::write("reviews/ignored.txt", "ignore me").unwrap();

    let stdout = run(&["--json", "reviews", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews list JSON should parse");
    let reviews = value["reviews"].as_array().unwrap();

    assert_eq!(value["ok"], true);
    assert_eq!(value["count"], 1);
    assert_eq!(reviews[0]["id"], id);
    assert_eq!(
        reviews[0]["path"],
        "reviews/20260613T150000Z-phase-5b-safety.review.json"
    );
    assert_eq!(reviews[0]["role_id"], "safety-reviewer");
    assert_eq!(reviews[0]["target"], "ctxt --json subagents list");
    assert_eq!(reviews[0]["valid"], true);
}

#[test]
fn reviews_inspect_latest_reads_review_object() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let older_id = "20260613T140000Z-phase-5b-docs";
    let latest_id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(
        format!("reviews/{older_id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(older_id, "docs-reviewer")).unwrap(),
    )
    .unwrap();
    std::fs::write(
        format!("reviews/{latest_id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(latest_id, "safety-reviewer")).unwrap(),
    )
    .unwrap();

    let stdout = run(&[
        "--json",
        "reviews",
        "inspect",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews inspect JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "reviews inspect");
    assert_eq!(value["id"], latest_id);
    assert_eq!(value["review"]["id"], latest_id);
    assert_eq!(value["truncated"], false);
}

#[test]
fn reviews_inspect_latest_flag_id_matches_positional() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(id, "safety-reviewer")).unwrap(),
    )
    .unwrap();

    let positional_stdout = run(&[
        "--json",
        "reviews",
        "inspect",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let flag_stdout = run(&[
        "--json",
        "reviews",
        "inspect",
        "--id",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let positional: serde_json::Value =
        serde_json::from_str(&positional_stdout).expect("positional JSON should parse");
    let flag: serde_json::Value =
        serde_json::from_str(&flag_stdout).expect("flag JSON should parse");

    assert_eq!(positional["id"], flag["id"]);
    assert_eq!(positional["path"], flag["path"]);
}

#[test]
fn reviews_validate_latest_accepts_valid_contract() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(id, "safety-reviewer")).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "reviews validate");
    assert_eq!(value["valid"], true);
    assert!(value["errors"].as_array().unwrap().is_empty());
}

#[test]
fn reviews_validate_latest_flag_id_accepts_valid_contract() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&valid_phase_5b_review(id, "safety-reviewer")).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "--id", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["id"], id);
    assert_eq!(value["valid"], true);
}

#[test]
fn reviews_validate_missing_required_field_returns_invalid() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    let mut review = valid_phase_5b_review(id, "safety-reviewer");
    review.as_object_mut().unwrap().remove("target");
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&review).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("target")));
}

#[test]
fn reviews_validate_id_mismatch_returns_invalid() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    let mut review = valid_phase_5b_review(id, "safety-reviewer");
    review["id"] = serde_json::json!("20260613T150000Z-other");
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&review).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("filename-derived id")));
}

#[test]
fn reviews_validate_malformed_json_returns_invalid_and_listable() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    std::fs::write(format!("reviews/{id}.review.json"), "{not valid json").unwrap();

    let list_stdout = run(&["--json", "reviews", "list"]);
    let list_value: serde_json::Value =
        serde_json::from_str(&list_stdout).expect("reviews list JSON should parse");
    assert_eq!(list_value["reviews"][0]["valid"], false);

    let validate_stdout = run(&["--json", "reviews", "validate", "latest"]);
    let validate_value: serde_json::Value =
        serde_json::from_str(&validate_stdout).expect("reviews validate JSON should parse");
    assert_eq!(validate_value["valid"], false);
    assert!(validate_value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("malformed")));
}

#[test]
fn reviews_reject_path_traversal_id_with_json_error() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    let value = run_fail(&["--json", "reviews", "inspect", "--id", "../outside"]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("invalid review id"));
}

#[test]
fn reviews_reject_invalid_max_bytes_with_json_error() {
    let _guard = test_lock();
    let value = run_fail(&[
        "--json",
        "reviews",
        "inspect",
        "latest",
        "--max-bytes",
        "nope",
    ]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("invalid --max-bytes"));
}

#[test]
fn reviews_reject_duplicate_id_with_json_error() {
    let _guard = test_lock();
    let value = run_fail(&[
        "--json", "reviews", "validate", "--id", "latest", "--id", "latest",
    ]);

    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("duplicate --id"));
}

#[test]
fn reviews_validate_true_safety_flag_returns_invalid() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    let mut review = valid_phase_5b_review(id, "safety-reviewer");
    review["safety_flags"]["network_used"] = serde_json::json!(true);
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&review).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("network_used")));
}

#[test]
fn reviews_validate_invalid_role_id_returns_invalid() {
    let _guard = test_lock();
    let _review_dir_guard = DirGuard::new("reviews");
    std::fs::create_dir_all("reviews").unwrap();
    let id = "20260613T150000Z-phase-5b-safety";
    let review = valid_phase_5b_review(id, "unknown-reviewer");
    std::fs::write(
        format!("reviews/{id}.review.json"),
        serde_json::to_string_pretty(&review).unwrap(),
    )
    .unwrap();

    let stdout = run(&["--json", "reviews", "validate", "latest"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("reviews validate JSON should parse");

    assert_eq!(value["valid"], false);
    assert!(value["errors"]
        .as_array()
        .unwrap()
        .iter()
        .any(|error| error.as_str().unwrap().contains("role_id")));
}

#[test]
fn reviews_unknown_commands_fail_with_json_errors() {
    let _guard = test_lock();
    let cases = [
        vec!["--json", "reviews"],
        vec!["--json", "reviews", "inspect"],
        vec!["--json", "reviews", "validate"],
        vec!["--json", "reviews", "run"],
        vec!["--json", "reviews", "generate"],
        vec!["--json", "reviews", "apply"],
        vec!["--json", "reviews", "list", "extra"],
        vec!["--json", "reviews", "unknown"],
    ];

    for args in cases {
        let value = run_fail(&args);
        assert_eq!(value["ok"], false);
        assert!(value["error"]["message"].is_string());
    }
}

#[test]
fn validate_json_lists_standard_commands() {
    let _guard = test_lock();
    let stdout = run(&["--json", "validate"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("validate JSON should parse");
    let commands = value["validation_commands"]
        .as_array()
        .expect("validation_commands should be an array");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "validate");
    assert!(commands.iter().any(|cmd| cmd == "cargo test"));
    assert!(commands
        .iter()
        .any(|cmd| cmd == "cargo clippy -- -D warnings"));
}

#[test]
fn validate_run_executes_validation_commands() {
    let _guard = test_lock();
    let output = Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "validate", "--run"])
        .env("CTXT_VALIDATE_COMMANDS_FOR_TEST", "rustc --version")
        .output()
        .expect("ctxt binary should run");

    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).expect("stdout should be UTF-8");
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("validate --run JSON should parse");
    let steps = value["steps"].as_array().expect("steps should be an array");
    let first_step = steps.first().expect("steps should not be empty");

    assert_eq!(value["command"], "validate");
    assert_eq!(value["ok"], true);
    assert_eq!(value["run"], true);
    assert!(!steps.is_empty());
    assert!(first_step.get("cmd").is_some());
    assert!(first_step["cmd"]
        .as_str()
        .expect("cmd should be a string")
        .contains("rustc --version"));
    assert_eq!(first_step["ok"], true);
    assert_eq!(first_step["exit_code"], 0);
    assert!(first_step.get("stdout_excerpt").is_some());
    assert!(first_step.get("stderr_excerpt").is_some());
}

#[test]
fn capabilities_json_reports_phase_four_b_introspection() {
    let _guard = test_lock();
    let stdout = run(&["--json", "capabilities"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("capabilities JSON should parse");
    let phases = value["phases"]
        .as_array()
        .expect("phases should be an array");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "capabilities");
    assert_eq!(value["schema_version"], "0.1");
    assert!(phases
        .iter()
        .any(|phase| { phase["phase"] == "4b" && phase["name"] == "agent-friendly CLI polish" }));
    assert!(phases
        .iter()
        .any(|phase| { phase["phase"] == "4h" && phase["name"] == "proposal capabilities" }));
    assert!(phases.iter().any(|phase| {
        phase["phase"] == "5a" && phase["name"] == "deterministic subagent role contract"
    }));
    assert!(phases.iter().any(|phase| {
        phase["phase"] == "5b" && phase["name"] == "deterministic review artifact contract"
    }));
    assert!(phases.iter().any(|phase| {
        phase["phase"] == "5c" && phase["name"] == "deterministic startup review flow contract"
    }));
    assert!(phases.iter().any(|phase| {
        phase["phase"] == "5d" && phase["name"] == "deterministic startup readiness contract"
    }));
    assert!(phases.iter().any(|phase| {
        phase["phase"] == "5e" && phase["name"] == "deterministic review workflow contract"
    }));
    assert_eq!(value["features"]["real_external_execution"], false);
    assert_eq!(value["features"]["network_gate"], false);
    assert_eq!(value["features"]["apply_gate"], false);
}

#[test]
fn capabilities_json_reports_proposal_capabilities() {
    let _guard = test_lock();
    let stdout = run(&["--json", "capabilities"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("capabilities JSON should parse");
    let features = &value["features"];
    let commands = value["commands"]
        .as_array()
        .expect("commands should be an array");

    assert_eq!(features["proposals_list"], true);
    assert_eq!(features["proposals_inspect"], true);
    assert_eq!(features["proposals_validate"], true);
    assert_eq!(features["proposal_artifact_contract"], true);
    assert_eq!(features["subagent_role_contract"], true);
    assert_eq!(features["subagent_execution"], false);
    assert_eq!(features["subagent_runtime_orchestration"], false);
    assert_eq!(features["reviews_list"], true);
    assert_eq!(features["reviews_inspect"], true);
    assert_eq!(features["reviews_validate"], true);
    assert_eq!(features["review_artifact_contract"], true);
    assert_eq!(features["startup_flow_contract"], true);
    assert_eq!(features["startup_flow_execution"], false);
    assert_eq!(features["startup_readiness_contract"], true);
    assert_eq!(features["startup_readiness_execution"], false);
    assert_eq!(features["ready_for_review_workflow"], true);
    assert_eq!(features["ready_for_external_execution"], false);
    assert_eq!(features["review_workflow_contract"], true);
    assert_eq!(features["review_workflow_execution"], false);
    assert_eq!(features["review_workflow_apply"], false);
    assert_eq!(features["review_generation"], false);
    assert_eq!(features["review_apply"], false);
    assert_eq!(features["proposal_apply"], false);
    assert_eq!(features["proposal_generation"], false);

    for command_name in [
        "proposals list",
        "proposals inspect",
        "proposals validate",
        "reviews list",
        "reviews inspect",
        "reviews validate",
        "startup flow",
        "startup readiness",
        "review workflow",
    ] {
        let command = commands
            .iter()
            .find(|command| command["name"] == command_name)
            .unwrap_or_else(|| panic!("missing capabilities command entry for {command_name}"));

        assert_eq!(command["json"], true);
        assert_eq!(command["side_effects"], false);
        assert_eq!(command["read_only"], true);
        assert_eq!(command["network_used"], false);
        assert_eq!(command["external_agent_invoked"], false);
        assert_eq!(command["apply_performed"], false);
    }

    let subagents_command = commands
        .iter()
        .find(|command| command["name"] == "subagents list")
        .expect("missing capabilities command entry for subagents list");
    assert_eq!(subagents_command["json"], true);
    assert_eq!(subagents_command["side_effects"], false);
    assert_eq!(subagents_command["read_only"], true);
    assert_eq!(subagents_command["network_used"], false);
    assert_eq!(subagents_command["external_agent_invoked"], false);
    assert_eq!(subagents_command["apply_performed"], false);
}

#[test]
fn review_workflow_json_reports_static_contract() {
    let _guard = test_lock();
    let stdout = run(&["--json", "review", "workflow"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("review workflow JSON should parse");
    let steps = value["workflow_steps"]
        .as_array()
        .expect("workflow_steps should be an array");
    let expected_steps = [
        ("startup-readiness", "ctxt --json startup readiness"),
        ("startup-flow", "ctxt --json startup flow"),
        ("inspect-schema", "ctxt --json schema"),
        ("inspect-capabilities", "ctxt --json capabilities"),
        ("inspect-subagent-roles", "ctxt --json subagents list"),
        ("list-proposals", "ctxt --json proposals list"),
        (
            "validate-target-proposal",
            "ctxt --json proposals validate latest",
        ),
        ("list-reviews", "ctxt --json reviews list"),
        (
            "validate-target-review",
            "ctxt --json reviews validate latest",
        ),
        ("run-local-validation", "ctxt --json validate --run"),
        ("summarize-findings-for-user", "user-facing summary only"),
    ];

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "review workflow");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["execution_supported"], false);
    assert_eq!(value["workflow_kind"], "deterministic-review");
    assert_eq!(steps.len(), expected_steps.len());

    for (index, (expected_id, expected_command)) in expected_steps.iter().enumerate() {
        let step = &steps[index];
        assert_eq!(step["order"].as_u64().unwrap(), (index + 1) as u64);
        assert_eq!(step["id"], *expected_id);
        assert_eq!(step["command"], *expected_command);
        assert!(step["purpose"].as_str().unwrap().len() > 0);
        assert_eq!(step["required"], true);
        assert_eq!(step["executes"], false);
        assert_eq!(step["applies_changes"], false);
    }

    for contract in [
        "startup_readiness",
        "startup_flow",
        "subagent_roles",
        "proposal_artifacts",
        "review_artifacts",
        "validation_runner",
        "schema",
        "capabilities",
        "self_report",
    ] {
        assert_eq!(
            value["required_contracts"][contract], true,
            "required contract {contract}"
        );
    }

    for role in [
        "schema-reviewer",
        "capabilities-reviewer",
        "proposal-reviewer",
        "test-reviewer",
        "docs-reviewer",
        "safety-reviewer",
    ] {
        assert!(value["required_roles"]
            .as_array()
            .unwrap()
            .iter()
            .any(|candidate| candidate == role));
    }

    for action in [
        "network",
        "providers",
        "external_agent_invocation",
        "proposal_apply",
        "review_apply",
        "git_write",
        "mcp_server",
        "hooks",
        "plugins",
    ] {
        assert!(value["forbidden_actions"]
            .as_array()
            .unwrap()
            .iter()
            .any(|candidate| candidate == action));
    }

    for flag in [
        "workflow_executed",
        "network_used",
        "external_agents_invoked",
        "subagents_executed",
        "apply_performed",
        "git_write_performed",
        "artifacts_read",
        "artifacts_written",
    ] {
        assert_eq!(value["safety"][flag], false, "safety flag {flag}");
    }
}

#[test]
fn review_workflow_unknown_commands_fail_with_json_errors() {
    let _guard = test_lock();
    let cases = [
        vec!["--json", "review"],
        vec!["--json", "review", "run"],
        vec!["--json", "review", "execute"],
        vec!["--json", "review", "workflow", "extra"],
        vec!["--json", "review", "unknown"],
    ];

    for args in cases {
        let value = run_fail(&args);
        assert_eq!(value["ok"], false);
        assert!(value["error"]["message"].is_string());
    }
}

#[test]
fn startup_readiness_json_reports_static_readiness() {
    let _guard = test_lock();
    let stdout = run(&["--json", "startup", "readiness"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("startup readiness JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "startup readiness");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["ready_for_review_workflow"], true);
    assert_eq!(value["ready_for_external_execution"], false);

    for field in [
        "self_report",
        "schema",
        "capabilities",
        "subagents",
        "proposals",
        "reviews",
        "startup_flow",
        "review_workflow",
        "validation_runner",
    ] {
        assert_eq!(value["contracts"][field], true, "contract {field}");
    }

    for field in [
        "network",
        "external_agents",
        "provider_calls",
        "proposal_apply",
        "review_apply",
        "subagent_execution",
        "git_write",
        "mcp_server",
        "hooks",
        "plugins",
    ] {
        assert_eq!(
            value["disabled_gates"][field], true,
            "disabled gate {field}"
        );
    }

    let expected_next = [
        "ctxt --json startup flow",
        "ctxt --json self report",
        "ctxt --json schema",
        "ctxt --json capabilities",
        "ctxt --json subagents list",
        "ctxt --json proposals list",
        "ctxt --json reviews list",
        "ctxt --json review workflow",
        "ctxt --json validate --run",
    ];
    let recommended_next = value["recommended_next_commands"]
        .as_array()
        .expect("recommended_next_commands should be an array");
    assert_eq!(recommended_next.len(), expected_next.len());
    for (index, expected) in expected_next.iter().enumerate() {
        assert_eq!(recommended_next[index], *expected);
    }

    assert_eq!(value["safety"]["readiness_executed_commands"], false);
    assert_eq!(value["safety"]["network_used"], false);
    assert_eq!(value["safety"]["external_agents_invoked"], false);
    assert_eq!(value["safety"]["subagents_executed"], false);
    assert_eq!(value["safety"]["apply_performed"], false);
    assert_eq!(value["safety"]["git_write_performed"], false);
}

#[test]
fn startup_flow_json_reports_static_sequence() {
    let _guard = test_lock();
    let stdout = run(&["--json", "startup", "flow"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("startup flow JSON should parse");
    let sequence = value["recommended_sequence"]
        .as_array()
        .expect("recommended_sequence should be an array");
    let expected_commands = [
        "ctxt --json startup readiness",
        "ctxt --json self report",
        "ctxt --json schema",
        "ctxt --json capabilities",
        "ctxt --json subagents list",
        "ctxt --json proposals list",
        "ctxt --json reviews list",
        "ctxt --json review workflow",
        "ctxt --json validate --run",
    ];

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "startup flow");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["execution_supported"], false);
    assert_eq!(sequence.len(), expected_commands.len());

    for (index, expected_command) in expected_commands.iter().enumerate() {
        let item = &sequence[index];
        assert_eq!(item["order"].as_u64().unwrap(), (index + 1) as u64);
        assert_eq!(item["command"], *expected_command);
        assert!(item["purpose"].as_str().unwrap().len() > 0);
        assert_eq!(item["required"], true);
        assert_eq!(item["executes"], false);
    }

    assert_eq!(value["safety"]["flow_executed"], false);
    assert_eq!(value["safety"]["network_used"], false);
    assert_eq!(value["safety"]["external_agents_invoked"], false);
    assert_eq!(value["safety"]["subagents_executed"], false);
    assert_eq!(value["safety"]["apply_performed"], false);
    assert_eq!(value["safety"]["git_write_performed"], false);
}

#[test]
fn startup_unknown_commands_fail_with_json_errors() {
    let _guard = test_lock();
    let cases = [
        vec!["--json", "startup"],
        vec!["--json", "startup", "run"],
        vec!["--json", "startup", "execute"],
        vec!["--json", "startup", "flow", "extra"],
        vec!["--json", "startup", "readiness", "extra"],
        vec!["--json", "startup", "ready"],
        vec!["--json", "startup", "status"],
        vec!["--json", "startup", "unknown"],
    ];

    for args in cases {
        let value = run_fail(&args);
        assert_eq!(value["ok"], false);
        assert!(value["error"]["message"].is_string());
    }
}

#[test]
fn schema_json_reports_stable_contracts() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "schema");
    assert_eq!(value["schema_version"], "0.1");
    for command in [
        "capabilities",
        "runs list",
        "runs read",
        "proposals list",
        "proposals inspect",
        "proposals validate",
        "proposal.v1 artifact",
        "subagents list",
        "startup flow",
        "startup readiness",
        "review workflow",
        "reviews list",
        "reviews inspect",
        "reviews validate",
        "review.v1 artifact",
        "agent discover",
        "agent run --allow-external --proposal-only",
        "validate",
    ] {
        assert!(contracts
            .iter()
            .any(|contract| contract["command"] == command));
    }
    assert_eq!(value["safety"]["read_only"], true);
    assert_eq!(value["safety"]["network_used"], false);
    assert_eq!(value["safety"]["external_agent_invoked"], false);
    assert_eq!(value["safety"]["apply_performed"], false);
}

#[test]
fn schema_json_reports_startup_flow_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");
    let contract = contracts
        .iter()
        .find(|contract| contract["command"] == "startup flow")
        .expect("startup flow contract should exist");

    assert_eq!(contract["status"], "stable");
    for note in [
        "read-only",
        "static contract",
        "does not execute flow",
        "no external agents",
        "no network",
        "no apply",
    ] {
        assert!(contract["notes"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == note));
    }
    for field in [
        "ok",
        "command",
        "schema_version",
        "execution_supported",
        "recommended_sequence",
        "safety",
    ] {
        assert!(contract["required_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
    for field in ["order", "command", "purpose", "required", "executes"] {
        assert!(contract["sequence_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
}

#[test]
fn schema_json_reports_startup_readiness_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");
    let contract = contracts
        .iter()
        .find(|contract| contract["command"] == "startup readiness")
        .expect("startup readiness contract should exist");

    assert_eq!(contract["status"], "stable");
    for note in [
        "read-only",
        "static contract",
        "does not execute commands",
        "review workflow readiness only",
        "external execution disabled",
        "no external agents",
        "no network",
        "no apply",
    ] {
        assert!(contract["notes"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == note));
    }
    for field in [
        "ok",
        "command",
        "schema_version",
        "ready_for_review_workflow",
        "ready_for_external_execution",
        "contracts",
        "disabled_gates",
        "recommended_next_commands",
        "safety",
    ] {
        assert!(contract["required_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
    for field in [
        "self_report",
        "schema",
        "capabilities",
        "subagents",
        "proposals",
        "reviews",
        "startup_flow",
        "validation_runner",
    ] {
        assert!(contract["contract_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
    for field in [
        "network",
        "external_agents",
        "provider_calls",
        "proposal_apply",
        "review_apply",
        "subagent_execution",
        "git_write",
        "mcp_server",
        "hooks",
        "plugins",
    ] {
        assert!(contract["disabled_gate_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
}

#[test]
fn schema_json_reports_review_workflow_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");
    let contract = contracts
        .iter()
        .find(|contract| contract["command"] == "review workflow")
        .expect("review workflow contract should exist");

    assert_eq!(contract["status"], "stable");
    for note in [
        "read-only",
        "static contract",
        "does not execute workflow",
        "review workflow contract only",
        "no external agents",
        "no network",
        "no apply",
        "no artifact reads",
    ] {
        assert!(contract["notes"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == note));
    }
    for field in [
        "ok",
        "command",
        "schema_version",
        "execution_supported",
        "workflow_kind",
        "required_contracts",
        "workflow_steps",
        "required_roles",
        "evidence_inputs",
        "forbidden_actions",
        "safety",
    ] {
        assert!(contract["required_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
    for field in [
        "order",
        "id",
        "command",
        "purpose",
        "required",
        "executes",
        "applies_changes",
    ] {
        assert!(contract["workflow_step_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
}

#[test]
fn schema_json_reports_subagent_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");
    let contract = contracts
        .iter()
        .find(|contract| contract["command"] == "subagents list")
        .expect("subagents list contract should exist");

    assert_eq!(contract["status"], "stable");
    for note in [
        "read-only",
        "static contract",
        "no runtime execution",
        "no external agents",
        "no network",
        "no apply",
    ] {
        assert!(contract["notes"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == note));
    }
    for field in [
        "ok",
        "command",
        "schema_version",
        "execution_supported",
        "roles",
        "safety",
    ] {
        assert!(contract["required_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
    for field in [
        "id",
        "name",
        "mode",
        "allowed_outputs",
        "may_edit_files",
        "may_run_commands",
        "forbidden",
    ] {
        assert!(contract["role_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == field));
    }
}

#[test]
fn schema_json_reports_review_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");
    let contract_for = |command: &str| -> &serde_json::Value {
        contracts
            .iter()
            .find(|contract| contract["command"] == command)
            .unwrap_or_else(|| panic!("missing schema contract for {command}"))
    };

    for command in ["reviews list", "reviews inspect", "reviews validate"] {
        let notes = contract_for(command)["notes"]
            .as_array()
            .expect("review command notes should be an array");
        for expected_note in [
            "read-only",
            "no apply",
            "no subagent execution",
            "no network",
            "no external agents",
        ] {
            assert!(
                notes.iter().any(|note| note == expected_note),
                "{command} should include safety note {expected_note}"
            );
        }
    }

    let artifact = contract_for("review.v1 artifact");
    let required_fields = artifact["required_fields"]
        .as_array()
        .expect("review artifact required_fields should be an array");
    for field in [
        "schema_version",
        "id",
        "role_id",
        "findings",
        "risks",
        "recommendations",
        "validation_refs",
        "safety_flags",
        "status",
    ] {
        assert!(
            required_fields.iter().any(|required| required == field),
            "review.v1 artifact should require {field}"
        );
    }
    assert!(artifact["notes"]
        .as_array()
        .unwrap()
        .iter()
        .any(|note| note == "untrusted input"));
    assert!(artifact["enums"]["role_id"]
        .as_array()
        .unwrap()
        .iter()
        .any(|value| value == "safety-reviewer"));
    assert!(artifact["safety_flag_fields"]
        .as_array()
        .unwrap()
        .iter()
        .any(|value| value == "secrets_accessed"));
}

#[test]
fn schema_json_reports_proposal_contract_details() {
    let _guard = test_lock();
    let stdout = run(&["--json", "schema"]);
    let value: serde_json::Value = serde_json::from_str(&stdout).expect("schema JSON should parse");
    let contracts = value["contracts"]
        .as_array()
        .expect("contracts should be an array");

    let contract_for = |command: &str| -> &serde_json::Value {
        contracts
            .iter()
            .find(|contract| contract["command"] == command)
            .unwrap_or_else(|| panic!("missing schema contract for {command}"))
    };

    for command in ["proposals list", "proposals inspect", "proposals validate"] {
        let notes = contract_for(command)["notes"]
            .as_array()
            .expect("proposal command notes should be an array");
        for expected_note in ["no apply", "no network", "no external agents"] {
            assert!(
                notes.iter().any(|note| note == expected_note),
                "{command} should include safety note {expected_note}"
            );
        }
    }

    let artifact = contract_for("proposal.v1 artifact");
    let required_fields = artifact["required_fields"]
        .as_array()
        .expect("proposal artifact required_fields should be an array");
    for field in [
        "schema_version",
        "id",
        "changes",
        "validation",
        "network",
        "status",
    ] {
        assert!(
            required_fields.iter().any(|required| required == field),
            "proposal.v1 artifact should require {field}"
        );
    }

    assert!(artifact["notes"]
        .as_array()
        .unwrap()
        .iter()
        .any(|note| note == "untrusted input"));
    assert!(artifact["enums"]["network"]
        .as_array()
        .unwrap()
        .iter()
        .any(|value| value == "offline-only"));
    assert!(artifact["enums"]["status"]
        .as_array()
        .unwrap()
        .iter()
        .any(|value| value == "approved-for-apply"));
    assert!(artifact["enums"]["action"]
        .as_array()
        .unwrap()
        .iter()
        .any(|value| value == "document"));
}

#[test]
fn schema_unexpected_arg_fails_with_json_error() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "schema", "unexpected"])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value = serde_json::from_str(&stderr).expect("error JSON should parse");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("unexpected argument"));
}

#[test]
fn self_report_json_reports_runtime_baseline() {
    let _guard = test_lock();
    let stdout = run(&["--json", "self", "report"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("self report JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "self report");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["runtime"]["name"], "ctxt");
    assert_eq!(value["runtime"]["phase"], "4e");
    assert_eq!(value["validation"]["last_known_unit_tests"], 37);
    assert_eq!(value["validation"]["last_known_smoke_tests"], 39);
    assert_eq!(value["agent_policy"]["external_execution"], false);
    assert_eq!(value["agent_policy"]["subagent_execution"], false);
    assert_eq!(value["agent_policy"]["subagent_roles_contract_only"], true);
    assert_eq!(value["agent_policy"]["review_generation"], false);
    assert_eq!(value["agent_policy"]["review_apply"], false);
    assert_eq!(
        value["agent_policy"]["review_artifacts_contract_only"],
        true
    );
    assert_eq!(value["agent_policy"]["startup_flow_execution"], false);
    assert_eq!(value["agent_policy"]["startup_flow_contract_only"], true);
    assert_eq!(value["agent_policy"]["startup_readiness_execution"], false);
    assert_eq!(
        value["agent_policy"]["startup_readiness_contract_only"],
        true
    );
    assert_eq!(value["agent_policy"]["ready_for_review_workflow"], true);
    assert_eq!(value["agent_policy"]["ready_for_external_execution"], false);
    assert_eq!(value["agent_policy"]["review_workflow_execution"], false);
    assert_eq!(value["agent_policy"]["review_workflow_contract_only"], true);
    assert_eq!(value["agent_policy"]["review_workflow_apply"], false);
    assert_eq!(value["agent_policy"]["network_default"], "deny");
    assert_eq!(value["agent_policy"]["apply_automatic"], false);
    assert!(value["safe_entrypoints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "ctxt --json subagents list"));
    assert!(value["safe_entrypoints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "ctxt --json startup readiness"));
    assert!(value["safe_entrypoints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "ctxt --json review workflow"));
    assert!(value["safe_entrypoints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry == "ctxt --json startup flow"));
    for entry in [
        "ctxt --json reviews list",
        "ctxt --json reviews inspect latest --max-bytes 12000",
        "ctxt --json reviews validate latest",
    ] {
        assert!(value["safe_entrypoints"]
            .as_array()
            .unwrap()
            .iter()
            .any(|candidate| candidate == entry));
    }
}

#[test]
fn subagents_list_json_reports_contract_only_roles() {
    let _guard = test_lock();
    let stdout = run(&["--json", "subagents", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("subagents list JSON should parse");
    let roles = value["roles"].as_array().expect("roles should be an array");
    let required_ids = [
        "schema-reviewer",
        "capabilities-reviewer",
        "proposal-reviewer",
        "test-reviewer",
        "docs-reviewer",
        "safety-reviewer",
    ];

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "subagents list");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["execution_supported"], false);
    for id in required_ids {
        assert!(roles.iter().any(|role| role["id"] == id), "missing {id}");
    }

    for role in roles {
        assert_eq!(role["mode"], "contract-only");
        assert_eq!(role["may_edit_files"], false);
        assert_eq!(role["may_run_commands"], false);
        for output in ["finding", "risk", "recommendation"] {
            assert!(role["allowed_outputs"]
                .as_array()
                .unwrap()
                .iter()
                .any(|value| value == output));
        }
        for forbidden in [
            "network",
            "providers",
            "external_agent_invocation",
            "proposal_apply",
            "git_write",
            "runtime_execution",
        ] {
            assert!(role["forbidden"]
                .as_array()
                .unwrap()
                .iter()
                .any(|value| value == forbidden));
        }
    }

    assert_eq!(value["safety"]["subagents_executed"], false);
    assert_eq!(value["safety"]["external_agents_invoked"], false);
    assert_eq!(value["safety"]["network_used"], false);
    assert_eq!(value["safety"]["apply_performed"], false);
    assert_eq!(value["safety"]["git_write_performed"], false);
}

#[test]
fn subagent_unknown_commands_fail_with_json_errors() {
    let _guard = test_lock();
    let cases = [
        vec!["--json", "subagents"],
        vec!["--json", "subagents", "run"],
        vec!["--json", "subagents", "execute"],
        vec!["--json", "subagents", "list", "extra"],
        vec!["--json", "subagents", "unknown"],
    ];

    for args in cases {
        let value = run_fail(&args);
        assert_eq!(value["ok"], false);
        assert!(value["error"]["message"].is_string());
    }
}

#[test]
fn self_without_report_fails_with_json_error() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "self"])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value = serde_json::from_str(&stderr).expect("error JSON should parse");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("missing subcommand"));
}

#[test]
fn self_report_extra_arg_fails_with_json_error() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "self", "report", "extra"])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value = serde_json::from_str(&stderr).expect("error JSON should parse");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("unexpected argument"));
}

#[test]
fn agent_list_json_reports_phase_one_agents() {
    let _guard = test_lock();
    let stdout = run(&["--json", "agent", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent list JSON should parse");
    let agents = value["agents"]
        .as_array()
        .expect("agents should be an array");

    assert_eq!(value["command"], "agent list");
    assert_eq!(value["ok"], true);
    assert!(agents
        .iter()
        .any(|agent| agent["kind"] == "dummy" && agent["status"] == "available"));
    assert!(agents
        .iter()
        .any(|agent| agent["kind"] == "codex" && agent["status"] == "dry-run-only"));
    assert!(agents
        .iter()
        .any(|agent| agent["kind"] == "antigravity" && agent["status"] == "dry-run-only"));
}

#[test]
fn agent_discover_json_lists_supported_targets() {
    let _guard = test_lock();
    let stdout = run(&["--json", "agent", "discover"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent discover JSON should parse");
    let targets = value["targets"]
        .as_array()
        .expect("targets should be an array");

    assert_eq!(value["command"], "agent discover");
    assert_eq!(value["ok"], true);
    assert!(targets.iter().any(|target| target == "codex"));
    assert!(targets.iter().any(|target| target == "antigravity"));
    assert_eq!(value["external_agent_invoked"], false);
    assert_eq!(value["network_used"], false);
}

fn assert_agent_discovery_shape(value: &serde_json::Value, kind: &str) {
    assert_eq!(value["command"], "agent discover");
    assert_eq!(value["kind"], kind);
    assert_eq!(value["ok"], true);
    assert_eq!(value["version"], serde_json::Value::Null);
    assert_eq!(value["external_agent_invoked"], false);
    assert_eq!(value["network_used"], false);

    let discovered = value["discovered"]
        .as_bool()
        .expect("discovered should be a bool");
    let path_is_string = value["path"].is_string();
    assert_eq!(discovered, path_is_string);
    assert!(value["path"].is_null() || path_is_string);
    assert!(value["notes"].is_array());
}

#[test]
fn agent_discover_codex_json_reports_path_metadata_only() {
    let _guard = test_lock();
    let stdout = run(&["--json", "agent", "discover", "--kind", "codex"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent discover codex JSON should parse");

    assert_agent_discovery_shape(&value, "codex");
}

#[test]
fn agent_discover_antigravity_json_reports_path_metadata_only() {
    let _guard = test_lock();
    let stdout = run(&["--json", "agent", "discover", "--kind", "antigravity"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent discover antigravity JSON should parse");

    assert_agent_discovery_shape(&value, "antigravity");
}

#[test]
fn agent_discover_unknown_kind_fails_with_json_error() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["--json", "agent", "discover", "--kind", "unknown"])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value = serde_json::from_str(&stderr).expect("error JSON should parse");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("unsupported agent discovery kind"));
}

#[test]
fn runs_list_json_reports_latest_reference() {
    let _guard = test_lock();
    let stdout = run(&["--json", "runs", "list"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("runs list JSON should parse");
    let runs = value["runs"].as_array().expect("runs should be an array");
    let latest = runs.first().expect("latest run reference should exist");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "runs list");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(latest["id"], "latest");
    assert_eq!(latest["path"], ".comptext/runs/latest/run.json");
    assert!(latest["exists"].is_boolean());
}

#[test]
fn runs_read_latest_positional_reads_bounded_runtime_artifact() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);
    run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "codex",
        "--task",
        "Prepare Codex execution plan",
        "--allow-external",
        "--proposal-only",
    ]);

    let stdout = run(&["--json", "runs", "read", "latest", "--max-bytes", "12000"]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("runs read JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "runs read");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["id"], "latest");
    assert_eq!(value["path"], ".comptext/runs/latest/run.json");
    assert_eq!(value["max_bytes"], 12000);
    assert!(value["content"]
        .as_str()
        .unwrap()
        .contains("execution-plan-only"));
}

#[test]
fn runs_read_latest_flag_id_reads_bounded_runtime_artifact() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);
    run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "codex",
        "--task",
        "Prepare Codex execution plan",
        "--allow-external",
        "--proposal-only",
    ]);

    let stdout = run(&[
        "--json",
        "runs",
        "read",
        "--id",
        "latest",
        "--max-bytes",
        "12000",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("runs read JSON should parse");

    assert_eq!(value["ok"], true);
    assert_eq!(value["command"], "runs read");
    assert_eq!(value["schema_version"], "0.1");
    assert_eq!(value["id"], "latest");
    assert_eq!(value["path"], ".comptext/runs/latest/run.json");
}

#[test]
fn runs_read_errors_are_machine_readable() {
    let _guard = test_lock();
    let cases = vec![
        vec!["--json", "runs", "read", "unknown"],
        vec!["--json", "runs", "read", "latest", "--max-bytes", "nope"],
        vec!["--json", "runs", "read", "--id", "latest", "--id", "latest"],
        vec!["--json", "runs", "read", "latest", "extra"],
    ];
    for args in cases {
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
            .args(&args)
            .output()
            .expect("ctxt binary should run");

        assert!(!output.status.success(), "command should fail: {args:?}");
        let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
        let value: serde_json::Value =
            serde_json::from_str(&stderr).expect("error JSON should parse");
        assert_eq!(value["ok"], false);
        assert!(value["error"]["message"].is_string());
    }
}

#[test]
fn agent_run_dummy_writes_run_artifact() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let context_path = std::path::Path::new(".comptext/context_pack.latest.json");
    let _run_guard = FileGuard::new(run_path);
    let _context_guard = FileGuard::new(context_path);

    let stdout = run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "dummy",
        "--task",
        "Agent dummy smoke",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent run JSON should parse");

    assert_eq!(value["command"], "agent run");
    assert_eq!(value["kind"], "dummy");
    assert_eq!(value["task"], "Agent dummy smoke");
    assert_eq!(value["external_execution"], false);
    assert_eq!(value["dry_run"], false);
    assert_eq!(value["ok"], true);
    assert_eq!(value["run_artifact"], ".comptext/runs/latest/run.json");
    assert!(run_path.exists());

    let artifact: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(run_path).unwrap())
            .expect("run artifact should parse");
    assert_eq!(artifact["schema_version"], "0.1");
    assert_eq!(artifact["task"], "Agent dummy smoke");
    assert_eq!(artifact["agent_kind"], "dummy");
    assert_eq!(
        artifact["context_pack"],
        ".comptext/context_pack.latest.json"
    );
    assert_eq!(artifact["network_default"], "deny");
    assert_eq!(artifact["proposal_required"], true);
    assert!(artifact["timestamp"]
        .as_str()
        .unwrap()
        .parse::<u64>()
        .is_ok());
}

#[test]
fn agent_run_codex_is_dry_run_by_default() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);

    let stdout = run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "codex",
        "--task",
        "Codex dry run smoke",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent run JSON should parse");

    assert_eq!(value["kind"], "codex");
    assert_eq!(value["external_execution"], false);
    assert_eq!(value["dry_run"], true);
    assert_eq!(value["ok"], true);
    assert!(value["would_run"].as_str().unwrap().contains("codex"));
}

#[test]
fn agent_run_antigravity_is_dry_run_by_default() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);

    let stdout = run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "antigravity",
        "--task",
        "Antigravity dry run smoke",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent run JSON should parse");

    assert_eq!(value["kind"], "antigravity");
    assert_eq!(value["external_execution"], false);
    assert_eq!(value["dry_run"], true);
    assert_eq!(value["ok"], true);
    assert!(value["would_run"].as_str().unwrap().contains("antigravity"));
}

#[test]
fn agent_run_codex_allow_external_proposal_only_returns_execution_plan() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);

    let stdout = run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "codex",
        "--task",
        "Codex execution plan smoke",
        "--allow-external",
        "--proposal-only",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent run JSON should parse");
    assert_eq!(value["kind"], "codex");
    assert_eq!(value["external_execution"], false);
    assert_eq!(value["dry_run"], false);
    assert_eq!(value["allow_external"], true);
    assert_eq!(value["proposal_only"], true);
    assert_eq!(value["ok"], true);
    assert_eq!(value["status"], "execution-plan-only");
    assert_eq!(value["execution_plan"]["agent_kind"], "codex");
    assert_eq!(value["execution_plan"]["mode"], "proposal-only");
    assert_eq!(value["execution_plan"]["external_process_invoked"], false);
    assert_eq!(value["execution_plan"]["network_default"], "deny");
    assert_eq!(value["execution_plan"]["writes_allowed"], false);
    assert_eq!(value["execution_plan"]["apply_allowed"], false);
    assert!(value["would_run"].as_str().unwrap().contains("codex"));
    assert_eq!(value["safety"]["external_agent_invoked"], false);

    let artifact: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(run_path).unwrap())
            .expect("run artifact should parse");
    assert_eq!(artifact["allow_external"], true);
    assert_eq!(artifact["proposal_only"], true);
    assert_eq!(artifact["status"], "execution-plan-only");
    assert_eq!(artifact["execution_plan"]["agent_kind"], "codex");
    assert_eq!(artifact["safety_flags"]["external_agent_invoked"], false);
    assert_eq!(artifact["safety_flags"]["apply_allowed"], false);
    assert_eq!(artifact["safety_flags"]["network_allowed"], false);
}

#[test]
fn agent_run_antigravity_allow_external_proposal_only_returns_execution_plan() {
    let _guard = test_lock();
    let run_path = std::path::Path::new(".comptext/runs/latest/run.json");
    let _run_guard = FileGuard::new(run_path);

    let stdout = run(&[
        "--json",
        "agent",
        "run",
        "--kind",
        "antigravity",
        "--task",
        "Antigravity execution plan smoke",
        "--allow-external",
        "--proposal-only",
    ]);
    let value: serde_json::Value =
        serde_json::from_str(&stdout).expect("agent run JSON should parse");
    assert_eq!(value["kind"], "antigravity");
    assert_eq!(value["external_execution"], false);
    assert_eq!(value["dry_run"], false);
    assert_eq!(value["allow_external"], true);
    assert_eq!(value["proposal_only"], true);
    assert_eq!(value["ok"], true);
    assert_eq!(value["status"], "execution-plan-only");
    assert_eq!(value["execution_plan"]["agent_kind"], "antigravity");
    assert_eq!(value["execution_plan"]["mode"], "proposal-only");
    assert_eq!(value["execution_plan"]["external_process_invoked"], false);
    assert!(value["would_run"].as_str().unwrap().contains("antigravity"));

    let artifact: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(run_path).unwrap())
            .expect("run artifact should parse");
    assert_eq!(artifact["execution_plan"]["agent_kind"], "antigravity");
    assert_eq!(artifact["safety_flags"]["external_agent_invoked"], false);
    assert_eq!(artifact["safety_flags"]["apply_allowed"], false);
    assert_eq!(artifact["safety_flags"]["network_allowed"], false);
}

#[test]
fn unknown_agent_kind_fails_with_json_error() {
    let _guard = test_lock();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args([
            "--json", "agent", "run", "--kind", "unknown", "--task", "Nope",
        ])
        .output()
        .expect("ctxt binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    let value: serde_json::Value = serde_json::from_str(&stderr).expect("error JSON should parse");
    assert_eq!(value["ok"], false);
    assert!(value["error"]["message"]
        .as_str()
        .unwrap()
        .contains("unsupported agent kind"));
}

#[test]
fn apply_and_validate_succeeds() {
    let _guard = test_lock();
    let mock_file = std::path::Path::new("tests/mock_applied_patch.rs");
    let _mock_file_guard = FileGuard::new(mock_file);
    std::fs::write(mock_file, "// initial\n").unwrap();

    let mock_proposal = serde_json::json!({
        "schema_version": "0.1",
        "task": "Test apply",
        "rationale": "Verify apply and validate commands",
        "preconditions": [],
        "affected_files": ["tests/mock_applied_patch.rs"],
        "operations": [
            {
                "op": "patch",
                "path": "tests/mock_applied_patch.rs",
                "detail": "Mock test patch detail"
            }
        ],
        "validation_commands": ["cargo --version"],
        "rollback_strategy": "none",
        "risk_notes": "none"
    });

    let proposal_path = std::path::Path::new("proposals/proposal_test_apply.json");
    let _proposal_guard = FileGuard::new(proposal_path);
    std::fs::write(
        proposal_path,
        serde_json::to_string_pretty(&mock_proposal).unwrap(),
    )
    .unwrap();

    let stdout_apply = run(&["apply", "--yes", "proposals/proposal_test_apply.json"]);
    assert!(stdout_apply.contains("Applying Proposal:"));
    assert!(stdout_apply.contains("Proposal applied and validated successfully."));

    let modified_content = std::fs::read_to_string(mock_file).unwrap();
    assert!(modified_content.contains("// Mock patch applied:"));

    let stdout_validate = run(&["validate"]);
    assert!(stdout_validate.contains("Standard local validation commands:"));
    assert!(stdout_validate.contains("cargo test"));
}

#[test]
fn apply_rejects_disallowed_paths() {
    let _guard = test_lock();
    let mock_proposal = serde_json::json!({
        "schema_version": "0.1",
        "task": "Malicious task",
        "rationale": "Try to edit forbidden file",
        "preconditions": [],
        "affected_files": [".env"],
        "operations": [
            {
                "op": "patch",
                "path": ".env",
                "detail": "inject secret"
            }
        ],
        "validation_commands": [],
        "rollback_strategy": "none",
        "risk_notes": "high"
    });

    let path = std::path::Path::new("proposals/proposal_malicious.json");
    let _proposal_guard = FileGuard::new(path);
    std::fs::write(path, serde_json::to_string_pretty(&mock_proposal).unwrap()).unwrap();

    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ctxt"))
        .args(["apply", "--yes", "proposals/proposal_malicious.json"])
        .output()
        .expect("ctxt binary should run");

    assert!(
        !output.status.success(),
        "should fail on security policy violation"
    );
    let stderr = String::from_utf8(output.stderr).expect("stderr should be UTF-8");
    assert!(stderr.contains("Security Policy Violation: Path '.env' is not an allowed write path."));
}

#[test]
fn test_antigravity_commands_skeleton() {
    let _guard = test_lock();

    let out_export = run(&["antigravity", "export"]);
    assert!(out_export.contains("Antigravity bundle export initialized."));

    let out_skills = run(&["antigravity", "skills", "validate"]);
    assert!(out_skills.contains("Validating repo-local skills..."));
    assert!(out_skills.contains("All skill paths verified."));

    let out_agents = run(&["antigravity", "agents", "export"]);
    assert!(out_agents.contains("Exporting advisory subagents metadata..."));
    assert!(out_agents.contains("advisory only"));

    let out_hooks = run(&["antigravity", "hooks", "audit"]);
    assert!(out_hooks.contains("Auditing hook permissions configuration..."));
    assert!(out_hooks.contains("No live runtime hooks detected"));

    let out_plugin = run(&["antigravity", "plugin", "package"]);
    assert!(out_plugin.contains("Packaging repo-local plugin bundle..."));
    assert!(out_plugin.contains("MCP outputs treated as untrusted input"));
}
