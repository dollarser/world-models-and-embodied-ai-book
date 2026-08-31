from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from generative_fixture import (  # noqa: E402
    conditional_mean,
    mode_refinement,
    nearest_mode_distance,
    oracle_straight_flow,
    sampling_fits_budget,
    summarize,
)


class GenerativeActionFixtureTests(unittest.TestCase):
    def test_mse_mean_lies_between_valid_modes(self):
        value = conditional_mean((-1.0, 1.0))
        self.assertEqual(value, 0.0)
        self.assertEqual(nearest_mode_distance(value), 1.0)

    def test_refinement_converges_toward_assigned_mode(self):
        self.assertLess(
            nearest_mode_distance(mode_refinement(0.25, steps=4)),
            nearest_mode_distance(mode_refinement(0.25, steps=1)),
        )

    def test_refinement_rejects_negative_steps(self):
        with self.assertRaises(ValueError):
            mode_refinement(0.5, steps=-1)

    def test_oracle_flow_reaches_mode_for_multiple_solver_steps(self):
        for steps in (1, 2, 4, 8):
            self.assertAlmostEqual(oracle_straight_flow(-1.5, steps), -1.0)

    def test_oracle_flow_requires_positive_steps(self):
        with self.assertRaises(ValueError):
            oracle_straight_flow(0.5, steps=0)

    def test_summary_separates_balance_from_validity(self):
        summary = summarize((0.0, 0.0))
        self.assertEqual(summary["sample_mean"], 0.0)
        self.assertEqual(summary["invalid_action_rate"], 1.0)
        self.assertEqual(summary["covered_mode_count"], 0)

    def test_sampling_budget_is_per_replan(self):
        self.assertTrue(sampling_fits_budget(4, available_evaluations=8))
        self.assertFalse(sampling_fits_budget(16, available_evaluations=8))
        with self.assertRaises(ValueError):
            sampling_fits_budget(0)


if __name__ == "__main__":
    unittest.main()
