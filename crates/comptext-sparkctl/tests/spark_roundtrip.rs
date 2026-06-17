use agy7rust::codec::package::{
    build_package_from_value, build_spark_evidence_packet_envelope, canonical_json,
    collect_field_paths, extract_commitment_tokens, replay_package_value,
    validate_spark_evidence_packet_envelope, validate_spark_evidence_packet_value,
    verify_package_value, ArtifactManifestEntry, ClaimHygiene, HumanReviewDecision, PolicyResult,
    ProviderBoundaryStatus, SparkEvidencePacketPreimage,
};
use agy7rust::sha256_hex;
use serde_json::json;

#[test]
fn test_canonical_json_sorting() {
    let original = json!({
        "z": 1,
        "a": {
            "c": 3,
            "b": 2
        },
        "m": [4, 5, 6]
    });

    let canonical = canonical_json(&original);
    // Keys should be sorted alphabetically: a, m, z
    // Under a, keys should be sorted: b, c
    assert_eq!(canonical, r#"{"a":{"b":2,"c":3},"m":[4,5,6],"z":1}"#);
}

#[test]
fn test_sha256_hex_known_input_is_stable() {
    assert_eq!(
        sha256_hex("abc"),
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    );
}

#[test]
fn test_spark_evidence_packet_demo_shape_validates() {
    let preimage = sample_spark_evidence_preimage();
    let envelope =
        build_spark_evidence_packet_envelope(preimage).expect("evidence envelope should build");

    assert_eq!(
        envelope.preimage.goal,
        "Review deterministic artifact packaging for SPARK Evidence Packet v1."
    );
    assert_eq!(envelope.preimage.policy_result, PolicyResult::ReviewNeeded);
    assert_eq!(
        envelope.preimage.provider_boundary_status,
        ProviderBoundaryStatus::DEMO
    );
    assert_eq!(
        envelope.preimage.human_review_decision,
        HumanReviewDecision::NOTES
    );
    assert!(!envelope.preimage.claim_hygiene.allowed_claims.is_empty());
    assert!(!envelope.preimage.claim_hygiene.blocked_claims.is_empty());
    assert!(!envelope.preimage.artifact_manifest.is_empty());
    assert!(!envelope.preimage.warnings.is_empty());
    assert!(!envelope.preimage.limitations.is_empty());

    let preimage_value = serde_json::to_value(&envelope.preimage).unwrap();
    assert_eq!(envelope.canonical_json, canonical_json(&preimage_value));
    assert_eq!(
        envelope.canonical_hash,
        sha256_hex(&envelope.canonical_json)
    );
    assert!(validate_spark_evidence_packet_envelope(&envelope).is_ok());

    let envelope_value = serde_json::to_value(&envelope).unwrap();
    assert!(validate_spark_evidence_packet_value(&envelope_value).is_ok());
}

#[test]
fn test_spark_evidence_packet_rejects_changed_preimage_with_stale_canonical_json() {
    let mut envelope =
        build_spark_evidence_packet_envelope(sample_spark_evidence_preimage()).unwrap();
    envelope.preimage.goal = "Tampered goal".to_string();

    let err = validate_spark_evidence_packet_envelope(&envelope)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "canonical_json mismatch");
}

#[test]
fn test_spark_evidence_packet_rejects_changed_canonical_json_with_stale_hash() {
    let mut envelope =
        build_spark_evidence_packet_envelope(sample_spark_evidence_preimage()).unwrap();
    envelope.canonical_json = "{}".to_string();

    let err = validate_spark_evidence_packet_envelope(&envelope)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "canonical_json mismatch");
}

#[test]
fn test_spark_evidence_packet_rejects_changed_canonical_hash() {
    let mut envelope =
        build_spark_evidence_packet_envelope(sample_spark_evidence_preimage()).unwrap();
    envelope.canonical_hash =
        "0000000000000000000000000000000000000000000000000000000000000000".to_string();

    let err = validate_spark_evidence_packet_envelope(&envelope)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "canonical_hash mismatch");
}

#[test]
fn test_spark_evidence_packet_rejects_missing_required_review_policy_goal_fields() {
    let mut missing_goal = sample_spark_evidence_preimage();
    missing_goal.goal = " ".to_string();
    assert_eq!(
        build_spark_evidence_packet_envelope(missing_goal)
            .unwrap_err()
            .to_string(),
        "missing goal"
    );

    let mut missing_review = sample_spark_evidence_preimage();
    missing_review.untrusted_proposal = "".to_string();
    assert_eq!(
        build_spark_evidence_packet_envelope(missing_review)
            .unwrap_err()
            .to_string(),
        "missing untrusted_proposal"
    );

    let mut missing_manifest = sample_spark_evidence_preimage();
    missing_manifest.artifact_manifest.clear();
    assert_eq!(
        build_spark_evidence_packet_envelope(missing_manifest)
            .unwrap_err()
            .to_string(),
        "missing artifact_manifest"
    );
}

#[test]
fn test_spark_evidence_packet_rejects_unknown_envelope_field() {
    let envelope = build_spark_evidence_packet_envelope(sample_spark_evidence_preimage()).unwrap();
    let mut envelope_value = serde_json::to_value(&envelope).unwrap();
    envelope_value["unexpected_envelope_field"] = json!("tamper");

    let err = validate_spark_evidence_packet_value(&envelope_value)
        .unwrap_err()
        .to_string();
    assert!(err.contains("unknown field"));
}

#[test]
fn test_spark_evidence_packet_rejects_unknown_preimage_field() {
    let mut preimage_value = serde_json::to_value(sample_spark_evidence_preimage()).unwrap();
    preimage_value["unexpected_preimage_field"] = json!("tamper");

    let err = serde_json::from_value::<SparkEvidencePacketPreimage>(preimage_value)
        .unwrap_err()
        .to_string();
    assert!(err.contains("unknown field"));
}

#[test]
fn test_spark_evidence_packet_rejects_blank_allowed_claim() {
    let mut preimage = sample_spark_evidence_preimage();
    preimage
        .claim_hygiene
        .allowed_claims
        .push("   ".to_string());

    let err = build_spark_evidence_packet_envelope(preimage)
        .unwrap_err()
        .to_string();
    assert_eq!(
        err,
        "missing or empty claim in claim_hygiene.allowed_claims"
    );
}

#[test]
fn test_spark_evidence_packet_rejects_blank_blocked_claim() {
    let mut preimage = sample_spark_evidence_preimage();
    preimage.claim_hygiene.blocked_claims.push("".to_string());

    let err = build_spark_evidence_packet_envelope(preimage)
        .unwrap_err()
        .to_string();
    assert_eq!(
        err,
        "missing or empty claim in claim_hygiene.blocked_claims"
    );
}

#[test]
fn test_spark_evidence_packet_rejects_blank_warning() {
    let mut preimage = sample_spark_evidence_preimage();
    preimage.warnings.push("\t".to_string());

    let err = build_spark_evidence_packet_envelope(preimage)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "missing or empty warning");
}

#[test]
fn test_spark_evidence_packet_rejects_blank_limitation() {
    let mut preimage = sample_spark_evidence_preimage();
    preimage.limitations.push("\n".to_string());

    let err = build_spark_evidence_packet_envelope(preimage)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "missing or empty limitation");
}

fn sample_spark_evidence_preimage() -> SparkEvidencePacketPreimage {
    SparkEvidencePacketPreimage {
        schema_version: "SPARK-EVIDENCE-PACKET-V1".to_string(),
        local_id: "unit-test-packet".to_string(),
        goal: "Review deterministic artifact packaging for SPARK Evidence Packet v1.".to_string(),
        source_summary: "Synthetic local fixture summary.".to_string(),
        context_pack_summary: "Context pack summary for deterministic review.".to_string(),
        policy_result: PolicyResult::ReviewNeeded,
        provider_boundary_status: ProviderBoundaryStatus::DEMO,
        untrusted_proposal: "Untrusted proposal requires human review.".to_string(),
        human_review_decision: HumanReviewDecision::NOTES,
        claim_hygiene: ClaimHygiene {
            allowed_claims: vec![
                "deterministic canonical packaging".to_string(),
                "artifact manifest".to_string(),
            ],
            blocked_claims: vec![
                "production-ready".to_string(),
                "guaranteed correctness".to_string(),
            ],
        },
        artifact_manifest: vec![ArtifactManifestEntry {
            path: "artifacts/spark/evidence_packet_v1.json".to_string(),
            role: "evidence_packet".to_string(),
            sha256: None,
        }],
        warnings: vec!["Provider output is untrusted until reviewed.".to_string()],
        limitations: vec!["No compliance or production claim is made.".to_string()],
    }
}

#[test]
fn test_field_paths_collection() {
    let original = json!({
        "case_id": "SPARK-1",
        "metadata": {
            "hash": "abc"
        },
        "items": [
            {"name": "first"}
        ]
    });

    let paths = collect_field_paths(&original);
    // Should be sorted alphabetically before traversal
    assert!(paths.contains(&"$".to_string()));
    assert!(paths.contains(&"$.case_id".to_string()));
    assert!(paths.contains(&"$.metadata".to_string()));
    assert!(paths.contains(&"$.metadata.hash".to_string()));
    assert!(paths.contains(&"$.items".to_string()));
    assert!(paths.contains(&"$.items[0]".to_string()));
    assert!(paths.contains(&"$.items[0].name".to_string()));
}

#[test]
fn test_commitment_tokens_extraction() {
    let original = json!({
        "case_id": "SPARK-1",
        "document_type": "PDF",
        "authority": "Amt",
        "procedure_type": "Normal",
        "applicant": "XYZ GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "123",
                "decision_recommendation": "Yes"
            }
        },
        "ignored_field": "secret"
    });

    let tokens = extract_commitment_tokens(&original);
    assert_eq!(tokens.len(), 7);
    assert!(tokens.contains(&"SPARK-1".to_string()));
    assert!(tokens.contains(&"PDF".to_string()));
    assert!(tokens.contains(&"Amt".to_string()));
    assert!(tokens.contains(&"Normal".to_string()));
    assert!(tokens.contains(&"XYZ GmbH".to_string()));
    assert!(tokens.contains(&"123".to_string()));
    assert!(tokens.contains(&"Yes".to_string()));
    // Ignored field value should not be extracted
    assert!(!tokens.contains(&"secret".to_string()));
}

#[test]
fn test_package_verification_lifecycle() {
    let original = json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    // 1. Build package
    let package = build_package_from_value(&original).expect("Build package failed");

    // 2. Verification of valid package
    assert!(verify_package_value(&package).is_ok());

    // 3. Mutate payload (tampering)
    let mut mutated_payload = package.clone();
    mutated_payload["payload"]["extraction"]["fields"]["parcel_id"] = json!("TAMPERED");
    assert!(verify_package_value(&mutated_payload).is_err());

    // 4. Mutate sidecar hash (tampering)
    let mut mutated_sidecar = package.clone();
    mutated_sidecar["sidecar"]["payload_sha256"] =
        json!("0000000000000000000000000000000000000000000000000000000000000000");
    assert!(verify_package_value(&mutated_sidecar).is_err());

    // 5. Mutate integrity hash (tampering)
    let mut mutated_integrity = package.clone();
    mutated_integrity["integrity_hash"] =
        json!("0000000000000000000000000000000000000000000000000000000000000000");
    assert!(verify_package_value(&mutated_integrity).is_err());
}

#[test]
fn test_replay_canonical_format() {
    let original = json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let package = build_package_from_value(&original).expect("Build package failed");
    let replay = replay_package_value(&package).expect("Replay failed");

    assert_eq!(replay["schema"].as_str().unwrap(), "SPARK-V7-REPLAY");
    assert_eq!(
        replay["source_type"].as_str().unwrap(),
        "spark_extraction_json"
    );
    assert!(replay.get("payload_sha256").is_some());
    assert!(replay.get("tool_sequence").is_some());
    assert!(replay.get("commitment_tokens").is_some());
    assert!(replay.get("field_paths").is_some());
    // Should NOT contain the original payload fields directly
    assert!(replay.get("payload").is_none());
}

#[test]
fn test_schema_checking_scenarios() {
    let valid_input = json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.document_type",
            "$.authority",
            "$.procedure_type",
            "$.applicant",
            "$.extraction.fields.parcel_id",
            "$.extraction.fields.location",
            "$.extraction.fields.project_type",
            "$.extraction.fields.decision_recommendation",
            "$.metadata.source_pdf_sha256"
        ],
        "non_claims": []
    });

    // 1. Valid fixture passes schema-check logic
    let res = agy7rust::codec::package::validate_schema(&valid_input, &valid_schema);
    assert!(res.is_ok());
    let (name, required, checked) = res.unwrap();
    assert_eq!(name, "genehmigung_v1");
    assert_eq!(required, 10);
    assert_eq!(checked, 10);

    // 2. Missing $.extraction.fields.parcel_id fails
    let mut missing_parcel = valid_input.clone();
    missing_parcel["extraction"]["fields"]
        .as_object_mut()
        .unwrap()
        .remove("parcel_id");
    let res = agy7rust::codec::package::validate_schema(&missing_parcel, &valid_schema);
    assert!(res.is_err());
    assert_eq!(
        res.unwrap_err().to_string(),
        "required field missing: $.extraction.fields.parcel_id"
    );

    // 3. Empty $.extraction.fields.decision_recommendation fails
    let mut empty_decision = valid_input.clone();
    empty_decision["extraction"]["fields"]["decision_recommendation"] = json!("   ");
    let res = agy7rust::codec::package::validate_schema(&empty_decision, &valid_schema);
    assert!(res.is_err());
    assert_eq!(
        res.unwrap_err().to_string(),
        "required field empty: $.extraction.fields.decision_recommendation"
    );

    // 4. Object value at required scalar path fails
    let mut object_instead_of_scalar = valid_input.clone();
    object_instead_of_scalar["extraction"]["fields"]["parcel_id"] = json!({ "nested": "object" });
    let res = agy7rust::codec::package::validate_schema(&object_instead_of_scalar, &valid_schema);
    assert!(res.is_err());
    assert_eq!(
        res.unwrap_err().to_string(),
        "required field not scalar: $.extraction.fields.parcel_id"
    );

    // 5. Invalid schema name fails
    let mut bad_schema_type = valid_schema.clone();
    bad_schema_type["schema"] = json!("SPARK-V7-INVALID");
    let res = agy7rust::codec::package::validate_schema(&valid_input, &bad_schema_type);
    assert!(res.is_err());
    assert_eq!(res.unwrap_err().to_string(), "schema mismatch");

    // 6. Missing schema version fails cleanly
    let mut missing_version_schema = valid_schema.clone();
    missing_version_schema
        .as_object_mut()
        .unwrap()
        .remove("version");
    let res = agy7rust::codec::package::validate_schema(&valid_input, &missing_version_schema);
    assert!(res.is_err());
    assert_eq!(res.unwrap_err().to_string(), "unsupported schema version");

    // 7. Unsupported schema version fails cleanly
    let mut unsupported_version_schema = valid_schema.clone();
    unsupported_version_schema["version"] = json!(2);
    let res = agy7rust::codec::package::validate_schema(&valid_input, &unsupported_version_schema);
    assert!(res.is_err());
    assert_eq!(res.unwrap_err().to_string(), "unsupported schema version");

    // 8. Unsupported path syntax fails cleanly
    let mut unsupported_path_schema = valid_schema.clone();
    unsupported_path_schema["required_field_paths"] = json!(["$.extraction.fields[0].parcel_id"]);
    let res = agy7rust::codec::package::validate_schema(&valid_input, &unsupported_path_schema);
    assert!(res.is_err());
    assert_eq!(res.unwrap_err().to_string(), "unsupported path syntax");
}

#[test]
fn test_context_model_shape_accepts_minimal_valid_context() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};

    let ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    assert!(ctx.validate_model_shape().is_ok());
}

#[test]
fn test_context_model_sort_stable_is_deterministic() {
    use agy7rust::context::model::{ContextDependencyEdge, ContextValidation, OperationalContext};

    let mut ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.document_type".to_string(), "$.case_id".to_string()],
        satisfied_field_paths: vec!["$.applicant".to_string(), "$.authority".to_string()],
        missing_field_paths: vec!["$.parcel_id".to_string()],
        constraints: vec!["no_unsafe".to_string(), "no_side_effects".to_string()],
        required_order: vec!["b".to_string(), "a".to_string()],
        dependency_edges: vec![
            ContextDependencyEdge {
                source: "b".to_string(),
                target: "y".to_string(),
            },
            ContextDependencyEdge {
                source: "a".to_string(),
                target: "z".to_string(),
            },
            ContextDependencyEdge {
                source: "b".to_string(),
                target: "x".to_string(),
            },
        ],
        blockers: vec![ContextDependencyEdge {
            source: "c".to_string(),
            target: "w".to_string(),
        }],
        recovery_paths: vec![ContextDependencyEdge {
            source: "d".to_string(),
            target: "v".to_string(),
        }],
        validation: ContextValidation {
            valid: false,
            failure_labels: vec!["label_b".to_string(), "label_a".to_string()],
            issues: vec!["issue_b".to_string(), "issue_a".to_string()],
        },
        non_claims: vec!["claim_b".to_string(), "claim_a".to_string()],
    };

    ctx.sort_stable();

    assert_eq!(
        ctx.required_field_paths,
        vec!["$.case_id".to_string(), "$.document_type".to_string()]
    );
    assert_eq!(
        ctx.satisfied_field_paths,
        vec!["$.applicant".to_string(), "$.authority".to_string()]
    );
    assert_eq!(ctx.missing_field_paths, vec!["$.parcel_id".to_string()]);
    assert_eq!(
        ctx.constraints,
        vec!["no_side_effects".to_string(), "no_unsafe".to_string()]
    );
    assert_eq!(ctx.required_order, vec!["a".to_string(), "b".to_string()]);

    assert_eq!(
        ctx.dependency_edges,
        vec![
            ContextDependencyEdge {
                source: "a".to_string(),
                target: "z".to_string()
            },
            ContextDependencyEdge {
                source: "b".to_string(),
                target: "x".to_string()
            },
            ContextDependencyEdge {
                source: "b".to_string(),
                target: "y".to_string()
            },
        ]
    );

    assert_eq!(
        ctx.validation.failure_labels,
        vec!["label_a".to_string(), "label_b".to_string()]
    );
    assert_eq!(
        ctx.validation.issues,
        vec!["issue_a".to_string(), "issue_b".to_string()]
    );
    assert_eq!(
        ctx.non_claims,
        vec!["claim_a".to_string(), "claim_b".to_string()]
    );
}

#[test]
fn test_context_model_rejects_missing_context_id() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};

    let ctx = OperationalContext {
        context_id: "".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "missing context_id"
    );
}

#[test]
fn test_context_model_rejects_missing_source_package_hash() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};

    let ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "missing source_package_hash"
    );
}

#[test]
fn test_context_model_rejects_missing_required_field_paths() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};

    let mut ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec![],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "missing required_field_paths"
    );

    ctx.required_field_paths = vec!["".to_string()];
    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "empty required_field_path"
    );
}

#[test]
fn test_context_model_rejects_empty_dependency_edge() {
    use agy7rust::context::model::{ContextDependencyEdge, ContextValidation, OperationalContext};

    let mut ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![ContextDependencyEdge {
            source: "".to_string(),
            target: "b".to_string(),
        }],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "empty dependency edge"
    );

    ctx.dependency_edges = vec![];
    ctx.blockers = vec![ContextDependencyEdge {
        source: "a".to_string(),
        target: "".to_string(),
    }];
    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "empty blocker edge"
    );

    ctx.blockers = vec![];
    ctx.recovery_paths = vec![ContextDependencyEdge {
        source: "".to_string(),
        target: "".to_string(),
    }];
    assert_eq!(
        ctx.validate_model_shape().unwrap_err(),
        "empty recovery edge"
    );
}

#[test]
fn test_context_model_serialization_has_no_raw_payload_fields() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};

    let ctx = OperationalContext {
        context_id: "ctx_123".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    let serialized = serde_json::to_string(&ctx).expect("Serialization failed");

    assert!(!serialized.contains("applicant"));
    assert!(!serialized.contains("decision_recommendation"));
    assert!(!serialized.contains("extraction.notes"));
    assert!(!serialized.contains("source_pdf_contents"));
    assert!(!serialized.contains("\"payload\":"));
}

#[test]
fn test_context_build_from_current_package_and_schema_succeeds() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.document_type",
            "$.authority",
            "$.procedure_type",
            "$.applicant",
            "$.extraction.fields.parcel_id",
            "$.extraction.fields.location",
            "$.extraction.fields.project_type",
            "$.extraction.fields.decision_recommendation",
            "$.metadata.source_pdf_sha256"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let ctx = build_context(&package, &valid_schema);
    assert!(ctx.is_ok());
    let context_val = ctx.unwrap();
    assert_eq!(context_val.schema_name, "genehmigung_v1");
    assert!(context_val.validation.valid);
}

#[test]
fn test_context_build_output_validates_model_shape() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.document_type",
            "$.authority",
            "$.procedure_type",
            "$.applicant",
            "$.extraction.fields.parcel_id",
            "$.extraction.fields.location",
            "$.extraction.fields.project_type",
            "$.extraction.fields.decision_recommendation",
            "$.metadata.source_pdf_sha256"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();
    assert!(context_val.validate_model_shape().is_ok());
}

#[test]
fn test_context_build_repeated_output_is_byte_identical() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.document_type",
            "$.authority",
            "$.procedure_type",
            "$.applicant",
            "$.extraction.fields.parcel_id",
            "$.extraction.fields.location",
            "$.extraction.fields.project_type",
            "$.extraction.fields.decision_recommendation",
            "$.metadata.source_pdf_sha256"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();

    let ctx1 = build_context(&package, &valid_schema).unwrap();
    let ctx2 = build_context(&package, &valid_schema).unwrap();

    let s1 = serde_json::to_string_pretty(&ctx1).unwrap();
    let s2 = serde_json::to_string_pretty(&ctx2).unwrap();

    assert_eq!(s1, s2);
}

#[test]
fn test_context_build_missing_required_path_is_reported() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.extraction.fields.parcel_id"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    assert!(!context_val.validation.valid);
    assert!(context_val
        .missing_field_paths
        .contains(&"$.extraction.fields.parcel_id".to_string()));
    assert!(context_val
        .validation
        .failure_labels
        .contains(&"MISSING_REQUIRED_FIELD".to_string()));
    assert!(context_val.validation.issues[0].contains("$.extraction.fields.parcel_id"));
}

#[test]
fn test_context_build_context_id_is_deterministic() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let ctx1 = build_context(&package, &valid_schema).unwrap();
    let ctx2 = build_context(&package, &valid_schema).unwrap();

    assert_eq!(ctx1.context_id, ctx2.context_id);
    assert!(!ctx1.context_id.is_empty());
}

#[test]
fn test_context_build_json_does_not_leak_raw_payload_values() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::build_context;

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.applicant"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    let serialized = serde_json::to_string(&context_val).unwrap();

    assert!(!serialized.contains("Nordwind Energie GmbH"));
    assert!(!serialized.contains("Zustimmung mit Nebenbestimmungen zur Schallemission"));
    assert!(!serialized.contains("Static test case for planning approval"));
    assert!(!serialized.contains("source_pdf_contents"));
    assert!(!serialized.contains("\"payload\":"));
}

#[test]
fn test_context_build_command_exists() {
    use agy7rust::commands::Cli;
    use clap::CommandFactory;

    let cmd = Cli::command();
    let subcommands: Vec<&str> = cmd.get_subcommands().map(|c| c.get_name()).collect();
    assert!(subcommands.contains(&"context-build"));
}

#[test]
fn test_context_render_command_exists() {
    use agy7rust::commands::Cli;
    use clap::CommandFactory;

    let cmd = Cli::command();
    let subcommands: Vec<&str> = cmd.get_subcommands().map(|c| c.get_name()).collect();
    assert!(subcommands.contains(&"context-render"));
}

#[test]
fn test_context_render_deterministic() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::{build_context, render_context};

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.document_type"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    let r1 = render_context(&context_val);
    let r2 = render_context(&context_val);

    assert_eq!(r1, r2);
    assert!(r1.ends_with('\n'));
}

#[test]
fn test_context_render_leak_free() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::{build_context, render_context};

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id",
            "$.applicant"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    let rendered = render_context(&context_val);

    assert!(!rendered.contains("Nordwind Energie GmbH"));
    assert!(!rendered.contains("Zustimmung mit Nebenbestimmungen zur Schallemission"));
    assert!(!rendered.contains("Static test case for planning approval"));
    assert!(!rendered.contains("source_pdf_contents"));
}

#[test]
fn test_context_validate_command_exists() {
    use agy7rust::commands::Cli;
    use clap::CommandFactory;

    let cmd = Cli::command();
    let subcommands: Vec<&str> = cmd.get_subcommands().map(|c| c.get_name()).collect();
    assert!(subcommands.contains(&"context-validate"));
}

#[test]
fn test_context_validate_deterministic() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::{build_context, validate_context};

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    let r1 = validate_context(&context_val);
    let r2 = validate_context(&context_val);

    assert_eq!(r1, r2);
    assert!(r1.is_ok());
}

#[test]
fn test_context_validate_leak_free() {
    use agy7rust::codec::package::build_package_from_value;
    use agy7rust::context::{build_context, validate_context};

    let valid_input = serde_json::json!({
        "case_id": "SPARK-2026-0042",
        "document_type": "BImSchG-Genehmigungsantrag",
        "authority": "Staatliches Amt fuer Umwelt und Arbeitsschutz",
        "procedure_type": "Vereinfachtes Verfahren",
        "applicant": "Nordwind Energie GmbH",
        "extraction": {
            "fields": {
                "parcel_id": "DE-NI-004-9872",
                "location": "Gemarkung Neustadt, Flur 12, Flueck 5",
                "project_type": "Errichtung Windkraftanlage WKA-03",
                "decision_recommendation": "Zustimmung mit Nebenbestimmungen zur Schallemission"
            },
            "confidence": 0.945,
            "notes": "Static test case for planning approval acceleration pipeline."
        },
        "metadata": {
            "source_pdf_sha256": "8f395d98a72b0c3cf0d262e3b8a3e03d428e253f1bdf4cfa489d2b5801d3b46fc"
        }
    });

    let valid_schema = serde_json::json!({
        "schema": "SPARK-V7-SCHEMA",
        "version": 1,
        "name": "genehmigung_v1",
        "fixture_type": "synthetic_spark_style",
        "required_field_paths": [
            "$.case_id"
        ],
        "non_claims": []
    });

    let package = build_package_from_value(&valid_input).unwrap();
    let context_val = build_context(&package, &valid_schema).unwrap();

    let res = validate_context(&context_val);
    assert!(res.is_ok());
}

#[test]
fn test_context_validate_invalid_shape_fails() {
    use agy7rust::context::model::{ContextValidation, OperationalContext};
    use agy7rust::context::validate_context;

    let ctx = OperationalContext {
        context_id: "".to_string(),
        source_package_hash: "hash_456".to_string(),
        schema_name: "genehmigung_v1".to_string(),
        schema_version: 1,
        required_field_paths: vec!["$.case_id".to_string()],
        satisfied_field_paths: vec![],
        missing_field_paths: vec![],
        constraints: vec![],
        required_order: vec![],
        dependency_edges: vec![],
        blockers: vec![],
        recovery_paths: vec![],
        validation: ContextValidation {
            valid: true,
            failure_labels: vec![],
            issues: vec![],
        },
        non_claims: vec!["no_mcp_integration".to_string()],
    };

    let res = validate_context(&ctx);
    assert!(res.is_err());
    assert!(res.unwrap_err().contains("validate_model_shape failed"));
}

#[test]
fn test_sparkctl_doctor_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .args(["run", "--bin", "sparkctl", "--", "doctor"])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("=== sparkctl doctor report ==="));
    assert!(stdout_str.contains("doctor result: PASS"));
}

#[test]
fn test_sparkctl_rust_validate_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .env("SPARKCTL_IN_TEST", "1")
        .args(["run", "--bin", "sparkctl", "--", "rust-validate"])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("=== sparkctl rust-validate ==="));
    assert!(stdout_str.contains("rust-validate result: PASS"));
}

#[test]
fn test_sparkctl_context_all_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .args(["run", "--bin", "sparkctl", "--", "context-all"])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("=== sparkctl context-all ==="));
    assert!(stdout_str.contains("context-all result: PASS"));
}

#[test]
fn test_sparkctl_spark_demo_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .args(["run", "--bin", "sparkctl", "--", "spark-demo"])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("=== sparkctl spark-demo ==="));
    assert!(stdout_str.contains("spark-demo result: PASS"));
}

#[test]
fn test_sparkctl_handoff_check_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .args(["run", "--bin", "sparkctl", "--", "handoff-check"])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("=== sparkctl handoff-check ==="));
    assert!(stdout_str.contains("handoff-check result: PASS"));
}

#[test]
fn test_package_verify_and_replay_with_structured_errors_and_ledger() {
    use agy7rust::codec::package::{replay_package_value, verify_package_value};
    use serde_json::json;

    // Helper to construct a valid package envelope
    let make_pkg = |payload: serde_json::Value,
                    ledger: Option<serde_json::Value>,
                    ledger_root: Option<&str>|
     -> serde_json::Value {
        use agy7rust::codec::hash::sha256_hex;
        use agy7rust::codec::package::canonical_json;

        let payload_canonical = canonical_json(&payload);
        let payload_sha256 = sha256_hex(&payload_canonical);

        let mut sidecar_pre = json!({
            "schema_version": "KVTC7-SPARK-1",
            "source_type": "spark_extraction_json",
            "payload_sha256": payload_sha256
        });

        let sidecar_canonical = canonical_json(&sidecar_pre);
        let final_state_hash = sha256_hex(&sidecar_canonical);

        sidecar_pre["final_state_hash"] = serde_json::Value::String(final_state_hash);

        let mut pkg = json!({
            "schema": "SPARK-V7-PACKAGE",
            "version": 1,
            "payload": payload,
            "sidecar": sidecar_pre
        });

        if let Some(l) = ledger {
            pkg["ledger"] = l;
        }
        if let Some(r) = ledger_root {
            pkg["ledger_root"] = serde_json::Value::String(r.to_string());
        }

        let pkg_canonical = canonical_json(&pkg);
        let integrity_hash = sha256_hex(&pkg_canonical);
        pkg["integrity_hash"] = serde_json::Value::String(integrity_hash);

        pkg
    };

    // 1. Valid package without ledger
    let valid_pkg = make_pkg(json!({"case_id": "SPARK-123"}), None, None);
    assert!(verify_package_value(&valid_pkg).is_ok());
    assert!(replay_package_value(&valid_pkg).is_ok());

    // 2. Missing evidence field -> returns EVIDENCE_LOSS
    let mut missing_field_pkg = valid_pkg.clone();
    missing_field_pkg.as_object_mut().unwrap().remove("payload");
    let err = verify_package_value(&missing_field_pkg).unwrap_err();
    assert!(err.to_string().contains("EVIDENCE_LOSS"));

    // 3. Hash manipulation -> returns CONSTRAINT_DRIFT
    let mut manipulated_pkg = valid_pkg.clone();
    manipulated_pkg["sidecar"]["payload_sha256"] =
        json!("wronghashwronghashwronghashwronghashwronghashwronghashwronghash");
    let err = verify_package_value(&manipulated_pkg).unwrap_err();
    assert!(err.to_string().contains("CONSTRAINT_DRIFT"));

    // 4. Replay fails on verify failure
    let err_replay = replay_package_value(&manipulated_pkg).unwrap_err();
    assert!(err_replay.to_string().contains("CONSTRAINT_DRIFT"));

    // 5. Valid package with ledger
    let valid_pkg_with_ledger = make_pkg(
        json!({"case_id": "SPARK-123"}),
        Some(json!([
            {"entry_hash": "hash1", "previous_hash": "0"},
            {"entry_hash": "hash2", "previous_hash": "hash1"}
        ])),
        Some("hash2"),
    );
    assert!(verify_package_value(&valid_pkg_with_ledger).is_ok());

    // 6. Ledger chaining mismatch -> returns CONSTRAINT_DRIFT
    let manipulated_ledger_pkg = make_pkg(
        json!({"case_id": "SPARK-123"}),
        Some(json!([
            {"entry_hash": "hash1", "previous_hash": "0"},
            {"entry_hash": "hash2", "previous_hash": "wrongchainhash"}
        ])),
        Some("hash2"),
    );
    let err = verify_package_value(&manipulated_ledger_pkg).unwrap_err();
    assert!(err.to_string().contains("CONSTRAINT_DRIFT"));
    assert!(err.to_string().contains("ledger chaining mismatch"));

    // 7. Ledger anchoring mismatch -> returns CONSTRAINT_DRIFT
    let manipulated_ledger_root_pkg = make_pkg(
        json!({"case_id": "SPARK-123"}),
        Some(json!([
            {"entry_hash": "hash1", "previous_hash": "0"},
            {"entry_hash": "hash2", "previous_hash": "hash1"}
        ])),
        Some("wrongroot"),
    );
    let err = verify_package_value(&manipulated_ledger_root_pkg).unwrap_err();
    assert!(err.to_string().contains("CONSTRAINT_DRIFT"));
    assert!(err.to_string().contains("ledger root anchoring mismatch"));
}

#[test]
fn test_agy_ct_package_inspect_execution() {
    use std::process::Command;
    let output = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "inspect",
            "-i",
            "../artifacts/spark/extraction.spkg",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("schema: SPARK-V7-PACKAGE"));
    assert!(stdout_str.contains("source_type: spark_extraction_json"));
    assert!(stdout_str.contains("field_paths count:"));
    assert!(stdout_str.contains("commitment_tokens count:"));
    assert!(stdout_str.contains("tool_sequence count:"));
}

#[test]
fn test_agy_ct_package_replay_output_streams() {
    use std::process::Command;

    // 1. Standard run (should output status on stderr with color codes, and JSON on stdout)
    let output = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "replay",
            "-i",
            "../artifacts/spark/extraction.spkg",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    let stderr_str = String::from_utf8_lossy(&output.stderr);

    // Verify stdout contains the replayed JSON schema
    assert!(stdout_str.contains("\"schema\": \"SPARK-V7-REPLAY\""));
    // Verify stderr contains status and color escapes
    assert!(stderr_str.contains("Replaying sidecar trace"));
    assert!(stderr_str.contains("\x1b[36m")); // cyan color code for status

    // 2. Quiet run (should output JSON on stdout, but stderr should be empty/contain no status messages)
    let output_quiet = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "--quiet",
            "package",
            "replay",
            "-i",
            "../artifacts/spark/extraction.spkg",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_quiet.status.success());
    let stdout_quiet = String::from_utf8_lossy(&output_quiet.stdout);
    let stderr_quiet = String::from_utf8_lossy(&output_quiet.stderr);

    assert!(stdout_quiet.contains("\"schema\": \"SPARK-V7-REPLAY\""));
    assert!(!stderr_quiet.contains("Replaying sidecar trace"));

    // 3. Plain run (should output JSON on stdout, status on stderr but without ANSI escapes)
    let output_plain = Command::new("cargo")
        .env("CARGO_TERM_COLOR", "never")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "--plain",
            "package",
            "replay",
            "-i",
            "../artifacts/spark/extraction.spkg",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_plain.status.success());
    let stdout_plain = String::from_utf8_lossy(&output_plain.stdout);
    let stderr_plain = String::from_utf8_lossy(&output_plain.stderr);

    assert!(stdout_plain.contains("\"schema\": \"SPARK-V7-REPLAY\""));
    assert!(stderr_plain.contains("Replaying sidecar trace"));
    assert!(!stderr_plain.contains("\x1b["));
}

#[test]
fn test_agy_ct_schema_check_execution() {
    use std::process::Command;

    // 1. Valid call (should return exit status success)
    let output = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "schema",
            "check",
            "-i",
            "../examples/spark/extraction.json",
            "-s",
            "../schemas/genehmigung_v1.json",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("OK: schema-check passed"));
    assert!(stdout_str.contains("schema: genehmigung_v1"));

    // 2. Invalid call (should fail)
    let output_fail = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "schema",
            "check",
            "-i",
            "../examples/spark/pdf_extraction_fixture.json",
            "-s",
            "../schemas/genehmigung_v1.json",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_fail.status.success());
}

#[test]
fn test_agy_ct_context_validate_execution() {
    use serde_json::json;
    use std::fs;
    use std::process::Command;

    let temp_dir = std::env::temp_dir();
    let valid_path = temp_dir.join("test_valid_context.json");
    let invalid_path = temp_dir.join("test_invalid_context.json");

    // 1. Create a minimal valid context JSON
    let valid_ctx = json!({
        "context_id": "ctx-valid-123",
        "source_package_hash": "hash-123",
        "schema_name": "schema-123",
        "schema_version": 1,
        "required_field_paths": ["$.field1"],
        "satisfied_field_paths": ["$.field1"],
        "missing_field_paths": [],
        "constraints": [],
        "required_order": [],
        "dependency_edges": [],
        "blockers": [],
        "recovery_paths": [],
        "validation": {
            "valid": true,
            "failure_labels": [],
            "issues": []
        },
        "non_claims": ["some_claim"]
    });

    fs::write(&valid_path, serde_json::to_string(&valid_ctx).unwrap()).unwrap();

    // 2. Create a minimal invalid context JSON
    let invalid_ctx = json!({
        "context_id": "ctx-invalid-123",
        "source_package_hash": "hash-123",
        "schema_name": "schema-123",
        "schema_version": 1,
        "required_field_paths": ["$.field1"],
        "satisfied_field_paths": [],
        "missing_field_paths": ["$.field1"],
        "constraints": [],
        "required_order": [],
        "dependency_edges": [],
        "blockers": [],
        "recovery_paths": [],
        "validation": {
            "valid": false,
            "failure_labels": ["MISSING_REQUIRED_FIELD"],
            "issues": ["field1 is missing"]
        },
        "non_claims": ["some_claim"]
    });

    fs::write(&invalid_path, serde_json::to_string(&invalid_ctx).unwrap()).unwrap();

    // 3. Test valid context validation (should return exit status success)
    let output_valid = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "context",
            "validate",
            "-i",
            valid_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_valid.status.success());
    let stdout_str = String::from_utf8_lossy(&output_valid.stdout);
    assert!(stdout_str.contains("OK: context-validate passed"));
    assert!(stdout_str.contains("context: ctx-valid-123"));

    // 4. Test invalid context validation (should fail)
    let output_invalid = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "context",
            "validate",
            "-i",
            invalid_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_invalid.status.success());

    // 5. Cleanup
    let _ = fs::remove_file(valid_path);
    let _ = fs::remove_file(invalid_path);
}

#[test]
fn test_agy_ct_context_build_execution() {
    use agy7rust::codec::package::build_package_from_value;
    use std::fs;
    use std::process::Command;

    let temp_dir = std::env::temp_dir();
    let temp_package_path = temp_dir.join("test_package.spkg");
    let temp_context_path = temp_dir.join("test_context.json");

    // 1. Read and parse extraction.json, build spkg dynamically in memory
    let input_content = fs::read_to_string("../examples/spark/extraction.json").unwrap();
    let input_value: serde_json::Value = serde_json::from_str(&input_content).unwrap();
    let package_value = build_package_from_value(&input_value).unwrap();

    // 2. Write spkg to tempdir
    let package_json = serde_json::to_string(&package_value).unwrap();
    fs::write(&temp_package_path, &package_json).unwrap();

    // 3. Invoke context build CLI (should return exit status success)
    let output = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "context",
            "build",
            "-i",
            temp_package_path.to_str().unwrap(),
            "-s",
            "../schemas/genehmigung_v1.json",
            "-o",
            temp_context_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output.status.success());
    let stdout_str = String::from_utf8_lossy(&output.stdout);
    assert!(stdout_str.contains("OK: context-build passed"));
    assert!(stdout_str.contains("context:"));

    // 4. Verify context was created in temp dir and is readable
    assert!(temp_context_path.exists());
    let context_content = fs::read_to_string(&temp_context_path).unwrap();
    assert!(context_content.contains("\"context_id\":"));

    // 5. Cleanup
    let _ = fs::remove_file(temp_package_path);
    let _ = fs::remove_file(temp_context_path);
}

#[test]
fn test_agy_ct_context_render_execution() {
    use serde_json::json;
    use std::fs;
    use std::process::Command;

    let temp_dir = std::env::temp_dir();
    let temp_input_path = temp_dir.join("test_render_input.json");
    let temp_output_path = temp_dir.join("test_render_output.txt");
    let temp_bad_input_path = temp_dir.join("test_render_bad_input.json");
    let temp_bad_output_path = temp_dir.join("test_render_bad_output.txt");

    // Ensure we clean up any pre-existing output files
    let _ = fs::remove_file(&temp_output_path);
    let _ = fs::remove_file(&temp_bad_output_path);

    // ============================================
    // 1. Success Test: Valid context JSON
    // ============================================
    let valid_ctx = json!({
        "context_id": "ctx-render-test-123",
        "source_package_hash": "hash-999",
        "schema_name": "genehmigung_v1",
        "schema_version": 1,
        "required_field_paths": ["$.case_id"],
        "satisfied_field_paths": ["$.case_id"],
        "missing_field_paths": [],
        "constraints": [],
        "required_order": [],
        "dependency_edges": [],
        "blockers": [],
        "recovery_paths": [],
        "validation": {
            "valid": true,
            "failure_labels": [],
            "issues": []
        },
        "non_claims": []
    });

    fs::write(&temp_input_path, serde_json::to_string(&valid_ctx).unwrap()).unwrap();

    let output_success = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "context",
            "render",
            "-i",
            temp_input_path.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success.status.success());
    let stdout_str = String::from_utf8_lossy(&output_success.stdout);
    assert!(stdout_str.contains("OK: context-render passed"));
    assert!(stdout_str.contains("context: ctx-render-test-123"));

    assert!(temp_output_path.exists());
    let render_content = fs::read_to_string(&temp_output_path).unwrap();
    assert!(!render_content.is_empty());
    assert!(render_content.contains("ctx-render-test-123"));
    assert!(render_content.contains("genehmigung_v1"));

    // ============================================
    // 2. Failure Test: Corrupted context JSON
    // ============================================
    fs::write(&temp_bad_input_path, "{ \"invalid\": ").unwrap();

    let output_failure = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "context",
            "render",
            "-i",
            temp_bad_input_path.to_str().unwrap(),
            "-o",
            temp_bad_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure.status.success());
    // Verify that the bad output file was not written (or doesn't exist)
    assert!(!temp_bad_output_path.exists());

    // ============================================
    // 3. Cleanup
    // ============================================
    let _ = fs::remove_file(temp_input_path);
    let _ = fs::remove_file(temp_output_path);
    let _ = fs::remove_file(temp_bad_input_path);
    let _ = fs::remove_file(temp_bad_output_path);
}

#[test]
fn test_agy_ct_package_compress_execution() {
    use agy7rust::codec::package::verify_package_value;
    use std::fs;
    use std::process::Command;

    let temp_dir = std::env::temp_dir();
    let temp_output_path = temp_dir.join("test_compressed.spkg");
    let temp_bad_input_path = temp_dir.join("test_compress_bad_input.json");
    let temp_bad_output_path = temp_dir.join("test_compress_bad_output.spkg");

    let _ = fs::remove_file(&temp_output_path);
    let _ = fs::remove_file(&temp_bad_output_path);

    // Ensure no residual temp file exists
    let expected_tmp_success = temp_dir.join(".test_compressed.spkg.tmp");
    let expected_tmp_failure = temp_dir.join(".test_compress_bad_output.spkg.tmp");
    let _ = fs::remove_file(&expected_tmp_success);
    let _ = fs::remove_file(&expected_tmp_failure);

    // ============================================
    // 1. Success Test: Valid JSON input
    // ============================================
    let output_success = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "compress",
            "-i",
            "../examples/spark/extraction.json",
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success.status.success());
    assert!(temp_output_path.exists());
    assert!(
        !expected_tmp_success.exists(),
        "Temporary write file must not persist on success"
    );

    let package_content = fs::read_to_string(&temp_output_path).unwrap();
    assert!(!package_content.is_empty());

    let package_value: serde_json::Value = serde_json::from_str(&package_content).unwrap();
    assert!(
        verify_package_value(&package_value).is_ok(),
        "Generated package must verify successfully"
    );

    // ============================================
    // 2. Failure Test 1: Missing input
    // ============================================
    let non_existent_input = temp_dir.join("test_compress_non_existent.json");
    let _ = fs::remove_file(&non_existent_input);

    let output_failure_missing = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "compress",
            "-i",
            non_existent_input.to_str().unwrap(),
            "-o",
            temp_bad_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_missing.status.success());
    assert!(!temp_bad_output_path.exists());
    assert!(
        !expected_tmp_failure.exists(),
        "Temporary write file must not persist on missing input failure"
    );

    // ============================================
    // 3. Failure Test 2: Corrupted JSON input
    // ============================================
    fs::write(&temp_bad_input_path, "{ \"invalid\": ").unwrap();

    let output_failure_corrupt = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "compress",
            "-i",
            temp_bad_input_path.to_str().unwrap(),
            "-o",
            temp_bad_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_corrupt.status.success());
    assert!(!temp_bad_output_path.exists());
    assert!(
        !expected_tmp_failure.exists(),
        "Temporary write file must not persist on corrupt JSON failure"
    );

    // ============================================
    // 4. Cleanup
    // ============================================
    let _ = fs::remove_file(temp_output_path);
    let _ = fs::remove_file(temp_bad_input_path);
    let _ = fs::remove_file(temp_bad_output_path);
}

#[test]
fn test_agy_ct_package_adversarial_execution() {
    use serde_json::json;
    use std::fs;
    use std::process::Command;

    let temp_dir = std::env::temp_dir();
    let temp_bad_input_path = temp_dir.join("test_adversarial_bad_input.json");
    let temp_missing_fields_path = temp_dir.join("test_adversarial_missing_fields.json");

    // ============================================
    // 1. Success Test: Valid raw input JSON trace
    // ============================================
    let output_success = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "adversarial",
            "-i",
            "../examples/spark/extraction.json",
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success.status.success());
    let stdout_str = String::from_utf8_lossy(&output_success.stdout);
    assert!(stdout_str.contains("adversarial: 5/5 detected"));

    // ============================================
    // 2. Failure Test 1: Missing input file
    // ============================================
    let non_existent_input = temp_dir.join("test_adversarial_non_existent.json");
    let _ = fs::remove_file(&non_existent_input);

    let output_failure_missing = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "adversarial",
            "-i",
            non_existent_input.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_missing.status.success());

    // ============================================
    // 3. Failure Test 2: Corrupted JSON input
    // ============================================
    fs::write(&temp_bad_input_path, "{ \"invalid\": ").unwrap();

    let output_failure_corrupt = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "adversarial",
            "-i",
            temp_bad_input_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_corrupt.status.success());

    // ============================================
    // 4. Failure Test 3: Missing Required Fields (missing parcel_id)
    // ============================================
    let bad_ctx_missing_fields = json!({
        "case_id": "test-123",
        "extraction": {
            "fields": {
                // missing parcel_id and decision_recommendation
            }
        }
    });
    fs::write(
        &temp_missing_fields_path,
        serde_json::to_string(&bad_ctx_missing_fields).unwrap(),
    )
    .unwrap();

    let output_failure_fields = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "package",
            "adversarial",
            "-i",
            temp_missing_fields_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_fields.status.success());

    // ============================================
    // 5. Cleanup
    // ============================================
    let _ = fs::remove_file(temp_bad_input_path);
    let _ = fs::remove_file(temp_missing_fields_path);
}

#[test]
fn test_agy_ct_report_export_execution() {
    use serde_json::json;
    use std::fs;
    use std::process::Command;

    let pid = std::process::id();
    let time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let suffix = format!("{}_{}", pid, time);

    let temp_dir = std::env::temp_dir();
    let temp_input_path = temp_dir.join(format!("test_report_input_{}.json", suffix));
    let temp_output_path = temp_dir.join(format!("test_report_output_{}.md", suffix));
    let temp_bad_input_path = temp_dir.join(format!("test_report_bad_input_{}.json", suffix));

    // Clean up from previous runs
    let _ = fs::remove_file(&temp_input_path);
    let _ = fs::remove_file(&temp_output_path);
    let _ = fs::remove_file(&temp_bad_input_path);

    // ============================================
    // 1. Success Test: Valid JSON report
    // ============================================
    let mock_report = json!({
        "tool": "agy-ct",
        "project": "CompText-Sparkctl",
        "phase": "6E",
        "result": "PASS",
        "stages": [
            {
                "index": 1,
                "name": "workspace doctor",
                "status": "PASS"
            }
        ]
    });
    fs::write(
        &temp_input_path,
        serde_json::to_string_pretty(&mock_report).unwrap(),
    )
    .unwrap();

    let output_success = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "report",
            "export",
            "-i",
            temp_input_path.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success.status.success());
    assert!(temp_output_path.exists());
    let md_content = fs::read_to_string(&temp_output_path).unwrap();
    assert!(!md_content.is_empty());
    assert!(md_content.contains("# CompText-Sparkctl Execution Report"));
    assert!(md_content.contains("workspace doctor"));
    assert!(md_content.contains("PASS"));

    // Clean up output
    let _ = fs::remove_file(&temp_output_path);

    // ============================================
    // 2. Failure Test 1: Missing input file
    // ============================================
    let non_existent_input = temp_dir.join(format!("test_report_non_existent_{}.json", suffix));
    let _ = fs::remove_file(&non_existent_input);

    let output_failure_missing = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "report",
            "export",
            "-i",
            non_existent_input.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_missing.status.success());
    assert!(!temp_output_path.exists());

    // ============================================
    // 3. Failure Test 2: Corrupted JSON input
    // ============================================
    fs::write(&temp_bad_input_path, "{ \"invalid\": ").unwrap();

    let output_failure_corrupt = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "report",
            "export",
            "-i",
            temp_bad_input_path.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_corrupt.status.success());
    assert!(!temp_output_path.exists());

    // Clean up temporary files
    let _ = fs::remove_file(&temp_input_path);
    let _ = fs::remove_file(&temp_bad_input_path);
    let _ = fs::remove_file(&temp_output_path);
}

#[test]
fn test_agy_ct_notebook_bundle_execution() {
    use serde_json::json;
    use std::fs;
    use std::process::Command;

    let pid = std::process::id();
    let time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let suffix = format!("{}_{}", pid, time);

    let temp_dir = std::env::temp_dir();
    let temp_context_path = temp_dir.join(format!("test_context_{}.json", suffix));
    let temp_render_path = temp_dir.join(format!("test_render_{}.txt", suffix));
    let temp_output_path = temp_dir.join(format!("test_bundle_{}.ipynb", suffix));
    let temp_output_no_render_path =
        temp_dir.join(format!("test_bundle_no_render_{}.ipynb", suffix));
    let temp_bad_context_path = temp_dir.join(format!("test_bad_context_{}.json", suffix));

    // Clean up from previous runs
    let _ = fs::remove_file(&temp_context_path);
    let _ = fs::remove_file(&temp_render_path);
    let _ = fs::remove_file(&temp_output_path);
    let _ = fs::remove_file(&temp_output_no_render_path);
    let _ = fs::remove_file(&temp_bad_context_path);

    // Mock operational context JSON
    let mock_context = json!({
        "context_id": "mock-ctx-123",
        "source_package_hash": "abc123hash",
        "schema_name": "genehmigung_v1",
        "schema_version": 1,
        "required_field_paths": ["field_a"],
        "satisfied_field_paths": ["field_a"],
        "missing_field_paths": [],
        "constraints": [],
        "required_order": [],
        "dependency_edges": [],
        "blockers": [],
        "recovery_paths": [],
        "validation": {
            "valid": true,
            "failure_labels": [],
            "issues": []
        },
        "non_claims": ["No production claim"]
    });

    fs::write(
        &temp_context_path,
        serde_json::to_string_pretty(&mock_context).unwrap(),
    )
    .unwrap();

    let mock_render = "This is a mock render text summary.";
    fs::write(&temp_render_path, mock_render).unwrap();

    // ============================================
    // 1. Success Test: With Render Output
    // ============================================
    let output_success = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "notebook",
            "bundle",
            "-c",
            temp_context_path.to_str().unwrap(),
            "-r",
            temp_render_path.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success.status.success());
    assert!(temp_output_path.exists());
    let ipynb_content = fs::read_to_string(&temp_output_path).unwrap();
    assert!(!ipynb_content.is_empty());

    let ipynb_json: serde_json::Value = serde_json::from_str(&ipynb_content).unwrap();
    assert_eq!(ipynb_json["nbformat"].as_u64(), Some(4));
    let cells = ipynb_json["cells"]
        .as_array()
        .expect("cells should be an array");
    assert!(!cells.is_empty());

    // Check cells content
    let cells_str = ipynb_content.to_string();
    assert!(cells_str.contains("CompText-Sparkctl Operational Notebook Bundle"));
    assert!(cells_str.contains("mock-ctx-123"));
    assert!(cells_str.contains("This is a mock render text summary."));

    // ============================================
    // 2. Success Test: Without Render Output
    // ============================================
    let output_success_no_render = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "notebook",
            "bundle",
            "-c",
            temp_context_path.to_str().unwrap(),
            "-o",
            temp_output_no_render_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(output_success_no_render.status.success());
    assert!(temp_output_no_render_path.exists());
    let ipynb_no_render_content = fs::read_to_string(&temp_output_no_render_path).unwrap();
    assert!(!ipynb_no_render_content.is_empty());
    assert!(ipynb_no_render_content.contains("CompText-Sparkctl Operational Notebook Bundle"));
    assert!(!ipynb_no_render_content.contains("This is a mock render text summary."));

    // ============================================
    // 3. Failure Test 1: Missing input file
    // ============================================
    let non_existent_input = temp_dir.join(format!("test_context_non_existent_{}.json", suffix));
    let _ = fs::remove_file(&non_existent_input);

    let output_failure_missing = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "notebook",
            "bundle",
            "-c",
            non_existent_input.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_missing.status.success());

    // ============================================
    // 4. Failure Test 2: Corrupted JSON input
    // ============================================
    fs::write(&temp_bad_context_path, "{ \"invalid\": ").unwrap();

    let output_failure_corrupt = Command::new("cargo")
        .args([
            "run",
            "--bin",
            "agy-ct",
            "--",
            "notebook",
            "bundle",
            "-c",
            temp_bad_context_path.to_str().unwrap(),
            "-o",
            temp_output_path.to_str().unwrap(),
        ])
        .output()
        .expect("failed to execute cargo run");

    assert!(!output_failure_corrupt.status.success());

    // ============================================
    // 5. Cleanup
    // ============================================
    let _ = fs::remove_file(&temp_context_path);
    let _ = fs::remove_file(&temp_render_path);
    let _ = fs::remove_file(&temp_output_path);
    let _ = fs::remove_file(&temp_output_no_render_path);
}

#[test]
fn test_plain_output_path_no_parent() {
    use serde_json::json;
    use std::env;
    use std::fs;

    let original_dir = env::current_dir().unwrap();
    let temp_dir = std::env::temp_dir();

    let pid = std::process::id();
    let time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let subdir_name = format!("test_plain_dir_{}_{}", pid, time);
    let run_dir = temp_dir.join(&subdir_name);
    fs::create_dir_all(&run_dir).unwrap();

    env::set_current_dir(&run_dir).unwrap();

    // Mock files
    let mock_report = json!({
        "tool": "agy-ct",
        "project": "CompText-Sparkctl",
        "phase": "6E",
        "result": "PASS"
    });
    fs::write(
        "mock_report.json",
        serde_json::to_string(&mock_report).unwrap(),
    )
    .unwrap();

    let mock_context = json!({
        "context_id": "mock-ctx-123",
        "source_package_hash": "abc123hash",
        "schema_name": "genehmigung_v1",
        "schema_version": 1,
        "required_field_paths": ["field_a"],
        "satisfied_field_paths": ["field_a"],
        "missing_field_paths": [],
        "constraints": [],
        "required_order": [],
        "dependency_edges": [],
        "blockers": [],
        "recovery_paths": [],
        "validation": {
            "valid": true,
            "failure_labels": [],
            "issues": []
        },
        "non_claims": []
    });
    fs::write(
        "mock_context.json",
        serde_json::to_string(&mock_context).unwrap(),
    )
    .unwrap();

    // 1. Report export test
    let res_report = agy7rust::commands::report_export::run("mock_report.json", "report.md");
    assert!(
        res_report.is_ok(),
        "Report export failed: {:?}",
        res_report.err()
    );
    assert!(
        fs::metadata("report.md").is_ok(),
        "report.md does not exist"
    );
    assert!(
        fs::metadata("report.md").unwrap().len() > 0,
        "report.md is empty"
    );

    // 2. Notebook bundle test
    let res_bundle =
        agy7rust::commands::notebook_bundle::run("mock_context.json", None, "bundle.ipynb");
    assert!(
        res_bundle.is_ok(),
        "Notebook bundle failed: {:?}",
        res_bundle.err()
    );
    assert!(
        fs::metadata("bundle.ipynb").is_ok(),
        "bundle.ipynb does not exist"
    );
    assert!(
        fs::metadata("bundle.ipynb").unwrap().len() > 0,
        "bundle.ipynb is empty"
    );

    // Restore original current dir and cleanup
    env::set_current_dir(&original_dir).unwrap();
    let _ = fs::remove_dir_all(&run_dir);
}
