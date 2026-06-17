#!/usr/bin/env bash
set -euo pipefail

# Navigate to crate directory
cd "$(dirname "$0")"

echo "=== Building agy7rust CLI ==="
cargo build --quiet

echo "=== Creating Artifacts Directory ==="
mkdir -p ../artifacts/spark

echo "=== Running 04: Compress ==="
cargo run --quiet -- compress -i ../examples/spark/extraction.json -o ../artifacts/spark/extraction.spkg
echo "Deterministic package created successfully at: artifacts/spark/extraction.spkg"

echo "=== Running 05: Inspect without Payload Leak ==="
cargo run --quiet -- inspect -i ../artifacts/spark/extraction.spkg

echo "=== Running 06: Verify Hash Chain ==="
cargo run --quiet -- verify -i ../artifacts/spark/extraction.spkg

echo "=== Running 07: Replay Canonical JSON ==="
cargo run --quiet -- replay -i ../artifacts/spark/extraction.spkg

echo "=== Running 08: Adversarial Suite ==="
cargo run --quiet -- adversarial -i ../examples/spark/extraction.json

echo "=== Demo completed successfully ==="
