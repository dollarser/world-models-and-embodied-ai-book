from __future__ import annotations

from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from evaluation_fixture import (  # noqa: E402
    action_blind,
    action_faithful_biased,
    action_sensitivity,
    binary_probability_report,
    choose_action,
    evaluate,
    horizon_error_report,
    missing_rollout_diagnostic,
    probability_metric_diagnostic,
    rmse,
    run_episode,
)


class EvaluationFixtureTest(unittest.TestCase):
    def test_action_blind_predictor_ignores_intervention(self) -> None:
        self.assertEqual(action_blind(0.2, -0.1), action_blind(0.2, 0.1))

    def test_action_faithful_predictor_changes_action_ranking(self) -> None:
        left = choose_action(action_faithful_biased, state=0.0, goal=-1.0)
        right = choose_action(action_faithful_biased, state=0.0, goal=1.0)
        self.assertEqual(left, -0.1)
        self.assertEqual(right, 0.1)

    def test_fixture_exposes_metric_ranking_reversal(self) -> None:
        metrics = evaluate()
        action_blind_metrics = metrics["action_blind"]
        action_faithful_metrics = metrics["action_faithful_biased"]
        self.assertLess(action_blind_metrics["one_step_rmse"], action_faithful_metrics["one_step_rmse"])
        self.assertLess(
            action_blind_metrics["closed_loop_success_rate"],
            action_faithful_metrics["closed_loop_success_rate"],
        )

    def test_action_sensitivity_is_explicitly_measured(self) -> None:
        self.assertEqual(action_sensitivity(action_blind), 0.0)
        self.assertAlmostEqual(action_sensitivity(action_faithful_biased), 0.2)

    def test_horizon_report_preserves_attempted_denominator(self) -> None:
        report = horizon_error_report(((0.1, 0.2), (0.1, None)), missing_penalty=1.0)
        self.assertEqual(report[1]["attempted_count"], 2)
        self.assertEqual(report[1]["available_count"], 1)
        self.assertEqual(report[1]["coverage"], 0.5)
        self.assertEqual(report[1]["available_case_mean_error"], 0.2)
        self.assertEqual(report[1]["fixed_denominator_mean_error"], 0.6)

    def test_missing_rollouts_reverse_terminal_ranking(self) -> None:
        result = missing_rollout_diagnostic()
        stable = result["stable"][-1]
        fragile = result["fragile"][-1]
        self.assertLess(fragile["available_case_mean_error"], stable["available_case_mean_error"])
        self.assertGreater(fragile["fixed_denominator_mean_error"], stable["fixed_denominator_mean_error"])
        self.assertEqual(fragile["coverage"], 1 / 3)

    def test_invalid_horizon_tables_are_rejected(self) -> None:
        cases = (
            (),
            ((),),
            ((0.1,), (0.1, 0.2)),
            ((0.1, None, 0.2),),
            ((0.1, -0.2),),
            ((0.1, float("nan")),),
            ((None,),),
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                horizon_error_report(rows, missing_penalty=1.0)

    def test_invalid_missing_penalties_are_rejected(self) -> None:
        for penalty in (-1.0, True, float("inf")):
            with self.subTest(penalty=penalty), self.assertRaises(ValueError):
                horizon_error_report(((0.1,),), missing_penalty=penalty)

    def test_coarse_ece_ties_forecasts_that_proper_scores_separate(self) -> None:
        diagnostic = probability_metric_diagnostic()
        uniform = diagnostic["uniform_base_rate"]
        informative = diagnostic["informative"]
        self.assertEqual(uniform["one_bin_ece"], 0.0)
        self.assertEqual(informative["one_bin_ece"], 0.0)
        self.assertLess(informative["brier_loss"], uniform["brier_loss"])
        self.assertLess(informative["log_loss"], uniform["log_loss"])

    def test_fixed_bin_ece_changes_with_registered_bins(self) -> None:
        diagnostic = probability_metric_diagnostic()
        informative = diagnostic["informative"]
        self.assertAlmostEqual(informative["two_bin_ece"], 0.1)
        self.assertGreater(informative["probability_variance"], 0.0)
        self.assertEqual(diagnostic["uniform_base_rate"]["probability_variance"], 0.0)

    def test_probability_report_rejects_invalid_contracts(self) -> None:
        cases = (
            ((), (), (0.0, 1.0)),
            ((True,), (0.5, 0.5), (0.0, 1.0)),
            ((1,), (0.5,), (0.0, 1.0)),
            ((True,), (0.0,), (0.0, 1.0)),
            ((True,), (float("nan"),), (0.0, 1.0)),
            ((True,), (0.5,), (0.0, 0.5, 0.5, 1.0)),
            ((True,), (0.5,), (0.1, 1.0)),
        )
        for outcomes, probabilities, edges in cases:
            with self.subTest(outcomes=outcomes, probabilities=probabilities, edges=edges):
                with self.assertRaises(ValueError):
                    binary_probability_report(outcomes, probabilities, bin_edges=edges)

    def test_invalid_episode_and_metric_inputs_are_rejected(self) -> None:
        for kwargs in ({"start": float("nan")}, {"goal": True}, {"steps": 0}, {"steps": False}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                run_episode(
                    action_blind,
                    start=kwargs.get("start", 0.0),
                    goal=kwargs.get("goal", 1.0),
                    steps=kwargs.get("steps", 2),
                )
        with self.assertRaises(ValueError):
            choose_action(lambda state, action: float("nan"), state=0.0, goal=1.0)
        for values in ((), (True,), (float("inf"),)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                rmse(values)


if __name__ == "__main__":
    unittest.main()
