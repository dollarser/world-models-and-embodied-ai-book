from __future__ import annotations

from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from evaluation_fixture import (  # noqa: E402
    action_blind,
    action_faithful_biased,
    choose_action,
    evaluate,
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


if __name__ == "__main__":
    unittest.main()
