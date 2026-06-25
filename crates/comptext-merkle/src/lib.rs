#![deny(unsafe_code)]

pub mod codec;
pub mod commands;
pub mod context;
pub mod dpl_ingest;
pub mod error;
pub mod evidence;

pub use codec::hash::sha256_hex;
pub use codec::merkle::{
    proof_from_hex, proof_to_hex, verify_proof, verify_proof_hash, Hash, MerkleProof,
    MerkleProofHex, MerkleTree,
};
pub use codec::package::{
    build_package_from_value, build_spark_evidence_packet_envelope, canonical_json,
    collect_field_paths, extract_commitment_tokens, generate_ledger_merkle_proof,
    generate_manifest_merkle_proof, get_value_by_path, replay_package_value, sort_json_value,
    validate_pdf_extraction_contract_value, validate_schema,
    validate_spark_evidence_packet_envelope, validate_spark_evidence_packet_value,
    verify_ledger_merkle_proof, verify_manifest_merkle_proof, verify_package_value,
    ArtifactManifestEntry, ClaimHygiene, HumanReviewDecision, PdfExtractedFields,
    PdfExtractionDocument, PdfExtractionFigure, PdfExtractionPage, PdfExtractionTable,
    PdfExtractionToolMetadata, PdfExtractionValidation, PolicyResult, ProviderBoundaryStatus,
    SparkEvidencePacketEnvelope, SparkEvidencePacketPreimage,
};
