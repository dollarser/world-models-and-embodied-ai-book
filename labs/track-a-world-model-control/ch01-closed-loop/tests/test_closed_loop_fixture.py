from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from closed_loop_fixture import (  # noqa: E402
    BOUNDARY_TOUCHING_DISTURBANCES,
    TRANSIENT_VIOLATION_DISTURBANCES,
    evaluate,
    feedback_rollout,
    rollout,
    terminal_state_aliasing_audit,
)


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

    def test_timely_feedback_rejects_the_same_persistent_disturbance(self):
        comparison = evaluate()["feedback_comparison"]
        self.assertEqual(comparison["open_loop"]["final_state"], 1.2)
        self.assertTrue(comparison["open_loop"]["bound_violated"])
        self.assertEqual(comparison["timely_feedback"]["final_state"], 0.124999999488)
        self.assertEqual(comparison["timely_feedback"]["maximum_abs_state"], 0.124999999488)
        self.assertFalse(comparison["timely_feedback"]["bound_violated"])

    def test_two_step_observation_delay_changes_the_closed_loop_outcome(self):
        comparison = evaluate()["feedback_comparison"]
        delayed = comparison["delayed_feedback"]
        self.assertEqual(delayed["controller_gain"], comparison["timely_feedback"]["controller_gain"])
        self.assertEqual(delayed["observation_delay_steps"], 2)
        self.assertEqual(delayed["final_state"], 0.4076)
        self.assertTrue(delayed["bound_violated"])
        self.assertEqual(delayed["first_violation_step"], 4)

    def test_insufficient_action_authority_is_reported_as_saturation(self):
        limited = evaluate()["feedback_comparison"]["authority_limited_feedback"]
        self.assertEqual(limited["action_limit"], 0.05)
        self.assertEqual(limited["saturation_count"], 11)
        self.assertEqual(limited["final_state"], 0.65)
        self.assertTrue(limited["bound_violated"])

    def test_feedback_contract_rejects_invalid_delay_gain_limit_and_disturbance(self):
        for kwargs in (
            {"controller_gain": -0.1},
            {"controller_gain": True},
            {"controller_gain": 0.8, "observation_delay_steps": True},
            {"controller_gain": 0.8, "observation_delay_steps": -1},
            {"controller_gain": 0.8, "action_limit": 0.0},
            {"controller_gain": 0.8, "safety_bound": float("inf")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                feedback_rollout((0.1,), **kwargs)
        for disturbances in ((), (False,), (float("nan"),)):
            with self.subTest(disturbances=disturbances), self.assertRaises(ValueError):
                feedback_rollout(disturbances, controller_gain=0.8)

    def test_terminal_aliasing_sequences_have_the_same_inputs_and_final_state(self):
        audit = terminal_state_aliasing_audit()
        self.assertTrue(audit["same_disturbance_multiset"])
        self.assertEqual(audit["final_state_gap"], 0.0)
        self.assertEqual(audit["boundary_touching"]["final_state"], 0.264)
        self.assertEqual(audit["transient_violation"]["final_state"], 0.264)

    def test_touching_the_strict_boundary_is_not_a_violation(self):
        result = terminal_state_aliasing_audit()["boundary_touching"]
        self.assertEqual(result["maximum_abs_state"], 0.3)
        self.assertFalse(result["bound_violated"])
        self.assertIsNone(result["first_violation_step"])

    def test_equal_terminal_state_can_hide_a_transient_violation(self):
        result = terminal_state_aliasing_audit()["transient_violation"]
        self.assertEqual(result["maximum_abs_state"], 0.476)
        self.assertTrue(result["bound_violated"])
        self.assertEqual(result["first_violation_step"], 7)

    def test_disturbance_order_changes_peak_not_mean_absolute_magnitude(self):
        audit = terminal_state_aliasing_audit()
        self.assertEqual(audit["maximum_abs_state_gap"], 0.176)
        self.assertEqual(
            audit["boundary_touching"]["disturbance_mean_abs"],
            audit["transient_violation"]["disturbance_mean_abs"],
        )
        self.assertEqual(
            sorted(BOUNDARY_TOUCHING_DISTURBANCES),
            sorted(TRANSIENT_VIOLATION_DISTURBANCES),
        )


if __name__ == "__main__":
    unittest.main()
