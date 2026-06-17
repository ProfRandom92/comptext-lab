use crate::codec::hash::sha256_hex;
use serde::{Deserialize, Serialize};
use serde_json;
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum PolicyResult {
    #[serde(rename = "ALLOW")]
    ALLOW,
    #[serde(rename = "REVIEW_NEEDED")]
    ReviewNeeded,
    #[serde(rename = "BLOCK")]
    BLOCK,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum ProviderBoundaryStatus {
    #[serde(rename = "DEMO")]
    DEMO,
    #[serde(rename = "UNAVAILABLE")]
    UNAVAILABLE,
    #[serde(rename = "AVAILABLE")]
    AVAILABLE,
    #[serde(rename = "BLOCKED_BY_POLICY")]
    BlockedByPolicy,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum HumanReviewDecision {
    #[serde(rename = "PASS")]
    PASS,
    #[serde(rename = "NOTES")]
    NOTES,
    #[serde(rename = "BLOCKED")]
    BLOCKED,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ClaimHygiene {
    pub allowed_claims: Vec<String>,
    pub blocked_claims: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ArtifactManifestEntry {
    pub path: String,
    pub role: String,
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SparkEvidencePacketPreimage {
    pub schema_version: String,
    pub local_id: String,
    pub goal: String,
    pub source_summary: String,
    pub context_pack_summary: String,
    pub policy_result: PolicyResult,
    pub provider_boundary_status: ProviderBoundaryStatus,
    pub untrusted_proposal: String,
    pub human_review_decision: HumanReviewDecision,
    pub claim_hygiene: ClaimHygiene,
    pub artifact_manifest: Vec<ArtifactManifestEntry>,
    pub warnings: Vec<String>,
    pub limitations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SparkEvidencePacketEnvelope {
    #[serde(flatten)]
    pub preimage: SparkEvidencePacketPreimage,
    pub canonical_json: String,
    pub canonical_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PdfExtractionDocument {
    pub schema_version: String,
    pub source_file: String,
    pub source_sha256: Option<String>,
    pub source_url: Option<String>,
    pub license_or_usage_note: Option<String>,
    pub sanitization_status: Option<String>,
    pub contains_personal_data_risk: Option<String>,
    pub document_type: String,
    pub pages: Vec<PdfExtractionPage>,
    pub tables: Vec<PdfExtractionTable>,
    pub figures: Vec<PdfExtractionFigure>,
    pub extracted_fields: PdfExtractedFields,
    pub warnings: Vec<String>,
    pub tool_metadata: PdfExtractionToolMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PdfExtractionPage {
    pub page_number: u64,
    pub text_summary: String,
    pub field_refs: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PdfExtractionTable {
    pub table_id: String,
    pub page_number: u64,
    pub caption: String,
    pub columns: Vec<String>,
    pub rows: Vec<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PdfExtractionFigure {
    pub figure_id: String,
    pub page_number: u64,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PdfExtractedFields {
    pub procedure_goal: String,
    pub authority: String,
    pub decision_points: Vec<String>,
    pub required_documents: Vec<String>,
    pub review_required: bool,
    pub public_sector_context: String,
    #[serde(flatten)]
    pub additional_fields: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PdfExtractionToolMetadata {
    pub converter: String,
    pub converter_version: String,
    pub extraction_mode: String,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PdfExtractionValidation {
    pub canonical_json: String,
    pub canonical_hash: String,
    pub page_count: usize,
    pub table_count: usize,
    pub first_table_row_count: usize,
}

pub fn sort_json_value(value: &serde_json::Value) -> serde_json::Value {
    match value {
        serde_json::Value::Object(map) => {
            let mut sorted_map = serde_json::Map::new();
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for key in keys {
                if let Some(val) = map.get(key) {
                    sorted_map.insert(key.clone(), sort_json_value(val));
                }
            }
            serde_json::Value::Object(sorted_map)
        }
        serde_json::Value::Array(arr) => {
            let sorted_arr: Vec<serde_json::Value> = arr.iter().map(sort_json_value).collect();
            serde_json::Value::Array(sorted_arr)
        }
        other => other.clone(),
    }
}

pub fn canonical_json(value: &serde_json::Value) -> String {
    let sorted = sort_json_value(value);
    serde_json::to_string(&sorted).unwrap_or_default()
}

pub fn build_spark_evidence_packet_envelope(
    preimage: SparkEvidencePacketPreimage,
) -> anyhow::Result<SparkEvidencePacketEnvelope> {
    validate_spark_evidence_preimage(&preimage)?;
    let preimage_value = serde_json::to_value(&preimage)?;
    let canonical = canonical_json(&preimage_value);
    let canonical_hash = sha256_hex(&canonical);

    Ok(SparkEvidencePacketEnvelope {
        preimage,
        canonical_json: canonical,
        canonical_hash,
    })
}

pub fn validate_spark_evidence_packet_envelope(
    envelope: &SparkEvidencePacketEnvelope,
) -> anyhow::Result<()> {
    validate_spark_evidence_preimage(&envelope.preimage)?;
    let preimage_value = serde_json::to_value(&envelope.preimage)?;
    let calculated_canonical_json = canonical_json(&preimage_value);
    if envelope.canonical_json != calculated_canonical_json {
        return Err(anyhow::anyhow!("canonical_json mismatch"));
    }

    let calculated_hash = sha256_hex(&envelope.canonical_json);
    if envelope.canonical_hash != calculated_hash {
        return Err(anyhow::anyhow!("canonical_hash mismatch"));
    }

    Ok(())
}

pub fn validate_spark_evidence_packet_value(value: &serde_json::Value) -> anyhow::Result<()> {
    let envelope: SparkEvidencePacketEnvelope = serde_json::from_value(value.clone())?;
    validate_spark_evidence_packet_envelope(&envelope)
}

pub fn validate_pdf_extraction_contract_value(
    value: &serde_json::Value,
) -> anyhow::Result<PdfExtractionValidation> {
    let document: PdfExtractionDocument = serde_json::from_value(value.clone())?;
    validate_pdf_extraction_document(&document)?;

    let canonical = canonical_json(value);
    let canonical_hash = sha256_hex(&canonical);
    let first_table_row_count = document
        .tables
        .first()
        .map(|table| table.rows.len())
        .unwrap_or(0);

    Ok(PdfExtractionValidation {
        canonical_json: canonical,
        canonical_hash,
        page_count: document.pages.len(),
        table_count: document.tables.len(),
        first_table_row_count,
    })
}

fn validate_pdf_extraction_document(document: &PdfExtractionDocument) -> anyhow::Result<()> {
    require_exact(
        "schema_version",
        &document.schema_version,
        "PDF-EXTRACTION-V1",
    )?;
    require_non_empty("source_file", &document.source_file)?;
    if let Some(risk) = &document.contains_personal_data_risk {
        require_allowed(
            "contains_personal_data_risk",
            risk,
            &["low", "medium", "high", "unknown"],
        )?;
    }
    require_non_empty("document_type", &document.document_type)?;
    require_allowed(
        "tool_metadata.converter",
        &document.tool_metadata.converter,
        &[
            "manual",
            "docling",
            "mineru",
            "marker",
            "pdftotext",
            "other",
        ],
    )?;
    require_non_empty(
        "tool_metadata.converter_version",
        &document.tool_metadata.converter_version,
    )?;
    require_allowed(
        "tool_metadata.extraction_mode",
        &document.tool_metadata.extraction_mode,
        &["synthetic_fixture", "manual_fixture", "external_tool"],
    )?;

    require_non_empty_pages(&document.pages)?;
    validate_tables(&document.tables)?;
    validate_warnings(&document.warnings)?;
    validate_pdf_extracted_fields(&document.extracted_fields)?;

    for figure in &document.figures {
        require_non_empty("figures.figure_id", &figure.figure_id)?;
        require_non_zero("figures.page_number", figure.page_number)?;
        require_non_empty("figures.description", &figure.description)?;
    }

    if let Some(hash) = &document.source_sha256 {
        validate_sha256_hex("source_sha256", hash)?;
    }

    Ok(())
}

fn validate_pdf_extracted_fields(fields: &PdfExtractedFields) -> anyhow::Result<()> {
    require_non_empty("extracted_fields.procedure_goal", &fields.procedure_goal)?;
    require_non_empty("extracted_fields.authority", &fields.authority)?;
    require_non_empty_list("extracted_fields.decision_points", &fields.decision_points)?;
    require_non_empty_list(
        "extracted_fields.required_documents",
        &fields.required_documents,
    )?;
    if !fields.review_required {
        return Err(anyhow::anyhow!(
            "PDF extraction extracted_fields.review_required must be true"
        ));
    }
    require_non_empty(
        "extracted_fields.public_sector_context",
        &fields.public_sector_context,
    )?;

    Ok(())
}

fn require_exact(label: &str, value: &str, expected: &str) -> anyhow::Result<()> {
    if value != expected {
        return Err(anyhow::anyhow!("{} mismatch", label));
    }
    Ok(())
}

fn require_allowed(label: &str, value: &str, allowed: &[&str]) -> anyhow::Result<()> {
    if !allowed.contains(&value) {
        return Err(anyhow::anyhow!("{} unsupported", label));
    }
    Ok(())
}

fn require_non_zero(label: &str, value: u64) -> anyhow::Result<()> {
    if value == 0 {
        return Err(anyhow::anyhow!("{} must be greater than zero", label));
    }
    Ok(())
}

fn validate_sha256_hex(label: &str, value: &str) -> anyhow::Result<()> {
    if value.len() != 64 || !value.chars().all(|ch| ch.is_ascii_hexdigit()) {
        return Err(anyhow::anyhow!("{} must be lowercase SHA-256 hex", label));
    }
    if value.chars().any(|ch| ch.is_ascii_uppercase()) {
        return Err(anyhow::anyhow!("{} must be lowercase SHA-256 hex", label));
    }
    Ok(())
}

fn require_non_empty_pages(pages: &[PdfExtractionPage]) -> anyhow::Result<()> {
    if pages.is_empty() {
        return Err(anyhow::anyhow!("missing pages"));
    }

    for page in pages {
        require_non_zero("pages.page_number", page.page_number)?;
        require_non_empty("pages.text_summary", &page.text_summary)?;
        if let Some(field_refs) = &page.field_refs {
            require_non_empty_list("pages.field_refs", field_refs)?;
        }
    }

    Ok(())
}

fn validate_tables(tables: &[PdfExtractionTable]) -> anyhow::Result<()> {
    for table in tables {
        require_non_empty("tables.table_id", &table.table_id)?;
        require_non_zero("tables.page_number", table.page_number)?;
        require_non_empty("tables.caption", &table.caption)?;
        require_non_empty_list("tables.columns", &table.columns)?;
        if table.rows.is_empty() {
            return Err(anyhow::anyhow!("missing tables.rows"));
        }
        for row in &table.rows {
            if row.is_empty() {
                return Err(anyhow::anyhow!("tables.rows row must not be empty"));
            }
            for cell in row {
                if cell.trim().is_empty() {
                    return Err(anyhow::anyhow!("tables.rows cell must not be empty"));
                }
            }
        }
    }

    Ok(())
}

fn validate_warnings(warnings: &[String]) -> anyhow::Result<()> {
    if warnings.iter().any(|warning| warning.trim().is_empty()) {
        return Err(anyhow::anyhow!("warnings"));
    }

    Ok(())
}

fn validate_spark_evidence_preimage(preimage: &SparkEvidencePacketPreimage) -> anyhow::Result<()> {
    require_non_empty("schema_version", &preimage.schema_version)?;
    if preimage.schema_version != "SPARK-EVIDENCE-PACKET-V1" {
        return Err(anyhow::anyhow!(
            "schema_version mismatch: expected SPARK-EVIDENCE-PACKET-V1"
        ));
    }
    require_non_empty("local_id", &preimage.local_id)?;
    require_non_empty("goal", &preimage.goal)?;
    require_non_empty("source_summary", &preimage.source_summary)?;
    require_non_empty("context_pack_summary", &preimage.context_pack_summary)?;
    require_non_empty("untrusted_proposal", &preimage.untrusted_proposal)?;

    require_non_empty_list(
        "missing or empty claim in claim_hygiene.allowed_claims",
        &preimage.claim_hygiene.allowed_claims,
    )?;
    require_non_empty_list(
        "missing or empty claim in claim_hygiene.blocked_claims",
        &preimage.claim_hygiene.blocked_claims,
    )?;
    if preimage.artifact_manifest.is_empty() {
        return Err(anyhow::anyhow!("missing artifact_manifest"));
    }
    require_non_empty_list("missing or empty warning", &preimage.warnings)?;
    require_non_empty_list("missing or empty limitation", &preimage.limitations)?;

    for entry in &preimage.artifact_manifest {
        require_non_empty("artifact_manifest.path", &entry.path)?;
        require_non_empty("artifact_manifest.role", &entry.role)?;
    }

    Ok(())
}

fn require_non_empty(label: &str, value: &str) -> anyhow::Result<()> {
    if value.trim().is_empty() {
        return Err(anyhow::anyhow!("missing {}", label));
    }
    Ok(())
}

fn require_non_empty_list(label: &str, values: &[String]) -> anyhow::Result<()> {
    if values.is_empty() || values.iter().any(|value| value.trim().is_empty()) {
        return Err(anyhow::anyhow!(label.to_string()));
    }
    Ok(())
}

pub fn collect_field_paths(value: &serde_json::Value) -> Vec<String> {
    let mut paths = Vec::new();
    collect_paths_recursive(value, "$", &mut paths);
    paths
}

fn collect_paths_recursive(value: &serde_json::Value, current_path: &str, paths: &mut Vec<String>) {
    paths.push(current_path.to_string());
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for key in keys {
                let next_path = format!("{}.{}", current_path, key);
                collect_paths_recursive(&map[key], &next_path, paths);
            }
        }
        serde_json::Value::Array(arr) => {
            for (i, val) in arr.iter().enumerate() {
                let next_path = format!("{}[{}]", current_path, i);
                collect_paths_recursive(val, &next_path, paths);
            }
        }
        _ => {}
    }
}

pub fn extract_commitment_tokens(value: &serde_json::Value) -> Vec<String> {
    let mut tokens = Vec::new();
    find_tokens_recursive(value, &mut tokens);
    tokens.sort();
    tokens.dedup();
    tokens
}

fn find_tokens_recursive(value: &serde_json::Value, tokens: &mut Vec<String>) {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for key in keys {
                let child = &map[key];
                if is_target_key(key) {
                    if let Some(s) = get_scalar_string(child) {
                        tokens.push(s);
                    }
                }
                find_tokens_recursive(child, tokens);
            }
        }
        serde_json::Value::Array(arr) => {
            for val in arr {
                find_tokens_recursive(val, tokens);
            }
        }
        _ => {}
    }
}

fn is_target_key(key: &str) -> bool {
    matches!(
        key,
        "case_id"
            | "document_type"
            | "authority"
            | "parcel_id"
            | "procedure_type"
            | "applicant"
            | "decision_recommendation"
    )
}

fn get_scalar_string(value: &serde_json::Value) -> Option<String> {
    match value {
        serde_json::Value::String(s) => Some(s.clone()),
        serde_json::Value::Number(n) => Some(n.to_string()),
        serde_json::Value::Bool(b) => Some(b.to_string()),
        _ => None,
    }
}

pub fn build_package_from_value(value: &serde_json::Value) -> anyhow::Result<serde_json::Value> {
    let payload = value.clone();
    let payload_canonical = canonical_json(&payload);
    let payload_sha256 = sha256_hex(payload_canonical);

    let field_paths = collect_field_paths(&payload);
    let commitment_tokens = extract_commitment_tokens(&payload);

    let mut sidecar = serde_json::json!({
        "schema_version": "KVTC7-SPARK-1",
        "source_type": "spark_extraction_json",
        "payload_sha256": payload_sha256,
        "field_paths": field_paths,
        "commitment_tokens": commitment_tokens,
        "tool_sequence": ["spark.extractor"]
    });

    let sidecar_preimage_canonical = canonical_json(&sidecar);
    let final_state_hash = sha256_hex(sidecar_preimage_canonical);

    if let serde_json::Value::Object(ref mut map) = sidecar {
        map.insert(
            "final_state_hash".to_string(),
            serde_json::Value::String(final_state_hash),
        );
    }

    let mut package = serde_json::json!({
        "schema": "SPARK-V7-PACKAGE",
        "version": 1,
        "payload": payload,
        "sidecar": sidecar
    });

    let package_preimage_canonical = canonical_json(&package);
    let integrity_hash = sha256_hex(package_preimage_canonical);

    if let serde_json::Value::Object(ref mut map) = package {
        map.insert(
            "integrity_hash".to_string(),
            serde_json::Value::String(integrity_hash),
        );
    }

    Ok(package)
}

pub fn verify_package_value(value: &serde_json::Value) -> anyhow::Result<()> {
    use crate::error::SparkError;

    let pkg = value.as_object().ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss(
            "Package is not a JSON object".to_string(),
        ))
    })?;

    let schema = pkg.get("schema").and_then(|v| v.as_str()).ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss(
            "schema mismatch: Missing schema".to_string(),
        ))
    })?;
    if schema != "SPARK-V7-PACKAGE" {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
            "schema mismatch: expected SPARK-V7-PACKAGE, got {}",
            schema
        ))));
    }

    let version = pkg.get("version").and_then(|v| v.as_i64()).ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss(
            "version mismatch: Missing version".to_string(),
        ))
    })?;
    if version != 1 {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
            "version mismatch: expected 1, got {}",
            version
        ))));
    }

    let payload = pkg.get("payload").ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss("Missing payload".to_string()))
    })?;

    let sidecar_val = pkg.get("sidecar").ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss("Missing sidecar".to_string()))
    })?;
    let sidecar = sidecar_val.as_object().ok_or_else(|| {
        anyhow::Error::new(SparkError::EvidenceLoss(
            "sidecar is not a JSON object".to_string(),
        ))
    })?;

    let schema_version = sidecar
        .get("schema_version")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "schema_version mismatch: Missing sidecar schema_version".to_string(),
            ))
        })?;
    if schema_version != "KVTC7-SPARK-1" {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
            "schema_version mismatch: expected KVTC7-SPARK-1, got {}",
            schema_version
        ))));
    }

    let source_type = sidecar
        .get("source_type")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "source_type mismatch: Missing sidecar source_type".to_string(),
            ))
        })?;
    if source_type != "spark_extraction_json" {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
            "source_type mismatch: expected spark_extraction_json, got {}",
            source_type
        ))));
    }

    let payload_canonical = canonical_json(payload);
    let calculated_payload_sha256 = sha256_hex(payload_canonical);

    let expected_payload_sha256 = sidecar
        .get("payload_sha256")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "payload_sha256 mismatch: Missing sidecar payload_sha256".to_string(),
            ))
        })?;
    if calculated_payload_sha256 != expected_payload_sha256 {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(
            "payload_sha256 mismatch".to_string(),
        )));
    }

    let expected_final_state_hash = sidecar
        .get("final_state_hash")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "final_state_hash mismatch: Missing sidecar final_state_hash".to_string(),
            ))
        })?;

    let mut sidecar_preimage = sidecar_val.clone();
    if let serde_json::Value::Object(ref mut map) = sidecar_preimage {
        map.remove("final_state_hash");
    }
    let sidecar_preimage_canonical = canonical_json(&sidecar_preimage);
    let calculated_final_state_hash = sha256_hex(sidecar_preimage_canonical);

    if calculated_final_state_hash != expected_final_state_hash {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(
            "final_state_hash mismatch".to_string(),
        )));
    }

    let expected_integrity_hash = pkg
        .get("integrity_hash")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "integrity_hash mismatch: Missing integrity_hash".to_string(),
            ))
        })?;

    let mut package_preimage = value.clone();
    if let serde_json::Value::Object(ref mut map) = package_preimage {
        map.remove("integrity_hash");
    }
    let package_preimage_canonical = canonical_json(&package_preimage);
    let calculated_integrity_hash = sha256_hex(package_preimage_canonical);

    if calculated_integrity_hash != expected_integrity_hash {
        return Err(anyhow::Error::new(SparkError::ConstraintDrift(
            "integrity_hash mismatch".to_string(),
        )));
    }

    // Optional ledger validation
    if let Some(ledger_val) = pkg.get("ledger") {
        let ledger_arr = ledger_val.as_array().ok_or_else(|| {
            anyhow::Error::new(SparkError::EvidenceLoss(
                "ledger is not an array".to_string(),
            ))
        })?;

        let ledger_root = pkg
            .get("ledger_root")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                anyhow::Error::new(SparkError::EvidenceLoss(
                    "ledger_root is missing".to_string(),
                ))
            })?;

        if ledger_arr.is_empty() {
            return Err(anyhow::Error::new(SparkError::EvidenceLoss(
                "ledger is empty".to_string(),
            )));
        }

        for (idx, entry_val) in ledger_arr.iter().enumerate() {
            let entry = entry_val.as_object().ok_or_else(|| {
                anyhow::Error::new(SparkError::EvidenceLoss(format!(
                    "ledger entry at index {} is not an object",
                    idx
                )))
            })?;

            let _entry_hash = entry
                .get("entry_hash")
                .and_then(|v| v.as_str())
                .ok_or_else(|| {
                    anyhow::Error::new(SparkError::EvidenceLoss(format!(
                        "ledger entry at index {} missing entry_hash",
                        idx
                    )))
                })?;

            let previous_hash = entry
                .get("previous_hash")
                .and_then(|v| v.as_str())
                .ok_or_else(|| {
                    anyhow::Error::new(SparkError::EvidenceLoss(format!(
                        "ledger entry at index {} missing previous_hash",
                        idx
                    )))
                })?;

            if idx > 0 {
                let prev_entry = ledger_arr[idx - 1].as_object().ok_or_else(|| {
                    anyhow::Error::new(SparkError::EvidenceLoss(
                        "Preceding ledger entry is not an object".to_string(),
                    ))
                })?;
                let prev_entry_hash = prev_entry
                    .get("entry_hash")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| {
                        anyhow::Error::new(SparkError::EvidenceLoss(
                            "Preceding ledger entry missing entry_hash".to_string(),
                        ))
                    })?;

                if previous_hash != prev_entry_hash {
                    return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
                        "ledger chaining mismatch: previous_hash '{}' at index {} does not match entry_hash '{}' of preceding entry",
                        previous_hash, idx, prev_entry_hash
                    ))));
                }
            }
        }

        let final_entry = ledger_arr
            .last()
            .ok_or_else(|| {
                anyhow::Error::new(SparkError::EvidenceLoss("ledger is empty".to_string()))
            })?
            .as_object()
            .ok_or_else(|| {
                anyhow::Error::new(SparkError::EvidenceLoss(
                    "Final ledger entry is not an object".to_string(),
                ))
            })?;
        let final_entry_hash = final_entry
            .get("entry_hash")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                anyhow::Error::new(SparkError::EvidenceLoss(
                    "Final ledger entry missing entry_hash".to_string(),
                ))
            })?;

        if ledger_root != final_entry_hash {
            return Err(anyhow::Error::new(SparkError::ConstraintDrift(format!(
                "ledger root anchoring mismatch: expected ledger_root '{}' to match final entry_hash '{}'",
                ledger_root, final_entry_hash
            ))));
        }
    }

    Ok(())
}

pub fn replay_package_value(value: &serde_json::Value) -> anyhow::Result<serde_json::Value> {
    verify_package_value(value)?;

    let sidecar = value
        .get("sidecar")
        .ok_or_else(|| anyhow::anyhow!("Missing sidecar"))?;

    let source_type = sidecar
        .get("source_type")
        .cloned()
        .unwrap_or(serde_json::Value::Null);
    let payload_sha256 = sidecar
        .get("payload_sha256")
        .cloned()
        .unwrap_or(serde_json::Value::Null);
    let tool_sequence = sidecar
        .get("tool_sequence")
        .cloned()
        .unwrap_or(serde_json::Value::Null);
    let commitment_tokens = sidecar
        .get("commitment_tokens")
        .cloned()
        .unwrap_or(serde_json::Value::Null);
    let field_paths = sidecar
        .get("field_paths")
        .cloned()
        .unwrap_or(serde_json::Value::Null);

    let replay = serde_json::json!({
        "schema": "SPARK-V7-REPLAY",
        "source_type": source_type,
        "payload_sha256": payload_sha256,
        "tool_sequence": tool_sequence,
        "commitment_tokens": commitment_tokens,
        "field_paths": field_paths
    });

    Ok(replay)
}

pub fn get_value_by_path(
    value: &serde_json::Value,
    path: &str,
) -> anyhow::Result<serde_json::Value> {
    if !path.starts_with('$') {
        return Err(anyhow::anyhow!("unsupported path syntax"));
    }

    if path.contains('[') || path.contains(']') {
        return Err(anyhow::anyhow!("unsupported path syntax"));
    }

    if path == "$" {
        return Ok(value.clone());
    }

    if !path.starts_with("$.") {
        return Err(anyhow::anyhow!("unsupported path syntax"));
    }

    let parts = path[2..].split('.');
    let mut current = value;

    for part in parts {
        if part.is_empty() {
            return Err(anyhow::anyhow!("unsupported path syntax"));
        }
        if let serde_json::Value::Object(map) = current {
            if let Some(next_val) = map.get(part) {
                current = next_val;
            } else {
                return Err(anyhow::anyhow!("required field missing: {}", path));
            }
        } else {
            return Err(anyhow::anyhow!("required field missing: {}", path));
        }
    }

    Ok(current.clone())
}

pub fn validate_schema(
    input_val: &serde_json::Value,
    schema_val: &serde_json::Value,
) -> anyhow::Result<(String, usize, usize)> {
    let schema_obj = schema_val
        .as_object()
        .ok_or_else(|| anyhow::anyhow!("Schema is not a JSON object"))?;

    let schema = schema_obj
        .get("schema")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("schema mismatch"))?;
    if schema != "SPARK-V7-SCHEMA" {
        return Err(anyhow::anyhow!("schema mismatch"));
    }

    let version = schema_obj
        .get("version")
        .and_then(|v| v.as_i64())
        .ok_or_else(|| anyhow::anyhow!("unsupported schema version"))?;
    if version != 1 {
        return Err(anyhow::anyhow!("unsupported schema version"));
    }

    let name = schema_obj
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("schema name missing"))?
        .to_string();

    let required_paths = schema_obj
        .get("required_field_paths")
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow::anyhow!("Schema missing required_field_paths array"))?;

    for path_value in required_paths {
        let path = path_value
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Required path is not a string"))?;
        let value = get_value_by_path(input_val, path)?;
        match value {
            serde_json::Value::String(text) => {
                if text.trim().is_empty() {
                    return Err(anyhow::anyhow!("required field empty: {}", path));
                }
            }
            serde_json::Value::Number(_) | serde_json::Value::Bool(_) => {}
            _ => return Err(anyhow::anyhow!("required field not scalar: {}", path)),
        }
    }

    Ok((name, required_paths.len(), required_paths.len()))
}
