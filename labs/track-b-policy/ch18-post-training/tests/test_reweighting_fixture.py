from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from reweighting_fixture import (  # noqa: E402
    advantage_group_report,
    dynamic_rejection_report,
    evaluate,
    joint_support_report,
    leave_one_out_advantages,
    mean_absolute_error,
    resampling_history_audit,
    summarize,
    within_dataset_support,
)


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
        self.assertTrue(result["successful_reference"]["joint_support_accepted"])
        self.assertFalse(result["marginal_extreme"]["marginal_range_accepted"])
        self.assertFalse(result["marginal_extreme"]["joint_support_accepted"])
        with self.assertRaises(ValueError):
            within_dataset_support((True, 0.5))

    def test_marginal_ranges_accept_an_unseen_hybrid_that_joint_support_rejects(self):
        hybrid = joint_support_report((0.9, 0.8))
        self.assertTrue(hybrid["marginal_range_accepted"])
        self.assertFalse(hybrid["joint_support_accepted"])
        self.assertEqual(hybrid["nearest_trajectory_mae"], 0.35)

    def test_joint_support_threshold_is_explicit_and_validated(self):
        self.assertTrue(joint_support_report((0.9, 0.8), max_mean_absolute_distance=0.35)["joint_support_accepted"])
        for threshold in (-1.0, True, math.inf, math.nan):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                joint_support_report((0.25, 0.75), max_mean_absolute_distance=threshold)  # type: ignore[arg-type]

    def test_leave_one_out_advantage_exposes_uniform_group_degeneracy(self):
        self.assertEqual(leave_one_out_advantages((1.0, 1.0, 1.0)), (0.0, 0.0, 0.0))
        self.assertEqual(leave_one_out_advantages((0.0, 0.0, 0.0)), (0.0, 0.0, 0.0))
        self.assertFalse(advantage_group_report((1.0, 1.0, 1.0))["has_nonzero_learning_signal"])
        self.assertFalse(advantage_group_report((0.0, 0.0, 0.0))["has_nonzero_learning_signal"])

    def test_leave_one_out_advantage_preserves_mixed_group_signal(self):
        self.assertEqual(leave_one_out_advantages((1.0, 0.0, 0.0)), (1.0, -0.5, -0.5))
        self.assertTrue(advantage_group_report((1.0, 0.0, 0.0))["has_nonzero_learning_signal"])
        for rewards in ((), (1.0,), (1.0, True), (1.0, math.nan)):
            with self.subTest(rewards=rewards), self.assertRaises(ValueError):
                leave_one_out_advantages(rewards)

    def test_dynamic_rejection_reports_attempted_used_and_rejected_denominators(self):
        report = evaluate()["dynamic_rejection"]
        self.assertEqual(report["attempted_group_count"], 4)
        self.assertEqual(report["used_group_count"], 2)
        self.assertEqual(report["rejected_group_count"], 2)
        self.assertEqual(report["attempted_rollout_count"], 12)
        self.assertEqual(report["used_rollout_count"], 6)
        self.assertEqual(report["rejected_rollout_count"], 6)

    def test_dynamic_rejection_changes_the_used_difficulty_mix(self):
        report = evaluate()["dynamic_rejection"]
        self.assertEqual(report["attempted_difficulty_distribution"], {"easy": 0.25, "hard": 0.25, "medium": 0.5})
        self.assertEqual(report["used_difficulty_distribution"], {"easy": 0.0, "hard": 0.0, "medium": 1.0})
        self.assertEqual(report["rejection_rate_by_difficulty"], {"easy": 1.0, "hard": 1.0, "medium": 0.0})

    def test_dynamic_rejection_contract_rejects_invalid_or_signal_free_batches(self):
        invalid_batches = ((), (("", (1.0, 0.0)),), (("easy", (1.0,)),), (("easy", (1.0, 1.0)),))
        for groups in invalid_batches:
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                dynamic_rejection_report(groups)

    def test_invalid_weights_and_values_are_rejected(self):
        for weights in ((), (1, 1), (0, 0, 0, 0), (1, -1, 1, 1), (1, True, 1, 1), (1, math.inf, 1, 1)):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                summarize(weights)
        with self.assertRaises(ValueError):
            mean_absolute_error((0.0,), (0.0, 1.0))

    def test_same_used_batch_can_hide_different_attempt_histories(self):
        audit = resampling_history_audit()
        self.assertTrue(audit["same_used_batch_summary"])
        self.assertEqual(audit["clean_history"]["used_rollout_count"], 6)
        self.assertEqual(audit["rejection_heavy_history"]["used_rollout_count"], 6)

    def test_rejection_history_doubles_attempted_rollout_cost(self):
        audit = resampling_history_audit()
        self.assertEqual(audit["clean_history"]["attempted_rollout_count"], 6)
        self.assertEqual(audit["rejection_heavy_history"]["attempted_rollout_count"], 12)
        self.assertEqual(audit["attempted_rollout_ratio"], 2.0)

    def test_used_only_summary_hides_rejected_contexts(self):
        audit = resampling_history_audit()
        self.assertEqual(audit["clean_history"]["rejected_group_count"], 0)
        self.assertEqual(audit["rejection_heavy_history"]["rejected_group_count"], 2)
        self.assertEqual(audit["hidden_extra_attempted_rollouts"], 6)

    def test_evaluate_registers_resampling_history_audit(self):
        audit = evaluate()["resampling_history_audit"]
        self.assertEqual(audit["attempted_rollout_ratio"], 2.0)


if __name__ == "__main__":
    unittest.main()
