//! Internal strict BLAKE3 hex utilities.
//!
//! Central source of truth for 64-character lowercase hex validation
//! (the strictest level used for manifest/ledger hashes and Merkle proofs).
//!
//! These are crate-internal only (`pub(crate)`). Public API surface is unchanged.

pub(crate) type Hash32 = [u8; 32];

const BLAKE3_HEX_LEN: usize = 64;

/// Returns true only for exactly 64 lowercase hex digits (a-f0-9, no uppercase).
pub(crate) fn is_valid_blake3_hex(s: &str) -> bool {
    s.len() == BLAKE3_HEX_LEN
        && s.chars().all(|c| c.is_ascii_hexdigit())
        && !s.chars().any(|c| c.is_ascii_uppercase())
}

/// Decode a labeled 64-char lowercase hex string to a 32-byte array.
/// Errors with clear message on any deviation (length, case, content).
pub(crate) fn decode_blake3_hex(label: &str, s: &str) -> anyhow::Result<Hash32> {
    if !is_valid_blake3_hex(s) {
        return Err(anyhow::anyhow!(
            "{} must be lowercase BLAKE3 hex (64 chars)",
            label
        ));
    }
    let bytes = hex::decode(s).map_err(|e| anyhow::anyhow!("invalid hex for {}: {}", label, e))?;
    // Length is guaranteed 32 by the 64-hex check above
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&bytes);
    Ok(arr)
}

/// Lenient Option version used by internal leaf collectors that tolerate
/// synthetic test data. Still enforces the strict lowercase-64 rule.
pub(crate) fn try_decode_blake3_hex(s: &str) -> Option<Hash32> {
    if !is_valid_blake3_hex(s) {
        return None;
    }
    hex::decode(s).ok().and_then(|b| {
        if b.len() == 32 {
            let mut a = [0u8; 32];
            a.copy_from_slice(&b);
            Some(a)
        } else {
            None
        }
    })
}

/// Encode a 32-byte hash as lowercase hex (consistent with hex::encode).
pub(crate) fn encode_hex_32(h: &Hash32) -> String {
    hex::encode(h)
}
