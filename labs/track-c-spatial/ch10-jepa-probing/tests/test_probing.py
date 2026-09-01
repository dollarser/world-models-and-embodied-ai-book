from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from probing_fixture import (  # noqa: E402
    action_interface_metrics,
    encode,
    evaluate,
    fit_centroid_probe,
    predict_next_state,
    probe_accuracy,
    reconstruction_mse,
)


class ProbingFixtureTests(unittest.TestCase):
    def test_appearance_wins_reconstruction(self):
        self.assertLess(reconstruction_mse("appearance"), reconstruction_mse("task_predictive"))

    def test_task_feature_wins_under_nuisance_shift(self):
        self.assertEqual(probe_accuracy("appearance"), 0.0)
        self.assertEqual(probe_accuracy("task_predictive"), 1.0)

    def test_in_distribution_score_exposes_appearance_shortcut(self):
        self.assertEqual(probe_accuracy("appearance", "in_distribution"), 1.0)
        self.assertEqual(probe_accuracy("task_predictive", "in_distribution"), 1.0)

    def test_collapsed_representation_is_detected(self):
        metrics = evaluate()["collapsed"]
        self.assertEqual(metrics["shifted_probe_accuracy"], 0.5)
        self.assertGreater(metrics["shifted_task_rmse"], 0.0)

    def test_probe_is_fit_on_train_only(self):
        self.assertEqual(fit_centroid_probe("appearance"), (-15.0, 15.0))

    def test_unknown_representation_is_rejected(self):
        with self.assertRaises(ValueError):
            encode({"task": 1.0, "texture": 1.0}, "unknown")

    def test_unknown_probe_split_is_rejected(self):
        with self.assertRaises(ValueError):
            probe_accuracy("appearance", "validation")

    def test_malformed_sample_is_rejected(self):
        with self.assertRaises(ValueError):
            encode({"task": 1.0}, "appearance")

    def test_both_action_interfaces_have_exact_current_state_readout(self):
        self.assertEqual(action_interface_metrics("action_blind")["current_state_probe_rmse"], 0.0)
        self.assertEqual(action_interface_metrics("action_conditioned")["current_state_probe_rmse"], 0.0)

    def test_action_conditioning_is_required_for_counterfactual_transition(self):
        blind = action_interface_metrics("action_blind")
        conditioned = action_interface_metrics("action_conditioned")
        self.assertEqual(blind["counterfactual_transition_rmse"], 1.0)
        self.assertEqual(conditioned["counterfactual_transition_rmse"], 0.0)

    def test_action_sensitivity_detects_ignored_actions(self):
        self.assertEqual(action_interface_metrics("action_blind")["action_sensitivity"], 0.0)
        self.assertEqual(action_interface_metrics("action_conditioned")["action_sensitivity"], 2.0)

    def test_unknown_action_interface_and_nonfinite_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            predict_next_state(0.0, 1.0, "unknown")
        with self.assertRaises(ValueError):
            predict_next_state(float("nan"), 1.0, "action_conditioned")


if __name__ == "__main__":
    unittest.main()
