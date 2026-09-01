from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from action_fixture import (  # noqa: E402
    evaluate,
    fit_action_deltas,
    predict_next,
    render_state,
    rollout,
    transition,
)


class ActionConditionedFixtureTests(unittest.TestCase):
    def test_action_deltas_are_learned_from_transitions(self):
        self.assertEqual(fit_action_deltas()["left"], (1.0, -1.0))
        self.assertEqual(fit_action_deltas()["brake"], (0.0, 0.0))

    def test_counterfactual_actions_produce_different_futures(self):
        start = (2.0, 3.0)
        self.assertNotEqual(predict_next(start, "left", "action_conditioned"), predict_next(start, "right", "action_conditioned"))

    def test_unseen_sequence_rollout_is_exact_for_conditioned_model(self):
        actions = ("left", "forward", "right")
        self.assertEqual(rollout((1.0, 3.0), actions), rollout((1.0, 3.0), actions, "action_conditioned"))

    def test_renderer_does_not_advance_state(self):
        state = transition((1.0, 1.0), "forward")
        frame = render_state(state)
        self.assertEqual(frame.count("A"), 1)
        self.assertEqual(state, (2.0, 1.0))

    def test_blind_model_fails_action_sensitivity(self):
        metrics = evaluate()
        self.assertEqual(metrics["action_blind"]["action_sensitivity"], 0.0)
        self.assertEqual(metrics["action_conditioned"]["action_sensitivity"], 2.0)

    def test_sensitivity_does_not_prove_action_direction(self):
        metrics = evaluate()
        self.assertEqual(metrics["left_right_swapped"]["action_sensitivity"], 2.0)
        self.assertEqual(metrics["left_right_swapped"]["left_right_separation"], 2.0)
        self.assertEqual(metrics["left_right_swapped"]["left_to_right_signed_separation"], -2.0)
        self.assertEqual(metrics["action_conditioned"]["left_to_right_signed_separation"], 2.0)

    def test_counterfactual_vector_error_detects_swapped_actions(self):
        metrics = evaluate()
        self.assertGreater(metrics["left_right_swapped"]["counterfactual_vector_rmse"], 0.0)
        self.assertEqual(metrics["action_conditioned"]["counterfactual_vector_rmse"], 0.0)

    def test_rollout_reports_fixed_sequence_and_transition_denominators(self):
        metrics = evaluate()["action_conditioned"]
        self.assertEqual(metrics["unseen_sequence_count"], 3)
        self.assertEqual(metrics["unseen_transition_count"], 9)
        self.assertEqual(metrics["unseen_sequence_trajectory_rmse"], 0.0)

    def test_swapped_actions_fail_held_out_trajectory(self):
        metrics = evaluate()["left_right_swapped"]
        self.assertGreater(metrics["unseen_sequence_trajectory_rmse"], 0.0)
        self.assertGreater(metrics["mean_unseen_sequence_endpoint_error"], 0.0)

    def test_endpoint_only_metric_misses_a_swapped_action_sequence(self):
        swapped = evaluate()["left_right_swapped"]
        self.assertEqual(swapped["endpoint_cancellation_sequence_count"], 1)
        self.assertEqual(swapped["endpoint_cancellation_sequence_ids"], ["left→forward→right"])
        self.assertEqual(swapped["maximum_hidden_intermediate_error"], 2.0)

    def test_exact_model_has_no_hidden_intermediate_error(self):
        conditioned = evaluate()["action_conditioned"]
        self.assertEqual(conditioned["endpoint_cancellation_sequence_count"], 0)
        self.assertEqual(conditioned["endpoint_cancellation_sequence_ids"], [])
        self.assertEqual(conditioned["maximum_hidden_intermediate_error"], 0.0)

    def test_endpoint_cancellation_is_not_inferred_from_aggregate_mean(self):
        swapped = evaluate()["left_right_swapped"]
        self.assertGreater(swapped["mean_unseen_sequence_endpoint_error"], 0.0)
        self.assertEqual(swapped["endpoint_cancellation_sequence_count"], 1)

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ValueError):
            transition((1.0, 1.0), "teleport")

    def test_invalid_state_and_render_size_are_rejected(self):
        with self.assertRaises(ValueError):
            transition((float("nan"), 1.0), "forward")
        with self.assertRaises(ValueError):
            render_state((1.0, 1.0), size=0)

    def test_empty_action_sequence_and_unknown_model_are_rejected(self):
        with self.assertRaises(ValueError):
            rollout((1.0, 1.0), ())
        with self.assertRaises(ValueError):
            predict_next((1.0, 1.0), "forward", "unknown")


if __name__ == "__main__":
    unittest.main()
