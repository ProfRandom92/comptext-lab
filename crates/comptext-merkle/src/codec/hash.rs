use blake3;

pub fn blake3_hex(input: impl AsRef<[u8]>) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(input.as_ref());
    hex::encode(hasher.finalize().as_bytes())
}

// Alias for backward compatibility (will be replaced over time)
pub fn sha256_hex(input: impl AsRef<[u8]>) -> String {
    blake3_hex(input)
}
