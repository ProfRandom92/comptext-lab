import unittest

from verified_experience.benchmark import run_benchmark
from verified_experience.canonical import canonical_bytes


EXPECTED_FIXTURES = [
    "coding_outcome",
    "rumor_vs_observer_truth",
    "approval_spoof",
    "temporal_supersession",
    "constraint_retention",
]


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_has_exact_seeded_fixture_set(self):
        report = run_benchmark()
        self.assertEqual(report["fixture_ids"], EXPECTED_FIXTURES)

    def test_verified_experience_beats_latest_write_baseline_on_seeded_attacks(self):
        report = run_benchmark()
        a = report["strategies"]["A_raw_history"]
        b = report["strategies"]["B_ordinary_memory"]
        c = report["strategies"]["C_verified_experience"]

        self.assertEqual(a["correct_tasks"], 1)
        self.assertEqual(b["correct_tasks"], 1)
        self.assertEqual(c["correct_tasks"], 5)
        self.assertGreater(c["task_success_rate"], b["task_success_rate"])
        self.assertEqual(c["protected_failures_vs_b"], 4)

    def test_verified_experience_hard_metrics_are_green(self):
        c = run_benchmark()["strategies"]["C_verified_experience"]
        self.assertEqual(c["unauthorized_promotions"], 0)
        self.assertEqual(c["unsupported_trusted_claims"], 0)
        self.assertEqual(c["false_promotion_rate"], 0.0)
        self.assertEqual(c["trusted_recall_precision"], 1.0)
        self.assertEqual(c["contradiction_recovery_rate"], 1.0)
        self.assertEqual(c["supersession_correctness"], 1.0)
        self.assertEqual(c["revocation_correctness"], 1.0)
        self.assertEqual(c["high_criticality_evidence_survival"], 1.0)
        self.assertEqual(c["constraint_survival"], 1.0)

    def test_verified_answers_match_expected_values(self):
        c = run_benchmark()["strategies"]["C_verified_experience"]
        self.assertEqual(
            c["answers"],
            {
                "coding_outcome": "cargo test --workspace",
                "rumor_vs_observer_truth": 18,
                "approval_spoof": False,
                "temporal_supersession": "buck2",
                "constraint_retention": False,
            },
        )

    def test_repeated_benchmark_is_byte_identical(self):
        self.assertEqual(canonical_bytes(run_benchmark()), canonical_bytes(run_benchmark()))


if __name__ == "__main__":
    unittest.main()
