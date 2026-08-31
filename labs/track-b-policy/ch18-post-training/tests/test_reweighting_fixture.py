from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from reweighting_fixture import evaluate, mean_absolute_error, summarize, within_dataset_support  # noqa: E402


class ReweightingFixtureTests(unittest.TestCase):
    def test_uniform_target_is_plain_behavior_average(self):
        self.assertEqual(summarize((1, 1, 1, 1))["action_target"], (0.55, 0.45))

    def test_reward_weighting_moves_toward_successful_reference(self):
        result = evaluate()
        self.assertEqual(result["reward_weighted"]["action_target"], (0.4, 0.6))
        self.assertEqual(result["uniform"]["reference_mae"], 0.3)
        self.assertEqual(result["reward_weighted"]["reference_mae"], 0.15)

    def test_success_only_target_matches_reference(self):
        result = evaluate()["success_only"]
        self.assertEqual(result["action_target"], (0.25, 0.75))
        self.assertEqual(result["reference_mae"], 0.0)

    def test_effective_sample_size_exposes_concentration(self):
        result = evaluate()
        self.assertEqual(result["uniform"]["effective_sample_size"], 4.0)
        self.assertEqual(result["reward_weighted"]["effective_sample_size"], 3.2)
        self.assertEqual(result["success_only"]["effective_sample_size"], 2.0)

    def test_episode_reward_suppresses_recovery_coverage(self):
        result = evaluate()
        self.assertEqual(result["uniform"]["recovery_mass"], 0.5)
        self.assertEqual(result["reward_weighted"]["recovery_mass"], 0.25)
        self.assertEqual(result["success_only"]["recovery_mass"], 0.0)

    def test_support_gate_rejects_unobserved_extremes(self):
        result = evaluate()["support_gate"]
        self.assertTrue(result["successful_reference_in_support"])
        self.assertFalse(result["out_of_support_proposal_accepted"])
        with self.assertRaises(ValueError):
            within_dataset_support((True, 0.5))

    def test_invalid_weights_and_values_are_rejected(self):
        for weights in ((), (1, 1), (0, 0, 0, 0), (1, -1, 1, 1), (1, True, 1, 1), (1, math.inf, 1, 1)):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                summarize(weights)
        with self.assertRaises(ValueError):
            mean_absolute_error((0.0,), (0.0, 1.0))


if __name__ == "__main__":
    unittest.main()
