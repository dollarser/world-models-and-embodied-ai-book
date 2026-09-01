from math import exp
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imitation_fixture import (  # noqa: E402
    action_error_correlation_audit,
    chunk_tradeoff,
    compounding_error,
    distribution_shift_rollout_audit,
    evaluate,
    temporal_ensemble,
)


class ImitationFixtureTests(unittest.TestCase):
    def test_action_bias_accumulates_over_rollout(self):
        result = compounding_error(horizon=20, action_bias=0.02)
        self.assertAlmostEqual(result["open_loop_action_rmse"], 0.02)
        self.assertAlmostEqual(result["integrated_final_state_error"], 0.4)
        self.assertAlmostEqual(result["integration_gain_steps"], 20.0)

    def test_equal_pointwise_errors_can_have_different_integrated_outcomes(self):
        result = action_error_correlation_audit()
        persistent = result["persistent_same_sign"]
        alternating = result["alternating_sign"]
        self.assertAlmostEqual(persistent["action_rmse"], alternating["action_rmse"])
        self.assertAlmostEqual(
            persistent["mean_absolute_action_error"], alternating["mean_absolute_action_error"]
        )
        self.assertAlmostEqual(persistent["integrated_final_state_error"], 0.4)
        self.assertAlmostEqual(alternating["integrated_final_state_error"], 0.0)

    def test_alternating_error_still_has_nonzero_transient_state_error(self):
        alternating = action_error_correlation_audit()["alternating_sign"]
        self.assertAlmostEqual(alternating["maximum_absolute_state_error"], 0.02)

    def test_action_error_correlation_audit_rejects_invalid_inputs(self):
        invalid_cases = ((0, 0.02), (3, 0.02), (True, 0.02), (20, -0.01), (20, float("inf")), (20, True))
        for horizon, magnitude in invalid_cases:
            with self.subTest(horizon=horizon, magnitude=magnitude), self.assertRaises(ValueError):
                action_error_correlation_audit(horizon, magnitude)

    def test_equal_expert_support_error_can_hide_opposite_feedback(self):
        result = distribution_shift_rollout_audit()
        self.assertEqual(
            result["expert_support_action_mse"],
            {"negative_feedback": 0.0, "positive_feedback": 0.0},
        )
        self.assertEqual(result["expert_support"], [{"state": 0.0, "action": 0.0}])

    def test_same_disturbance_yields_recovery_and_divergence(self):
        result = distribution_shift_rollout_audit()
        self.assertAlmostEqual(result["negative_feedback"]["final_absolute_state"], 0.00390625)
        self.assertAlmostEqual(result["positive_feedback"]["final_absolute_state"], 2.84765625)
        self.assertLess(
            result["negative_feedback"]["final_absolute_state"], result["initial_disturbance"]
        )
        self.assertGreater(
            result["positive_feedback"]["final_absolute_state"], result["initial_disturbance"]
        )

    def test_zero_disturbance_does_not_probe_off_support_behavior(self):
        result = distribution_shift_rollout_audit(initial_disturbance=0.0)
        self.assertEqual(result["negative_feedback"]["final_absolute_state"], 0.0)
        self.assertEqual(result["positive_feedback"]["final_absolute_state"], 0.0)

    def test_disturbance_direction_preserves_the_absolute_outcome(self):
        positive = distribution_shift_rollout_audit(initial_disturbance=0.25)
        negative = distribution_shift_rollout_audit(initial_disturbance=-0.25)
        self.assertEqual(
            positive["negative_feedback"]["final_absolute_state"],
            negative["negative_feedback"]["final_absolute_state"],
        )
        self.assertEqual(
            positive["positive_feedback"]["final_absolute_state"],
            negative["positive_feedback"]["final_absolute_state"],
        )

    def test_distribution_shift_audit_rejects_invalid_contracts(self):
        invalid_cases = (
            {"horizon": 0},
            {"horizon": True},
            {"initial_disturbance": float("nan")},
            {"policy_gain": 0.0},
            {"policy_gain": 1.0},
            {"policy_gain": True},
        )
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                distribution_shift_rollout_audit(**kwargs)

    def test_chunk_one_reacts_without_stale_delay(self):
        result = chunk_tradeoff()[0]
        self.assertEqual(result["prediction_horizon_steps"], 8)
        self.assertEqual(result["execution_horizon_steps"], 1)
        self.assertEqual(result["discarded_prediction_steps_per_full_query"], 7)
        self.assertEqual(result["mean_reaction_delay_steps"], 0.0)
        self.assertEqual(result["deadline_pass_rate"], 1.0)

    def test_larger_execution_horizon_trades_queries_for_reaction_delay(self):
        rows = chunk_tradeoff()
        self.assertGreater(rows[0]["policy_queries"], rows[-1]["policy_queries"])
        self.assertLess(rows[0]["max_reaction_delay_steps"], rows[-1]["max_reaction_delay_steps"])

    def test_prediction_horizon_is_held_fixed_while_execution_horizon_changes(self):
        rows = chunk_tradeoff()
        self.assertEqual({row["prediction_horizon_steps"] for row in rows}, {8})
        self.assertEqual([row["execution_horizon_steps"] for row in rows], [1, 4, 8])
        self.assertEqual([row["discarded_prediction_steps_per_full_query"] for row in rows], [7, 4, 0])

    def test_temporal_ensemble_reduces_stationary_jitter(self):
        result = evaluate()["temporal_ensemble"]
        self.assertLess(result["stationary_ensemble_absolute_error"], result["stationary_latest_absolute_error"])

    def test_temporal_ensemble_lags_a_real_change(self):
        result = evaluate()["temporal_ensemble"]
        self.assertEqual(result["changed_latest_absolute_error"], 0.0)
        self.assertGreater(result["changed_ensemble_absolute_error"], 0.7)

    def test_temporal_ensemble_uses_oldest_first_exponential_weights(self):
        self.assertAlmostEqual(temporal_ensemble((1.0, 0.0), coefficient=1.0), 1.0 / (1.0 + exp(-1.0)))

    def test_invalid_horizon_is_rejected(self):
        with self.assertRaises(ValueError):
            compounding_error(horizon=0)

    def test_invalid_numeric_and_chunk_contracts_are_rejected(self):
        invalid_compounding = ((True, 0.02), (20, True), (20, float("nan")))
        for horizon, bias in invalid_compounding:
            with self.subTest(horizon=horizon, bias=bias), self.assertRaises(ValueError):
                compounding_error(horizon=horizon, action_bias=bias)
        invalid_chunks = (
            {"prediction_horizon": True},
            {"execution_horizons": ()},
            {"execution_horizons": (1, 9)},
            {"execution_horizons": (1, 1)},
            {"deadline_steps": True},
        )
        for kwargs in invalid_chunks:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                chunk_tradeoff(**kwargs)

    def test_temporal_ensemble_rejects_invalid_inputs(self):
        invalid_cases = (((), 0.01), ((0.0, float("inf")), 0.01), ((0.0,), -0.1), ((0.0,), True))
        for predictions, coefficient in invalid_cases:
            with self.subTest(predictions=predictions, coefficient=coefficient), self.assertRaises(ValueError):
                temporal_ensemble(predictions, coefficient)


if __name__ == "__main__":
    unittest.main()
