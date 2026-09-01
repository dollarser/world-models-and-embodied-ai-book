from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imagination_fixture import (  # noqa: E402
    bootstrap_discounts,
    cumulative_loss_weights,
    evaluate,
    lambda_returns,
    weighted_loss_audit,
)


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

    def test_terminal_closes_bootstrap_but_valid_truncation_does_not(self):
        self.assertEqual(bootstrap_discounts((True,), (False,), (False,), 0.9), (0.0,))
        self.assertEqual(bootstrap_discounts((False,), (True,), (True,), 0.9), (0.9,))

    def test_collapsing_done_underestimates_a_truncated_target(self):
        result = evaluate()["episode_end_semantics"]
        self.assertEqual(result["terminal_target"], 1.0)
        self.assertEqual(result["truncation_target"], 5.0)
        self.assertEqual(result["collapsed_done_target"], 1.0)
        self.assertEqual(result["truncation_bootstrap_loss"], 4.0)

    def test_terminal_dominates_bootstrap_when_both_end_flags_are_true(self):
        self.assertEqual(bootstrap_discounts((True,), (True,), (False,)), (0.0,))

    def test_missing_next_observation_is_not_silently_treated_as_terminal(self):
        with self.assertRaises(ValueError):
            bootstrap_discounts((False,), (True,), (False,))

    def test_cumulative_weights_stop_after_terminal_transition(self):
        self.assertEqual(cumulative_loss_weights((1.0, 0.0, 0.0)), (1.0, 1.0, 0.0))

    def test_missing_mask_leaks_post_terminal_loss_into_objective(self):
        result = evaluate()["imagined_loss_weighting"]
        self.assertEqual(result["correct_mask"]["weighted_contributions"], (1.0, 1.0, 0.0))
        self.assertEqual(result["missing_mask"]["weighted_contributions"], (1.0, 1.0, 100.0))
        self.assertEqual(result["post_terminal_loss_leakage"], 100.0)

    def test_loss_weighting_rejects_bad_sequences_and_losses(self):
        for args in (((1.0,), (1.0, 0.0)), ((-1.0,), (1.0,)), ((1.0,), (1.1,))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                weighted_loss_audit(*args)

    def test_end_contract_rejects_bad_lengths_types_and_gamma(self):
        invalid_cases = (
            ((False,), (), (True,), 1.0),
            ((False,), (False,), (True, False), 1.0),
            ((0,), (False,), (True,), 1.0),
            ((False,), (False,), (True,), True),
            ((False,), (False,), (True,), 1.1),
        )
        for case in invalid_cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                bootstrap_discounts(*case)

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
