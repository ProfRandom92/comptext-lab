import copy
import unittest

from verified_experience.benchmark import run_benchmark
from verified_experience.gate import evaluate_gate


class GateTests(unittest.TestCase):
    def test_seeded_benchmark_passes_all_hard_gates(self):
        result = evaluate_gate(run_benchmark(), deterministic_replay=True)
        self.assertEqual(result["decision"], "GO")
        self.assertTrue(all(item["pass"] for item in result["hard_gates"].values()))

    def test_any_unauthorized_promotion_forces_no_go(self):
        report = copy.deepcopy(run_benchmark())
        report["strategies"]["C_verified_experience"]["unauthorized_promotions"] = 1
        result = evaluate_gate(report, deterministic_replay=True)
        self.assertEqual(result["decision"], "NO-GO")
        self.assertFalse(result["hard_gates"]["zero_unauthorized_promotions"]["pass"])

    def test_nondeterministic_replay_forces_no_go(self):
        result = evaluate_gate(run_benchmark(), deterministic_replay=False)
        self.assertEqual(result["decision"], "NO-GO")
        self.assertFalse(result["hard_gates"]["deterministic_replay"]["pass"])


if __name__ == "__main__":
    unittest.main()
