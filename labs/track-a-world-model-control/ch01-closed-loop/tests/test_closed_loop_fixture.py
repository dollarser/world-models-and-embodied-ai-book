from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from closed_loop_fixture import evaluate, rollout  # noqa: E402


class ClosedLoopFixtureTests(unittest.TestCase):
    def test_two_sequences_have_the_same_offline_mae(self):
        result = evaluate()
        self.assertEqual(result["persistent_residual"]["offline_residual_mae"], 0.1)
        self.assertEqual(result["alternating_residual"]["offline_residual_mae"], 0.1)
        self.assertEqual(result["offline_mae_gap"], 0.0)

    def test_persistent_residual_accumulates(self):
        result = evaluate()["persistent_residual"]
        self.assertEqual(result["final_lateral_state"], 0.5)
        self.assertEqual(result["maximum_abs_lateral_state"], 0.5)

    def test_alternating_residual_partly_cancels(self):
        result = evaluate()["alternating_residual"]
        self.assertEqual(result["final_lateral_state"], 0.1)
        self.assertEqual(result["maximum_abs_lateral_state"], 0.1)

    def test_only_persistent_sequence_crosses_fixed_bound(self):
        result = evaluate()
        self.assertTrue(result["persistent_residual"]["bound_violated"])
        self.assertEqual(result["persistent_residual"]["first_violation_step"], 4)
        self.assertFalse(result["alternating_residual"]["bound_violated"])

    def test_custom_bound_changes_only_outcome_contract(self):
        result = rollout((0.1, 0.1), safety_bound=0.25)
        self.assertFalse(result["bound_violated"])
        self.assertEqual(result["offline_residual_mae"], 0.1)

    def test_empty_boolean_non_finite_and_invalid_bound_are_rejected(self):
        invalid = ((), (True,), (math.nan,), (math.inf,))
        for residuals in invalid:
            with self.subTest(residuals=residuals), self.assertRaises(ValueError):
                rollout(residuals)
        with self.assertRaises(ValueError):
            rollout((0.1,), safety_bound=0.0)


if __name__ == "__main__":
    unittest.main()
