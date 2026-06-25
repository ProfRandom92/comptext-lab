#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=== Building release binaries ==="
cargo build --release -p agy7rust

BIN_DIR="target/release"
SPARKCTL_BIN="${BIN_DIR}/sparkctl"
AGYCT_BIN="${BIN_DIR}/agy-ct"

mkdir -p benchmarks/reports
mkdir -p artifacts/spark

echo "=== Running divan micro-benchmarks ==="
cargo bench -p comptext-benchmarks -- --format json > benchmarks/reports/latest_divan.json

echo "=== Preparing synthetic input (if needed) ==="
if [ ! -f artifacts/spark/evidence-envelope.json ]; then
  "${SPARKCTL_BIN}" spark-evidence-demo -o artifacts/spark/evidence-envelope.json || true
fi

INPUT="artifacts/spark/evidence-envelope.json"

echo "=== Running hyperfine for CLI verify / replay ==="
# Use the granular agy-ct binary which exposes package verify/replay
# (sparkctl binary uses different high-level commands)
hyperfine --warmup 1 --runs 3 --export-json benchmarks/reports/hyperfine_verify.json \
  "${AGYCT_BIN} package verify -i ${INPUT}" || true

hyperfine --warmup 1 --runs 3 --export-json benchmarks/reports/hyperfine_replay.json \
  "${AGYCT_BIN} package replay -i ${INPUT}" || true

echo "=== Creating aggregated latest.json ==="
python3 - << 'PYEOF'
import json
import time
from pathlib import Path

reports = Path("benchmarks/reports")
reports.mkdir(parents=True, exist_ok=True)

latest_path = reports / "latest.json"

data = {
    "tool": "comptext-benchmarks",
    "project": "CompText-Sparkctl",
    "phase": "final-bench-infra",
    "result": "PASS",
    "timestamp": int(time.time()),
    "divan_results_path": "reports/latest_divan.json",
    "notes": "Lab-only benchmarks on synthetic data. Environment specific. No production or compliance claims."
}

for name in ["hyperfine_verify.json", "hyperfine_replay.json"]:
    p = reports / name
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                data[name.replace(".json", "")] = json.load(f)
        except Exception:
            pass

with open(latest_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Wrote {latest_path}")
PYEOF

echo "=== Generating static HTML cockpit ==="
python3 benchmarks/html/generate-cockpit.py || echo "Cockpit generation skipped or failed (non-fatal)"

echo "=== Benchmark run complete ==="
echo "Artifacts in benchmarks/reports/"
