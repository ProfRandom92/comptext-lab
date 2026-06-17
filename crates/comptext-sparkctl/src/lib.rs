#![deny(unsafe_code)]

pub mod codec;
pub mod commands;
pub mod context;
pub mod error;

pub use codec::hash::sha256_hex;
pub use codec::package::{
    build_package_from_value, build_spark_evidence_packet_envelope, canonical_json,
    collect_field_paths, extract_commitment_tokens, get_value_by_path, replay_package_value,
    sort_json_value, validate_pdf_extraction_contract_value, validate_schema,
    validate_spark_evidence_packet_envelope, validate_spark_evidence_packet_value,
    verify_package_value, ArtifactManifestEntry, ClaimHygiene, HumanReviewDecision,
    PdfExtractedFields, PdfExtractionDocument, PdfExtractionFigure, PdfExtractionPage,
    PdfExtractionTable, PdfExtractionToolMetadata, PdfExtractionValidation, PolicyResult,
    ProviderBoundaryStatus, SparkEvidencePacketEnvelope, SparkEvidencePacketPreimage,
};
