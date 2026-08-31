from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imagination_fixture import evaluate, lambda_returns  # noqa: E402


class ImaginationFixtureTests(unittest.TestCase):
    def setUp(self):
        self.rewards = (0.0, 0.0, 1.0)
        self.discounts = (1.0, 1.0, 0.0)
        self.next_values = (0.4, 0.8, 0.0)

    def test_lambda_zero_is_one_step_bootstrap(self):
        self.assertEqual(lambda_returns(self.rewards, self.discounts, self.next_values, 0.0), (0.4, 0.8, 1.0))

    def test_lambda_half_mixes_bootstrap_and_long_return(self):
        self.assertEqual(lambda_returns(self.rewards, self.discounts, self.next_values, 0.5), (0.65, 0.9, 1.0))

    def test_lambda_one_propagates_terminal_reward(self):
        self.assertEqual(lambda_returns(self.rewards, self.discounts, self.next_values, 1.0), (1.0, 1.0, 1.0))

    def test_reward_model_bias_propagates_to_earlier_targets(self):
        result = evaluate()["reward_model_bias"]
        self.assertEqual(result["biased_targets"], (2.0, 2.0, 2.0))
        self.assertEqual(result["start_target_gap"], 1.0)

    def test_continuation_mask_stops_post_terminal_reward(self):
        result = evaluate()["continuation_mask"]
        self.assertEqual(result["correct_start_target"], 1.0)
        self.assertEqual(result["leaked_start_target"], 11.0)
        self.assertEqual(result["leakage_gap"], 10.0)

    def test_mismatched_or_empty_sequences_are_rejected(self):
        with self.assertRaises(ValueError):
            lambda_returns((), (), (), 0.5)
        with self.assertRaises(ValueError):
            lambda_returns((0.0,), (1.0, 1.0), (0.0,), 0.5)

    def test_invalid_numbers_ranges_and_booleans_are_rejected(self):
        invalid_cases = (
            ((True,), (1.0,), (0.0,), 0.5),
            ((math.inf,), (1.0,), (0.0,), 0.5),
            ((0.0,), (-0.1,), (0.0,), 0.5),
            ((0.0,), (1.1,), (0.0,), 0.5),
            ((0.0,), (1.0,), (0.0,), True),
            ((0.0,), (1.0,), (0.0,), math.nan),
            ((0.0,), (1.0,), (0.0,), 1.1),
        )
        for case in invalid_cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                lambda_returns(*case)


if __name__ == "__main__":
    unittest.main()
