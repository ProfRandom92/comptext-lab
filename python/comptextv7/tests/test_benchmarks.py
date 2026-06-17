from __future__ import annotations

from benchmarks.run_kvtc_v7_benchmarks import benchmark_cases, run_benchmarks


def test_benchmark_suite_covers_strong_weak_and_sparse_cases() -> None:
    cases = benchmark_cases()

    assert len(cases) >= 4
    assert any("Best case" in case.expectation for case in cases)
    assert any("Weak case" in case.expectation for case in cases)
    assert any("Sparse edge case" in case.expectation for case in cases)


def test_benchmark_results_are_structured_and_honest_about_sparse_micro_frame() -> None:
    results = run_benchmarks(iterations=1, warmups=0)
    by_name = {result.name: result for result in results}

    assert by_name["repetitive_xentry_2k"].reduction_percent > 95.0
    assert by_name["high_entropy_json_750"].distinct_families == by_name["high_entropy_json_750"].lines
    assert by_name["high_entropy_json_750"].top_family_coverage_percent < 5.0
    assert by_name["short_sparse_3"].compressed_tokens < by_name["short_sparse_3"].original_tokens
    assert by_name["short_sparse_3"].payload_bytes < by_name["short_sparse_3"].input_bytes
    assert all(result.median_ms > 0 for result in results)
