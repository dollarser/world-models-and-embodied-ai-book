from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from protocol_fixture import comparability_warnings, evaluate_protocol  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
