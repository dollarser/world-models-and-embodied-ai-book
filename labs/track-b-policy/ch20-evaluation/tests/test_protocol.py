from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from protocol_fixture import comparability_warnings, evaluate_protocol, wilson_interval  # noqa: E402


class ProtocolFixtureTests(unittest.TestCase):
    def test_easy_goal_only_protocol_reports_all_success(self):
        result = evaluate_protocol("easy_goal_only")
        self.assertEqual(result["episode_count"], 4)
        self.assertEqual(result["success_rate"], 1.0)

    def test_safety_aware_protocol_rejects_collision_and_intervention(self):
        result = evaluate_protocol("full_safety_aware")
        self.assertEqual(result["episode_count"], 8)
        self.assertEqual(result["success_rate"], 0.625)
        self.assertEqual(result["collision_rate"], 0.125)
        self.assertEqual(result["intervention_rate"], 0.125)

    def test_comparability_audit_finds_three_differences(self):
        self.assertEqual(
            comparability_warnings("easy_goal_only", "full_safety_aware"),
            ["task_population_differs", "success_definition_differs", "denominator_differs"],
        )

    def test_unknown_protocol_is_rejected(self):
        with self.assertRaises(KeyError):
            evaluate_protocol("unknown")

    def test_wilson_interval_contains_observed_proportion(self):
        interval = wilson_interval(5, 8)
        self.assertLess(interval["lower"], 0.625)
        self.assertGreater(interval["upper"], 0.625)

    def test_perfect_small_sample_does_not_imply_certainty(self):
        interval = wilson_interval(4, 4)
        self.assertLess(interval["lower"], 1.0)
        self.assertEqual(interval["upper"], 1.0)

    def test_wilson_interval_rejects_invalid_counts(self):
        for successes, trials in ((-1, 4), (5, 4), (0, 0)):
            with self.subTest(successes=successes, trials=trials):
                with self.assertRaises(ValueError):
                    wilson_interval(successes, trials)
        with self.assertRaises(TypeError):
            wilson_interval(True, 4)
        with self.assertRaises(ValueError):
            wilson_interval(2, 4, float("nan"))


if __name__ == "__main__":
    unittest.main()
