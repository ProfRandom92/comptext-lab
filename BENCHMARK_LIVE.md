# Challenge 3 „Safe and Stable!“ — Automated Benchmark Report

**Datum:** 2026-06-19 18:57
**Worktree:** `comptext-lab-feature-merkle`
**Runner:** `cargo run --release --bin spark-bench`

---

## Benchmark 1 — Evidence Overhead (Challenge 3)

**Baseline (fest):** Docling `4.230s` · LLM `4.750s` · Summe `8.980s`
**Gemessen:** `spark-evidence-demo` → `426.48 ms` (PASS)
**Overhead vs. Baseline:** `4.75%` der SPARK-Pipeline-Zeit

```text
Docling (baseline)     ■■■■■■■■■■■■■■■■■■■ 4.230s
LLM (baseline)       ■■■■■■■■■■■■■■■■■■■■■ 4.750s
CompText Evidence    ■■ 426.48 ms
```

<details><summary>spark-evidence-demo stdout</summary>

```text
spark-evidence-demo result: PASS
  output: ../../artifacts/spark/evidence-envelope.json
  canonical_hash: 1d0fd3b120d22d48aafd3a471d24d5ffda70b2d724192ab2b8a2b30648dc9c89
```
</details>

## Benchmark 2 — Merkle Skalierung (Challenge 3)

**Befehl:** `cargo test -p agy7rust bench_merkle_various_sizes --release -- --nocapture`
**Laufzeit:** `924.13 ms` · Status: **PASS**

| Leaves | Build Tree | Generate Proof | Verify Proof |
|--------|------------|----------------|--------------|
| 8 | 69.5µs | 20µs | 600ns |
| 64 | 23.4µs | 9.7µs | 800ns |
| 1024 | 338.5µs | 122.6µs | 1.3µs |
| 8192 | 2.8828ms | 1.6083ms | 2µs |

**Interpretation:** Proof-Verifikation skaliert für Artifact-Manifeste (typisch ≪ 1024 Leaves).

## Benchmark 3 — Zero-Trust / Adversarial (Challenge 3)

**Ergebnis:** `PASS — 5/5 detected`
**Laufzeit:** `557.36 ms`

```powershell
Set-Location //?/C:/CompText-SPARK-Sandbox-TESTING/CompText-SPARK-Sandbox/repos/comptext-lab-feature-merkle
cargo run --release --bin agy-ct -- package adversarial -i crates/examples/spark/extraction.json
```

```text
case 01/05 payload field mutation: ok
case 02/05 payload field deletion: ok
case 03/05 payload_sha256 mutation: ok
case 04/05 integrity_hash mutation: ok
case 05/05 tool sequence mutation: ok
adversarial: 5/5 detected
```


---

*Generiert von `spark-bench` — reine stdout-Markdown-Ausgabe für Copy-Paste.*
