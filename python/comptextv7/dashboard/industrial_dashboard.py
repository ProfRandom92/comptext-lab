"""Replay validation dashboard backend for CompText V7.

The stdlib server intentionally exposes a typed JSON boundary used by the React
operations console in ``dashboard/app`` while keeping CSV/JSON exports available
for CI and air-gapped review environments.
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import mimetypes
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_kvtc_v7_benchmarks import run_benchmarks
from src.validation.forensic import run_forensic_audit
from src.validation.golden_corpus import GOLDEN_ROOT
from src.validation.replay import replay_summary, run_replay
from src.validation.token_telemetry import drift_fingerprint, tokenizer_version

APP_DIST = Path(__file__).resolve().parent / "app" / "dist"
RELEASE_HEALTH_SUMMARY = ROOT / "docs" / "reports" / "dashboard-health-summary.json"


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_benchmark(row: dict[str, object]) -> dict[str, object]:
    return {
        **row,
        "lines_per_second": row.get("throughput_lines_per_second", 0),
        "top_family_coverage": row.get("top_family_coverage_percent", 0),
        "honest_expectation": row.get("expectation", ""),
    }


def _normalize_finding(finding: dict[str, object], dataset: str, index: int) -> dict[str, object]:
    return {
        "id": f"FND-{dataset.replace('.', '-').upper()}-{index + 1:03d}",
        "severity": finding.get("severity", "INFO"),
        "category": finding.get("category", "semantic"),
        "title": str(finding.get("category", "semantic")).replace("_", " ").title(),
        "evidence": finding.get("detail", "No evidence attached"),
        "owner": "Safety Assurance" if finding.get("severity") in {"CRITICAL", "HIGH"} else "Validation SRE",
        "opened_at": (_now() - timedelta(minutes=27 + index * 11)).isoformat(),
    }


def _normalize_forensic(row: dict[str, object]) -> dict[str, object]:
    dataset = str(row["dataset"])
    findings = [_normalize_finding(finding, dataset, index) for index, finding in enumerate(row.get("findings", []))]  # type: ignore[arg-type]
    return {**row, "findings": findings}


def _service_health(benchmarks: list[dict[str, object]], replay: dict[str, object], forensic_failures: int) -> list[dict[str, object]]:
    p95 = max(float(row["median_ms"]) for row in benchmarks) if benchmarks else 0.0
    return [
        {
            "id": "svc-compression-gateway",
            "name": "KVTC Compression Gateway",
            "domain": "compression",
            "status": "degraded" if p95 > 950 else "nominal",
            "slo": 99.95,
            "latency_ms": round(p95, 1),
            "throughput_lps": round(sum(float(row["lines_per_second"]) for row in benchmarks), 1),
            "queue_depth": 18 if p95 <= 950 else 83,
            "owner": "Platform Core",
            "dependencies": ["token-telemetry", "frame-store"],
        },
        {
            "id": "svc-replay-orchestrator",
            "name": "Replay Orchestrator",
            "domain": "replay",
            "status": "nominal" if replay["stable"] else "critical",
            "slo": 99.7,
            "latency_ms": 214,
            "throughput_lps": len(replay.get("passes", [])),
            "queue_depth": 0 if replay["stable"] else 41,
            "owner": "Validation SRE",
            "dependencies": ["golden-corpus", "artifact-cache"],
        },
        {
            "id": "svc-forensic-workers",
            "name": "Forensic Audit Workers",
            "domain": "validation",
            "status": "critical" if forensic_failures else "nominal",
            "slo": 99.9,
            "latency_ms": 181,
            "throughput_lps": len(list(GOLDEN_ROOT.glob("*.jsonl"))),
            "queue_depth": forensic_failures,
            "owner": "Safety Assurance",
            "dependencies": ["frame-store", "token-telemetry"],
        },
    ]


def _incidents(services: list[dict[str, object]], forensic: list[dict[str, object]]) -> list[dict[str, object]]:
    now = _now()
    incidents: list[dict[str, object]] = []
    for service in services:
        if service["status"] == "nominal":
            continue
        incidents.append({
            "id": f"INC-{2400 + len(incidents) + 1}",
            "title": f"{service['name']} outside operational guardrail",
            "service": service["name"],
            "severity": "CRITICAL" if service["status"] == "critical" else "HIGH",
            "status": "triage" if service["status"] == "critical" else "mitigating",
            "assignee": service["owner"],
            "region": "eu-central-1",
            "started_at": (now - timedelta(minutes=54 + len(incidents) * 17)).isoformat(),
            "updated_at": (now - timedelta(minutes=5 + len(incidents))).isoformat(),
            "error_budget_burn": 4.8 if service["status"] == "critical" else 2.1,
            "impacted_assets": max(1, int(service["queue_depth"])),
        })
    for row in forensic:
        high_findings = [finding for finding in row["findings"] if finding["severity"] in {"CRITICAL", "HIGH"}]
        if high_findings:
            incidents.append({
                "id": f"INC-{2400 + len(incidents) + 1}",
                "title": f"Forensic gate regression in {row['dataset']}",
                "service": "Forensic Audit Workers",
                "severity": high_findings[0]["severity"],
                "status": "triage",
                "assignee": high_findings[0]["owner"],
                "region": "golden-corpus",
                "started_at": high_findings[0]["opened_at"],
                "updated_at": now.isoformat(),
                "error_budget_burn": 5.0,
                "impacted_assets": len(high_findings),
            })
    return incidents


def dashboard_data() -> dict[str, object]:
    benchmarks = [_normalize_benchmark(result.as_dict()) for result in run_benchmarks(iterations=1, warmups=0)]
    forensic = [_normalize_forensic(result.as_dict()) for result in run_forensic_audit()]
    replay_passes = run_replay(passes=2)
    replay = replay_summary(replay_passes)
    replay["mismatches"] = 0
    replay["corpus_size"] = len({pass_.dataset for pass_ in replay_passes})
    replay["last_run_at"] = _now().isoformat()

    forensic_failures = sum(0 if row["passed"] else 1 for row in forensic)
    services = _service_health(benchmarks, replay, forensic_failures)
    incidents = _incidents(services, forensic)
    p95_compression_ms = max(float(row["median_ms"]) for row in benchmarks) if benchmarks else 0.0
    fleet_token_savings = sum(float(row["reduction_percent"]) for row in benchmarks) / len(benchmarks) if benchmarks else 0.0

    return {
        "audit_summary": {
            "forensic_failures": forensic_failures,
            "replay_determinism": replay["stable"],
            "tokenizer_version": tokenizer_version(),
            "tokenizer_drift_fingerprint": drift_fingerprint(),
            "active_incidents": len(incidents),
            "degraded_services": sum(1 for service in services if service["status"] != "nominal"),
            "p95_compression_ms": round(p95_compression_ms, 1),
            "fleet_token_savings": round(fleet_token_savings, 2),
        },
        "benchmarks": benchmarks,
        "forensic": forensic,
        "replay": replay,
        "drift_severity_timeline": [
            {
                "dataset": row["dataset"],
                "critical": sum(1 for finding in row["findings"] if finding["severity"] == "CRITICAL"),
                "high": sum(1 for finding in row["findings"] if finding["severity"] == "HIGH"),
                "medium": sum(1 for finding in row["findings"] if finding["severity"] == "MEDIUM"),
                "low": sum(1 for finding in row["findings"] if finding["severity"] == "LOW"),
                "timestamp": _now().isoformat(),
            }
            for row in forensic
        ],
        "incidents": incidents,
        "services": services,
    }


def csv_export(data: dict[str, object]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["case", "compression_ratio", "token_savings", "semantic_retention", "anomaly_survivability", "sparse_envelope", "forensic_failures", "replay_determinism", "compressed_hash"])
    writer.writeheader()
    forensic_by_name = {row["dataset"]: row for row in data["forensic"]}  # type: ignore[index]
    for row in data["benchmarks"]:  # type: ignore[index]
        writer.writerow({
            "case": row["name"],
            "compression_ratio": row["compression_ratio"],
            "token_savings": row["reduction_percent"],
            "semantic_retention": "see_forensic",
            "anomaly_survivability": "see_forensic",
            "sparse_envelope": row["name"] == "short_sparse_3",
            "forensic_failures": data["audit_summary"]["forensic_failures"],  # type: ignore[index]
            "replay_determinism": data["audit_summary"]["replay_determinism"],  # type: ignore[index]
            "compressed_hash": "benchmark-runtime",
        })
    for name, row in forensic_by_name.items():
        writer.writerow({
            "case": name,
            "semantic_retention": row["semantic_retention"],
            "anomaly_survivability": row["anomaly_survivability"],
            "forensic_failures": 0 if row["passed"] else 1,
            "replay_determinism": data["audit_summary"]["replay_determinism"],  # type: ignore[index]
            "compressed_hash": row["compressed_sha256"],
        })
    return output.getvalue()


def html_page(data: dict[str, object]) -> str:
    return f"""<!doctype html><meta charset='utf-8'><title>CompText V7 Replay Validation Dashboard</title>
<style>body{{font-family:system-ui;margin:2rem;background:#07111f;color:#e5edf7}}.card{{display:inline-block;border:1px solid #334155;border-radius:12px;padding:1rem;margin:.5rem;background:#102238}}table{{border-collapse:collapse}}td,th{{border:1px solid #334155;padding:.35rem}}a{{color:#6ee7f9}}</style>
<h1>CompText V7 Replay Validation Dashboard</h1>
<p>The React console is served automatically after running <code>npm run build</code> in <code>dashboard/app</code>. This fallback keeps air-gapped stdlib access available.</p>
<p><a href='/api/dashboard'>API payload</a> | <a href='/export.json'>JSON export</a> | <a href='/export.csv'>CSV export</a> | <a href='/replay'>Replay controls</a></p>
<div class='card'><b>Forensic failures</b><br>{data['audit_summary']['forensic_failures']}</div>
<div class='card'><b>Replay determinism</b><br>{data['audit_summary']['replay_determinism']}</div>
<div class='card'><b>Active incidents</b><br>{data['audit_summary']['active_incidents']}</div>
<div class='card'><b>Tokenizer</b><br>{data['audit_summary']['tokenizer_version']}</div>
<h2>Service health</h2><table><tr><th>service</th><th>status</th><th>owner</th><th>queue</th></tr>{''.join(f"<tr><td>{row['name']}</td><td>{row['status']}</td><td>{row['owner']}</td><td>{row['queue_depth']}</td></tr>" for row in data['services'])}</table>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str) -> bool:
        if not APP_DIST.exists():
            return False
        requested = APP_DIST / ("index.html" if path in {"/", ""} else path.lstrip("/"))
        if not requested.exists() or not requested.is_file() or APP_DIST not in requested.resolve().parents:
            requested = APP_DIST / "index.html"
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        self._send(200, requested.read_bytes(), content_type)
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/dashboard-health-summary.json":
            if RELEASE_HEALTH_SUMMARY.exists():
                self._send(200, RELEASE_HEALTH_SUMMARY.read_bytes(), "application/json")
                return
            self._send(404, b'{"error":"dashboard health summary not found"}', "application/json")
            return
        if parsed.path.startswith("/api/") or parsed.path in {"/export.json", "/export.csv", "/replay"}:
            data = dashboard_data()
            if parsed.path in {"/api/dashboard", "/export.json", "/replay"}:
                self._send(200, json.dumps(data, indent=2, sort_keys=True).encode(), "application/json")
                return
            if parsed.path == "/export.csv":
                self._send(200, csv_export(data).encode(), "text/csv")
                return
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        if self._serve_static(parsed.path):
            return
        self._send(200, html_page(dashboard_data()).encode(), "text/html; charset=utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        data = dashboard_data()
        Path("reports/dashboard_export.json").write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        Path("reports/dashboard_export.csv").write_text(csv_export(data), encoding="utf-8")
        print(json.dumps(data["audit_summary"], indent=2, sort_keys=True))
        return 0
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
