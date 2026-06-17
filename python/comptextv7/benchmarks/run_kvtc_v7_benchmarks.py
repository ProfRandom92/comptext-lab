"""Honest, reproducible KVTC-V7 benchmark scenarios.

The benchmark intentionally reports both strong and weak cases.  KVTC-V7 is a
lossy structured-log compressor, so repetitive diagnostic telemetry should
compress very well while short or high-entropy inputs should not be advertised as
wins.  The datasets below are synthetic and deterministic; they are not vendor
certification data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
import statistics
import sys
import time
import tracemalloc
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.kvtc_v7 import KVTCV7Engine  # noqa: E402


Generator = Callable[[], str]


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """A benchmark input with an explicit expectation note."""

    name: str
    description: str
    expectation: str
    generator: Generator


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Aggregated measurement for one benchmark case."""

    name: str
    description: str
    expectation: str
    lines: int
    input_bytes: int
    payload_bytes: int
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    reduction_percent: float
    median_ms: float
    min_ms: float
    max_ms: float
    throughput_lines_per_second: float
    peak_kib: float
    distinct_families: int
    top_family_coverage_percent: float

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "name": self.name,
            "description": self.description,
            "expectation": self.expectation,
            "lines": self.lines,
            "input_bytes": self.input_bytes,
            "payload_bytes": self.payload_bytes,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": round(self.compression_ratio, 6),
            "reduction_percent": round(self.reduction_percent, 3),
            "median_ms": round(self.median_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "throughput_lines_per_second": round(self.throughput_lines_per_second, 1),
            "peak_kib": round(self.peak_kib, 1),
            "distinct_families": self.distinct_families,
            "top_family_coverage_percent": round(self.top_family_coverage_percent, 2),
        }


def repetitive_xentry_log(lines: int = 2_000) -> str:
    severities = ("ERROR", "WARN", "INFO")
    modules = ("MCM", "ACM", "SCR")
    codes = ("P0301", "P0401", "SPN 1234 FMI 5")
    rows: list[str] = []
    for idx in range(lines):
        rows.append(
            "2026-05-10T12:{minute:02d}:{second:02d}Z {severity} ECU={module} {code} "
            "engine misfire cylinder={cylinder} temperature={temperature}C pressure=2.{pressure}bar "
            "voltage=23.{voltage}V XENTRY guided-test says combustion irregularity detected"
            .format(
                minute=(idx // 60) % 60,
                second=idx % 60,
                severity=severities[idx % len(severities)],
                module=modules[idx % len(modules)],
                code=codes[idx % len(codes)],
                cylinder=(idx % 6) + 1,
                temperature=94 + (idx % 9),
                pressure=idx % 7,
                voltage=idx % 10,
            )
        )
    return "\n".join(rows)


def mixed_obd_workshop_log(lines: int = 1_500) -> str:
    rng = random.Random(7)
    templates = (
        "{ts} ERROR source=ABS C0035 wheel speed sensor plausibility fault axle={axle} voltage={v}V",
        "{ts} WARN ECU=SCR SPN {spn} FMI {fmi} aftertreatment pressure={p}kPa temperature={t}C",
        "{ts} INFO module=CPC torque request accepted current={cur}A timeout counter={cnt}",
        "{ts} DEBUG PTCAN frame=0x{frame:X} diagnostic keepalive latency={lat}ms",
    )
    rows: list[str] = []
    for idx in range(lines):
        ts = f"2026-05-10T13:{(idx // 60) % 60:02d}:{idx % 60:02d}Z"
        rows.append(
            rng.choice(templates).format(
                ts=ts,
                axle=rng.choice(("front_left", "front_right", "rear_left", "rear_right")),
                v=round(11.8 + rng.random() * 2, 2),
                spn=rng.choice((4334, 3364, 5246, 1234)),
                fmi=rng.choice((2, 5, 9, 31)),
                p=rng.randrange(180, 260),
                t=rng.randrange(180, 460),
                cur=round(3 + rng.random() * 9, 2),
                cnt=rng.randrange(0, 12),
                frame=rng.randrange(0x100, 0x7FF),
                lat=rng.randrange(1, 75),
            )
        )
    return "\n".join(rows)


def high_entropy_json_log(lines: int = 750) -> str:
    rng = random.Random(11)
    rows: list[str] = []
    for idx in range(lines):
        blob = {
            "ts": f"2026-05-10T14:{(idx // 60) % 60:02d}:{idx % 60:02d}Z",
            "severity": rng.choice(("INFO", "DEBUG", "WARN")),
            "uuid": f"{rng.getrandbits(128):032x}",
            "nonce": f"{rng.getrandbits(96):024x}",
            "sample": [rng.randrange(0, 1_000_000) for _ in range(8)],
            "comment": f"operator free text {rng.getrandbits(64):016x}",
        }
        rows.append(json.dumps(blob, sort_keys=True, separators=(",", ":")))
    return "\n".join(rows)


def short_sparse_log() -> str:
    return "\n".join(
        (
            "2026-05-10T15:00:00Z INFO ECU=MCM startup complete voltage=24.1V",
            "2026-05-10T15:00:03Z WARN ECU=ABS C0035 intermittent wheel speed sensor",
            "manual note: customer reports rare vibration after pothole impact",
        )
    )


def benchmark_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            name="repetitive_xentry_2k",
            description="2,000 repeated XENTRY-style diagnostic rows with small value drift.",
            expectation="Best case: repeated families should compress extremely well.",
            generator=repetitive_xentry_log,
        ),
        BenchmarkCase(
            name="mixed_obd_workshop_1_5k",
            description="1,500 mixed workshop rows across ABS, SCR, CPC, and PTCAN patterns.",
            expectation="Realistic middle case: several families, noisy measurements, still structured.",
            generator=mixed_obd_workshop_log,
        ),
        BenchmarkCase(
            name="high_entropy_json_750",
            description="750 JSON rows dominated by random UUID-like fields and numeric samples.",
            expectation="Weak case: apparent reduction is lossy and misleading; top-family coverage should be low.",
            generator=high_entropy_json_log,
        ),
        BenchmarkCase(
            name="short_sparse_3",
            description="Three short heterogeneous notes using the sparse micro-frame path.",
            expectation="Sparse edge case: micro-frame prevents metadata overhead from dominating tiny inputs.",
            generator=short_sparse_log,
        ),
    )


def run_case(case: BenchmarkCase, *, iterations: int, warmups: int) -> CaseResult:
    engine = KVTCV7Engine(window_seconds=60, max_families=12, max_bursts=8)
    text = case.generator()
    line_count = len(text.splitlines())

    for _ in range(warmups):
        engine.compress(text)

    durations_ms: list[float] = []
    peaks_kib: list[float] = []
    last_result = None
    for _ in range(iterations):
        tracemalloc.start()
        start = time.perf_counter()
        last_result = engine.compress(text)
        elapsed_ms = (time.perf_counter() - start) * 1_000
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        durations_ms.append(elapsed_ms)
        peaks_kib.append(peak_bytes / 1024)

    if last_result is None:  # defensive; argparse prevents this.
        raise ValueError("iterations must be positive")

    family_counts: dict[str, int] = {}
    for event in last_result.events:
        family = engine._family_key(event)
        family_counts[family] = family_counts.get(family, 0) + 1
    top_family_total = sum(sorted(family_counts.values(), reverse=True)[: engine.max_families])

    median_ms = statistics.median(durations_ms)
    return CaseResult(
        name=case.name,
        description=case.description,
        expectation=case.expectation,
        lines=line_count,
        input_bytes=len(text.encode("utf-8")),
        payload_bytes=len(last_result.text.encode("utf-8")),
        original_tokens=last_result.original_tokens,
        compressed_tokens=last_result.compressed_tokens,
        compression_ratio=last_result.compression_ratio,
        reduction_percent=last_result.reduction_percent,
        median_ms=median_ms,
        min_ms=min(durations_ms),
        max_ms=max(durations_ms),
        throughput_lines_per_second=(line_count / (median_ms / 1_000)) if median_ms else float("inf"),
        peak_kib=max(peaks_kib),
        distinct_families=len(family_counts),
        top_family_coverage_percent=(top_family_total / line_count * 100) if line_count else 0.0,
    )


def run_benchmarks(*, iterations: int = 5, warmups: int = 1) -> list[CaseResult]:
    return [run_case(case, iterations=iterations, warmups=warmups) for case in benchmark_cases()]


def print_markdown(results: Iterable[CaseResult]) -> None:
    print("# KVTC-V7 benchmark results")
    print()
    print("Synthetic deterministic inputs; lower compression ratio is smaller output. Runtime is wall-clock median.")
    print()
    print(
        "| case | lines | input bytes | payload bytes | original tokens | compressed tokens | "
        "reduction | median ms | lines/s | peak KiB | distinct families | top-family coverage | honest expectation |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for result in results:
        print(
            "| {name} | {lines} | {input_bytes} | {payload_bytes} | {original_tokens} | "
            "{compressed_tokens} | {reduction_percent:.2f}% | {median_ms:.2f} | "
            "{throughput_lines_per_second:.0f} | {peak_kib:.1f} | {distinct_families} | "
            "{top_family_coverage_percent:.2f}% | {expectation} |".format(**result.as_dict())
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5, help="Measured repetitions per case (default: 5).")
    parser.add_argument("--warmups", type=int, default=1, help="Unmeasured warmup repetitions per case (default: 1).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of Markdown.")
    args = parser.parse_args()

    if args.iterations <= 0:
        raise SystemExit("--iterations must be positive")
    if args.warmups < 0:
        raise SystemExit("--warmups must be non-negative")

    results = run_benchmarks(iterations=args.iterations, warmups=args.warmups)
    if args.json:
        print(json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True))
    else:
        print_markdown(results)


if __name__ == "__main__":
    main()
