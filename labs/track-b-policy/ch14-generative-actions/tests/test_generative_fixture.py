from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from generative_fixture import (  # noqa: E402
    candidate_availability_audit,
    conditional_mean,
    mode_frequency_report,
    mode_refinement,
    nearest_mode_distance,
    oracle_straight_flow,
    sampling_budget_report,
    screen_candidates,
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

    def test_mode_coverage_does_not_measure_frequency_calibration(self):
        balanced = mode_frequency_report((-1.0,) * 5 + (1.0,) * 5)
        imbalanced = mode_frequency_report((-1.0,) * 9 + (1.0,))
        self.assertEqual(balanced["valid_action_rate"], imbalanced["valid_action_rate"])
        self.assertEqual(balanced["covered_mode_count"], imbalanced["covered_mode_count"])
        self.assertEqual(balanced["empirical_total_variation_to_target"], 0.0)
        self.assertEqual(imbalanced["empirical_total_variation_to_target"], 0.4)

    def test_mode_frequency_report_preserves_mode_counts(self):
        report = mode_frequency_report((-1.0,) * 9 + (1.0,))
        self.assertEqual(report["negative_mode_count"], 9)
        self.assertEqual(report["positive_mode_count"], 1)
        self.assertEqual(report["negative_mode_empirical_probability"], 0.9)

    def test_mode_frequency_report_rejects_invalid_contracts(self):
        invalid_cases = (
            ((), (0.5, 0.5)),
            ((0.0,), (0.5, 0.5)),
            ((-1.0, 1.0), (0.7, 0.4)),
            ((-1.0, 1.0), (-0.1, 1.1)),
            ((-1.0, 1.0), (True, 0.0)),
        )
        for samples, probabilities in invalid_cases:
            with self.subTest(samples=samples, probabilities=probabilities), self.assertRaises(ValueError):
                mode_frequency_report(samples, probabilities)

    def test_sampling_budget_is_per_replan(self):
        sequential = sampling_budget_report(4, 10, 1, 8)
        batched = sampling_budget_report(4, 10, 10, 8)
        self.assertEqual(sequential["forward_pass_count"], 40)
        self.assertFalse(sequential["fits_abstract_forward_budget"])
        self.assertEqual(batched["forward_pass_count"], 4)
        self.assertTrue(batched["fits_abstract_forward_budget"])

    def test_budget_rejects_invalid_counts(self):
        with self.assertRaises(ValueError):
            sampling_budget_report(0, 10, 10, 8)
        with self.assertRaises(ValueError):
            sampling_budget_report(4, 0, 10, 8)
        with self.assertRaises(ValueError):
            sampling_budget_report(4, 10, 0, 8)
        with self.assertRaises(ValueError):
            sampling_budget_report(4, 10, 10, -1)

    def test_iid_candidate_availability_uses_best_of_n_formula(self):
        rows = candidate_availability_audit()
        self.assertEqual([row["candidate_count"] for row in rows], [1, 4, 16])
        self.assertEqual(rows[0]["iid_any_accepted_probability"], 0.2)
        self.assertEqual(rows[1]["iid_any_accepted_probability"], 0.5904)
        self.assertEqual(rows[2]["iid_any_accepted_probability"], 0.971852502329)
        self.assertEqual(rows[2]["sample_model_evaluation_count"], 64)
        self.assertEqual(rows[2]["forward_pass_count"], 8)

    def test_perfect_correlation_erases_best_of_n_gain(self):
        rows = candidate_availability_audit()
        self.assertEqual(
            {row["perfectly_correlated_any_accepted_probability"] for row in rows},
            {0.2},
        )
        self.assertGreater(
            rows[-1]["iid_any_accepted_probability"],
            rows[-1]["perfectly_correlated_any_accepted_probability"],
        )

    def test_iid_more_candidates_reduce_fallback_probability(self):
        rows = candidate_availability_audit()
        probabilities = [row["iid_fallback_probability"] for row in rows]
        self.assertEqual(probabilities, sorted(probabilities, reverse=True))
        self.assertEqual(rows[-1]["perfectly_correlated_fallback_probability"], 0.8)

    def test_candidate_availability_rejects_invalid_contracts(self):
        invalid_cases = (
            {"per_candidate_acceptance_probability": -0.1},
            {"per_candidate_acceptance_probability": 1.1},
            {"per_candidate_acceptance_probability": True},
            {"candidate_counts": ()},
            {"candidate_counts": (1, 1)},
            {"candidate_counts": (1, 0)},
            {"candidate_counts": [1, 4]},
            {"solver_steps": 0},
            {"batch_capacity": 0},
        )
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                candidate_availability_audit(**kwargs)

    def test_safety_screen_reports_explicit_denominators(self):
        report = screen_candidates((-1.0, 1.0, 0.0))
        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["valid_action_count"], 2)
        self.assertEqual(report["invalid_action_count"], 1)
        self.assertEqual(report["safety_rejected_valid_count"], 1)
        self.assertEqual(report["safety_accepted_count"], 1)
        self.assertFalse(report["fallback_used"])
        self.assertEqual(report["selected_action"], 1.0)
        with self.assertRaises(ValueError):
            screen_candidates(())
        with self.assertRaises(ValueError):
            screen_candidates((1.0,), blocked_interval=(1.0, -1.0))

    def test_all_safety_rejected_candidates_use_fallback(self):
        report = screen_candidates((-1.0, -1.0), fallback_action=0.0)
        self.assertTrue(report["fallback_used"])
        self.assertEqual(report["safety_accepted_count"], 0)
        self.assertEqual(report["selected_action"], 0.0)

    def test_conditional_mean_requires_finite_nonempty_demonstrations(self):
        with self.assertRaises(ValueError):
            conditional_mean(())
        with self.assertRaises(ValueError):
            conditional_mean((float("nan"),))

    def test_summary_requires_finite_nonempty_samples(self):
        with self.assertRaises(ValueError):
            summarize(())
        with self.assertRaises(ValueError):
            summarize((float("inf"),))

    def test_scalar_sampler_inputs_reject_nonfinite_values(self):
        with self.assertRaises(ValueError):
            mode_refinement(float("nan"), steps=1)
        with self.assertRaises(ValueError):
            oracle_straight_flow(float("inf"), steps=1)

    def test_refinement_rate_has_a_bounded_contract(self):
        with self.assertRaises(ValueError):
            mode_refinement(0.5, steps=1, rate=0.0)
        with self.assertRaises(ValueError):
            mode_refinement(0.5, steps=1, rate=1.1)


if __name__ == "__main__":
    unittest.main()
