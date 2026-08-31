from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from generative_fixture import (  # noqa: E402
    conditional_distribution,
    diffusion_forward,
    empirical_distribution,
    evaluate,
    expected_squared_error,
    flow_path,
    negative_log_likelihood,
    point_mean,
    quantile_samples,
)


class GenerativeFoundationTests(unittest.TestCase):
    def test_multimodal_mean_is_not_a_supported_future(self):
        mean = point_mean("fork")
        self.assertEqual(mean, 0.0)
        self.assertEqual(expected_squared_error(mean, "fork"), 1.0)
        self.assertNotIn(mean, conditional_distribution("fork"))

    def test_categorical_model_preserves_both_futures(self):
        distribution = conditional_distribution("fork")
        self.assertEqual(distribution, {-1.0: 0.5, 1.0: 0.5})
        self.assertEqual(quantile_samples(distribution, (0.125, 0.375, 0.625, 0.875)), (-1.0, -1.0, 1.0, 1.0))

    def test_conditioning_improves_dataset_nll(self):
        metrics = evaluate()
        self.assertLess(metrics["conditional_dataset_nll"], metrics["unconditional_dataset_nll"])

    def test_diffusion_forward_endpoints(self):
        self.assertEqual(diffusion_forward(1.0, -2.0, 1.0), 1.0)
        self.assertEqual(diffusion_forward(1.0, -2.0, 0.0), -2.0)

    def test_flow_path_endpoints_and_velocity(self):
        self.assertEqual(flow_path(-2.0, 1.0, 0.0), (-2.0, 3.0))
        self.assertEqual(flow_path(-2.0, 1.0, 1.0), (1.0, 3.0))

    def test_invalid_distribution_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            empirical_distribution(())
        with self.assertRaises(ValueError):
            negative_log_likelihood({-1.0: 1.0}, (1.0,))
        with self.assertRaises(ValueError):
            quantile_samples({-1.0: 0.5}, (0.25,))
        with self.assertRaises(ValueError):
            empirical_distribution((float("nan"),))
        with self.assertRaises(ValueError):
            quantile_samples({-1.0: -1.0, 1.0: 2.0}, (0.25,))

    def test_invalid_probability_path_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            diffusion_forward(1.0, 0.0, True)
        with self.assertRaises(ValueError):
            flow_path(0.0, 1.0, 1.1)
        with self.assertRaises(ValueError):
            diffusion_forward(float("inf"), 0.0, 0.5)


if __name__ == "__main__":
    unittest.main()
