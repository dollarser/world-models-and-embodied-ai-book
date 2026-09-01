from math import exp
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imitation_fixture import chunk_tradeoff, compounding_error, evaluate, temporal_ensemble  # noqa: E402


class ImitationFixtureTests(unittest.TestCase):
    def test_action_bias_accumulates_over_rollout(self):
        result = compounding_error(horizon=20, action_bias=0.02)
        self.assertAlmostEqual(result["open_loop_action_rmse"], 0.02)
        self.assertAlmostEqual(result["closed_loop_final_state_error"], 0.4)
        self.assertAlmostEqual(result["amplification_factor"], 20.0)

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
