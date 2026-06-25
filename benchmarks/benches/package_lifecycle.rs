use comptext_lab::{build_package_from_value, replay_package_value, verify_package_value};
use divan::black_box;
use serde_json::json;

#[divan::bench]
fn package_lifecycle(bencher: divan::Bencher) {
    let value = json!({
        "schema_version": "SPARK-EVIDENCE-PACKET-V1",
        "local_id": "bench",
        "goal": "benchmark",
        "source_summary": "synthetic",
        "context_pack_summary": "",
        "policy_result": "ALLOW",
        "provider_boundary_status": "DEMO",
        "untrusted_proposal": "",
        "human_review_decision": "PASS",
        "claim_hygiene": {
            "allowed_claims": ["synthetic"],
            "blocked_claims": []
        },
        "artifact_manifest": [],
        "warnings": [],
        "limitations": []
    });

    bencher.bench(|| {
        if let Ok(envelope) = build_package_from_value(black_box(&value)) {
            let _ = verify_package_value(black_box(&envelope));
            let _ = replay_package_value(black_box(&envelope));
        }
    });
}

fn main() {
    divan::main();
}
