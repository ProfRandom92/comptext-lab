$ErrorActionPreference = "Stop"

# Navigate to script directory
Set-Location -Path $PSScriptRoot

Write-Host "=== Building agy7rust CLI ==="
cargo build --quiet

Write-Host "=== Creating Artifacts Directory ==="
New-Item -ItemType Directory -Force -Path "../artifacts/spark" | Out-Null

Write-Host "=== Running 04: Compress ==="
cargo run --quiet -- compress -i ../examples/spark/extraction.json -o ../artifacts/spark/extraction.spkg
Write-Host "Deterministic package created successfully at: artifacts/spark/extraction.spkg"

Write-Host "=== Running 05: Inspect without Payload Leak ==="
cargo run --quiet -- inspect -i ../artifacts/spark/extraction.spkg

Write-Host "=== Running 06: Verify Hash Chain ==="
cargo run --quiet -- verify -i ../artifacts/spark/extraction.spkg

Write-Host "=== Running 07: Replay Canonical JSON ==="
cargo run --quiet -- replay -i ../artifacts/spark/extraction.spkg

Write-Host "=== Running 08: Adversarial Suite ==="
cargo run --quiet -- adversarial -i ../examples/spark/extraction.json

Write-Host "=== Demo completed successfully ==="
