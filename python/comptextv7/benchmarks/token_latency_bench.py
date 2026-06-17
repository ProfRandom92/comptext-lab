"""Deterministic token and latency benchmark for KVTC-V7.

This script measures the wall-clock latency of the KVTC-V7 compression engine
across various fixtures (papers and agent traces) to provide a clean benchmark
layer. It computes latency per run, per KB, and per 1k tokens.

Output: artifacts/token_latency_results.json
Schema:
{
    "benchmark": "token_latency_bench",
    "timestamp": "ISO-8601",
    "iterations": int,
    "results": [
        {
            "fixture": str,
            "type": "paper" | "agent_trace",
            "tokens_in": int,
            "tokens_compact": int,
            "compression_ratio": float,
            "reduction_percent": float,
            "latency_ms_per_run": float,
            "latency_ms_per_kb": float,
            "latency_ms_per_1k_tokens": float
        },
        ...
    ]
}
"""

import json
import time
import statistics
from pathlib import Path
from datetime import datetime, timezone
from runpy import run_path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_IMPORT_HELPER = _REPO_ROOT / "tests" / "utils" / "_import_root.py"
ensure_repo_root_on_path = run_path(str(_IMPORT_HELPER))["ensure_repo_root_on_path"]
ensure_repo_root_on_path()

from src.core.adaptive_policy import CompressionProfile, ReplayMetrics, get_params, reduction_percent_from_ratio, select_profile
from src.core.kvtc_v7 import KVTCV7Engine
from src.validation.token_telemetry import count_tokens
from tests.utils.paper_replay_runner import PAPER_SPECS, FIXTURE_ROOT as PAPER_FIXTURE_ROOT, build_paper_replay_artifact
from tests.utils.agent_trace_replay_runner import TRACE_SPECS, FIXTURE_ROOT as TRACE_FIXTURE_ROOT, build_agent_trace_replay_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "token_latency_results.json"

def run_benchmark(iterations=20, output_path=None):
    if output_path is None:
        output_path = DEFAULT_ARTIFACT_PATH
    else:
        output_path = Path(output_path)

    engine = KVTCV7Engine()
    results = []

    # Process Papers
    for spec in PAPER_SPECS:
        fixture_path = PAPER_FIXTURE_ROOT / spec["fixture"]
        text = fixture_path.read_text(encoding="utf-8")
        results.append(measure_fixture(engine, text, spec["fixture"], "paper", iterations))

    # Process Agent Traces
    for spec in TRACE_SPECS:
        fixture_path = TRACE_FIXTURE_ROOT / spec["fixture"]
        # Agent trace fixtures are JSON, we want the raw string for token count
        # but the runner usually parses them. For consistency with core.compress(text),
        # we treat the whole JSON as the input text.
        text = fixture_path.read_text(encoding="utf-8")
        results.append(measure_fixture(engine, text, spec["fixture"], "agent_trace", iterations))

    output = {
        "benchmark": "token_latency_bench",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iterations": iterations,
        "results": results
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    return output

def measure_fixture(engine, text, name, fixture_type, iterations):
    input_kb = len(text.encode("utf-8")) / 1024
    tokens_in = count_tokens(text, "cl100k_base").count

    # Warmup
    last_result = engine.compress(text)

    latencies_ns = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        last_result = engine.compress(text)
        latencies_ns.append(time.perf_counter_ns() - start)

    avg_latency_ms = (sum(latencies_ns) / len(latencies_ns)) / 1_000_000 if latencies_ns else 0.0

    tokens_compact = count_tokens(last_result.text, "cl100k_base").count

    return {
        "fixture": name,
        "type": fixture_type,
        "tokens_in": tokens_in,
        "tokens_compact": tokens_compact,
        "compression_ratio": round(tokens_in / tokens_compact, 4) if tokens_compact > 0 else 0,
        "reduction_percent": round((1 - tokens_compact / tokens_in) * 100, 2) if tokens_in > 0 else 0,
        "latency_ms_per_run": round(avg_latency_ms, 4),
        "latency_ms_per_kb": round(avg_latency_ms / input_kb, 4) if input_kb > 0 else 0,
        "latency_ms_per_1k_tokens": round(avg_latency_ms / (tokens_in / 1000), 4) if tokens_in > 0 else 0
    }


def build_adaptive_policy_demo(iterations=5):
    """Return optional profile comparisons without changing default benchmarks.

    The demo evaluates each fixture with all deterministic policy profiles and
    carries replay evidence metrics from the replay artifacts beside measured
    token/latency values. It is intentionally opt-in and does not mutate the
    default KVTC-V7 engine configuration used by ``run_benchmark``.
    """

    paper_rows = {row["paper"]: row for row in build_paper_replay_artifact()["papers"]}
    trace_rows = {row["trace"]: row for row in build_agent_trace_replay_artifact()["traces"]}
    comparisons = []

    for spec in PAPER_SPECS:
        fixture_name = str(spec["fixture"])
        row = paper_rows[str(spec["paper"])]
        text = (PAPER_FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8")
        metrics = ReplayMetrics(
            compression_ratio=float(row["compression_ratio"]),
            reduction_percent=reduction_percent_from_ratio(float(row["compression_ratio"])),
            replay_consistency=float(row["replay_consistency"]),
            constraint_survival=1.0,
            blocker_survival=1.0,
            evidence_survival_rate=float(row["evidence_survival_rate"]),
            has_evidence=int(row["evidence_total"]) > 0,
            high_critical_evidence_survival_rate=float(row["high_critical_evidence_survival_rate"]),
        )
        comparisons.append(_measure_profiles_for_demo(fixture_name, "paper", text, metrics, iterations))

    for spec in TRACE_SPECS:
        fixture_name = str(spec["fixture"])
        row = trace_rows[str(spec["trace"])]
        text = (TRACE_FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8")
        metrics = ReplayMetrics(
            compression_ratio=float(row["compression_ratio"]),
            reduction_percent=reduction_percent_from_ratio(float(row["compression_ratio"])),
            replay_consistency=float(row["replay_consistency"]),
            constraint_survival=float(row["constraint_survival_rate"]),
            blocker_survival=float(row["blocker_survival_rate"]),
            evidence_survival_rate=float(row["evidence_survival_rate"]),
            has_evidence=int(row["evidence_total"]) > 0,
            high_critical_evidence_survival_rate=float(row["high_critical_evidence_survival_rate"]),
        )
        comparisons.append(_measure_profiles_for_demo(fixture_name, "agent_trace", text, metrics, iterations))

    return {
        "benchmark": "adaptive_policy_demo",
        "iterations": iterations,
        "results": comparisons,
    }


def _measure_profiles_for_demo(name, fixture_type, text, metrics, iterations):
    selected_profile = select_profile(metrics)
    profiles = []
    for profile in ("CONSERVATIVE", "BALANCED", "AGGRESSIVE"):
        typed_profile: CompressionProfile = profile
        params = get_params(typed_profile)
        engine = KVTCV7Engine(
            window_seconds=params.window_seconds,
            max_families=params.max_families,
            max_bursts=params.max_bursts,
        )
        measured = measure_fixture(engine, text, name, fixture_type, iterations)
        profiles.append(
            {
                "profile": profile,
                "selected": profile == selected_profile,
                "window_seconds": params.window_seconds,
                "max_families": params.max_families,
                "max_bursts": params.max_bursts,
                "use_sparse_micro_frames": params.use_sparse_micro_frames,
                "compression_ratio": measured["compression_ratio"],
                "reduction_percent": measured["reduction_percent"],
                "latency_ms_per_run": measured["latency_ms_per_run"],
            }
        )

    return {
        "fixture": name,
        "type": fixture_type,
        "selected_profile": selected_profile,
        "evidence_survival_rate": metrics.evidence_survival_rate,
        "has_evidence": metrics.has_evidence,
        "replay_consistency": metrics.replay_consistency,
        "profiles": profiles,
    }

if __name__ == "__main__":
    run_benchmark()
