from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from probing_fixture import (  # noqa: E402
    encode,
    evaluate,
    fit_centroid_probe,
    probe_accuracy,
    reconstruction_mse,
)


class ProbingFixtureTests(unittest.TestCase):
    def test_appearance_wins_reconstruction(self):
        self.assertLess(reconstruction_mse("appearance"), reconstruction_mse("task_predictive"))

    def test_task_feature_wins_under_nuisance_shift(self):
        self.assertEqual(probe_accuracy("appearance"), 0.0)
        self.assertEqual(probe_accuracy("task_predictive"), 1.0)

    def test_collapsed_representation_is_detected(self):
        metrics = evaluate()["collapsed"]
        self.assertEqual(metrics["shifted_probe_accuracy"], 0.5)
        self.assertGreater(metrics["shifted_task_rmse"], 0.0)

    def test_probe_is_fit_on_train_only(self):
        self.assertEqual(fit_centroid_probe("appearance"), (-15.0, 15.0))

    def test_unknown_representation_is_rejected(self):
        with self.assertRaises(ValueError):
            encode({"task": 1.0, "texture": 1.0}, "unknown")


if __name__ == "__main__":
    unittest.main()
