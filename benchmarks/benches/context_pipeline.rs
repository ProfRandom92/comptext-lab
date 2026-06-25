use comptext_lab::context::{build_context, render_context, validate_context};
use divan::black_box;
use serde_json::json;

fn make_minimal_package() -> serde_json::Value {
    json!({
        "schema_version": "SPARK-EVIDENCE-PACKET-V1",
        "local_id": "bench-ctx",
        "goal": "benchmark context",
        "source_summary": "synthetic fixture",
        "context_pack_summary": "minimal",
        "policy_result": "ALLOW",
        "provider_boundary_status": "DEMO",
        "untrusted_proposal": "n/a",
        "human_review_decision": "PASS",
        "claim_hygiene": {
            "allowed_claims": ["synthetic"],
            "blocked_claims": []
        },
        "artifact_manifest": [],
        "warnings": [],
        "limitations": []
    })
}

fn make_minimal_schema() -> serde_json::Value {
    json!({
        "name": "bench-schema",
        "required_field_paths": ["goal"]
    })
}

#[divan::bench]
fn context_build_render_validate(bencher: divan::Bencher) {
    let package = make_minimal_package();
    let schema = make_minimal_schema();

    bencher.bench(|| {
        if let Ok(ctx) = build_context(black_box(&package), black_box(&schema)) {
            let _ = render_context(black_box(&ctx));
            let _ = validate_context(black_box(&ctx));
        }
    });
}

fn main() {
    divan::main();
}
