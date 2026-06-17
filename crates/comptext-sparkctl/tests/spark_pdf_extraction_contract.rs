use agy7rust::validate_pdf_extraction_contract_value;
use serde_json::Value;
use std::fs;

#[test]
fn test_pdf_extraction_fixture_contract_shape() {
    let fixture = fs::read_to_string("../examples/spark/pdf_extraction_fixture.json")
        .expect("failed to read PDF extraction fixture");
    let value: Value = serde_json::from_str(&fixture).expect("fixture should parse as JSON");
    let validation =
        validate_pdf_extraction_contract_value(&value).expect("fixture contract should validate");

    assert_eq!(value["schema_version"], "PDF-EXTRACTION-V1");
    assert_non_empty_string(&value["source_file"], "source_file");
    assert_eq!(value["tool_metadata"]["converter"], "manual");
    assert_eq!(value["tool_metadata"]["extraction_mode"], "manual_fixture");

    let extracted_fields = &value["extracted_fields"];
    assert_non_empty_string(
        &extracted_fields["procedure_goal"],
        "extracted_fields.procedure_goal",
    );
    assert_non_empty_string(&extracted_fields["authority"], "extracted_fields.authority");
    assert_non_empty_array(
        &extracted_fields["decision_points"],
        "extracted_fields.decision_points",
    );
    assert_non_empty_array(
        &extracted_fields["required_documents"],
        "extracted_fields.required_documents",
    );
    assert_eq!(extracted_fields["review_required"], true);

    let tables = value["tables"]
        .as_array()
        .expect("tables should be an array");
    let first_table = tables.first().expect("fixture should include a table");
    let first_table_rows = first_table["rows"]
        .as_array()
        .expect("first table rows should be an array");
    assert_eq!(first_table_rows.len(), 3);

    assert_eq!(validation.page_count, 2);
    assert_eq!(validation.table_count, 1);
    assert_eq!(validation.first_table_row_count, 3);
    assert_eq!(validation.canonical_hash.len(), 64);
    assert!(!validation.canonical_json.is_empty());
}

#[test]
fn test_pdf_extraction_contract_rejects_wrong_schema_version() {
    let mut value = load_fixture_value();
    value["schema_version"] = Value::String("PDF-EXTRACTION-V0".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "schema_version mismatch");
}

#[test]
fn test_pdf_extraction_contract_rejects_unknown_top_level_field() {
    let mut value = load_fixture_value();
    value
        .as_object_mut()
        .expect("fixture should be an object")
        .insert(
            "unexpected_field".to_string(),
            Value::String("tamper".to_string()),
        );

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert!(err.contains("unknown field `unexpected_field`"));
}

#[test]
fn test_pdf_extraction_contract_rejects_missing_required_top_level_field() {
    let mut value = load_fixture_value();
    value
        .as_object_mut()
        .expect("fixture should be an object")
        .remove("source_file");

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert!(err.contains("missing field `source_file`"));
}

#[test]
fn test_pdf_extraction_contract_rejects_missing_required_extracted_field() {
    let mut value = load_fixture_value();
    value["extracted_fields"]
        .as_object_mut()
        .expect("extracted_fields should be an object")
        .remove("procedure_goal");

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert!(err.contains("missing field `procedure_goal`"));
}

#[test]
fn test_pdf_extraction_contract_rejects_unsupported_converter() {
    let mut value = load_fixture_value();
    value["tool_metadata"]["converter"] = Value::String("unsupported".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "tool_metadata.converter unsupported");
}

#[test]
fn test_pdf_extraction_contract_rejects_unsupported_extraction_mode() {
    let mut value = load_fixture_value();
    value["tool_metadata"]["extraction_mode"] = Value::String("unsupported".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "tool_metadata.extraction_mode unsupported");
}

#[test]
fn test_pdf_extraction_contract_rejects_unsupported_personal_data_risk() {
    let mut value = load_fixture_value();
    value["contains_personal_data_risk"] = Value::String("review_required".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "contains_personal_data_risk unsupported");
}

#[test]
fn test_pdf_extraction_contract_allows_empty_tables() {
    let mut value = load_fixture_value();
    value["tables"] = serde_json::json!([]);

    let validation =
        validate_pdf_extraction_contract_value(&value).expect("empty tables should be allowed");
    assert_eq!(validation.table_count, 0);
    assert_eq!(validation.first_table_row_count, 0);
}

#[test]
fn test_pdf_extraction_contract_rejects_empty_table_row() {
    let mut value = load_fixture_value();
    value["tables"][0]["rows"][0] = serde_json::json!([]);

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "tables.rows row must not be empty");
}

#[test]
fn test_pdf_extraction_contract_rejects_empty_pages() {
    let mut value = load_fixture_value();
    value["pages"] = serde_json::json!([]);

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "missing pages");
}

#[test]
fn test_pdf_extraction_contract_rejects_blank_table_cell() {
    let mut value = load_fixture_value();
    value["tables"][0]["rows"][0][0] = Value::String("   ".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "tables.rows cell must not be empty");
}

#[test]
fn test_pdf_extraction_contract_allows_empty_warnings() {
    let mut value = load_fixture_value();
    value["warnings"] = serde_json::json!([]);

    let validation = validate_pdf_extraction_contract_value(&value);
    assert!(validation.is_ok());
}

#[test]
fn test_pdf_extraction_contract_rejects_blank_warning() {
    let mut value = load_fixture_value();
    value["warnings"] = serde_json::json!(["manual fixture", "   "]);

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "warnings");
}

#[test]
fn test_pdf_extraction_contract_rejects_blank_procedure_goal() {
    let mut value = load_fixture_value();
    value["extracted_fields"]["procedure_goal"] = Value::String("  ".to_string());

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "missing extracted_fields.procedure_goal");
}

#[test]
fn test_pdf_extraction_contract_rejects_empty_decision_points() {
    let mut value = load_fixture_value();
    value["extracted_fields"]["decision_points"] = serde_json::json!([]);

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(err, "extracted_fields.decision_points");
}

#[test]
fn test_pdf_extraction_contract_rejects_review_required_false() {
    let mut value = load_fixture_value();
    value["extracted_fields"]["review_required"] = Value::Bool(false);

    let err = validate_pdf_extraction_contract_value(&value)
        .unwrap_err()
        .to_string();
    assert_eq!(
        err,
        "PDF extraction extracted_fields.review_required must be true"
    );
}

fn assert_non_empty_string(value: &Value, label: &str) {
    assert!(
        value.as_str().is_some_and(|text| !text.trim().is_empty()),
        "{label} should be a non-empty string"
    );
}

fn assert_non_empty_array(value: &Value, label: &str) {
    assert!(
        value.as_array().is_some_and(|items| !items.is_empty()),
        "{label} should be a non-empty array"
    );
}

fn load_fixture_value() -> Value {
    let fixture = fs::read_to_string("../examples/spark/pdf_extraction_fixture.json")
        .expect("failed to read PDF extraction fixture");
    serde_json::from_str(&fixture).expect("fixture should parse as JSON")
}
