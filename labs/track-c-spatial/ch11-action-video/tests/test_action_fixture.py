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
        self.assertEqual(metrics["action_blind"]["action_sensitivity"], 0.25)
        self.assertEqual(metrics["action_conditioned"]["action_sensitivity"], 1.0)

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ValueError):
            transition((1.0, 1.0), "teleport")


if __name__ == "__main__":
    unittest.main()
