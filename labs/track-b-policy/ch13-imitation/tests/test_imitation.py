from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imitation_fixture import chunk_tradeoff, compounding_error  # noqa: E402


class ImitationFixtureTests(unittest.TestCase):
    def test_action_bias_accumulates_over_rollout(self):
        result = compounding_error(horizon=20, action_bias=0.02)
        self.assertAlmostEqual(result["open_loop_action_rmse"], 0.02)
        self.assertAlmostEqual(result["closed_loop_final_state_error"], 0.4)
        self.assertAlmostEqual(result["amplification_factor"], 20.0)

    def test_chunk_one_reacts_without_stale_delay(self):
        result = chunk_tradeoff()[0]
        self.assertEqual(result["chunk_size"], 1)
        self.assertEqual(result["mean_reaction_delay_steps"], 0.0)
        self.assertEqual(result["deadline_pass_rate"], 1.0)

    def test_larger_chunk_trades_calls_for_reaction_delay(self):
        rows = chunk_tradeoff()
        self.assertGreater(rows[0]["planning_calls"], rows[-1]["planning_calls"])
        self.assertLess(rows[0]["max_reaction_delay_steps"], rows[-1]["max_reaction_delay_steps"])

    def test_invalid_horizon_is_rejected(self):
        with self.assertRaises(ValueError):
            compounding_error(horizon=0)


if __name__ == "__main__":
    unittest.main()
