from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from policy_utility import (  # noqa: E402
    POLICIES,
    State,
    evaluate,
    policy_returns,
    rollout,
    spearman_rank_correlation,
    transition,
    transition_agreement,
)


class PolicyUtilityTests(unittest.TestCase):
    def test_safe_route_agrees_in_both_environments(self):
        self.assertEqual(rollout(POLICIES["safe_route"], learned=False), rollout(POLICIES["safe_route"], learned=True))
        self.assertAlmostEqual(policy_returns(learned=False)["safe_route"], 0.85)

    def test_shortcut_is_a_model_blind_spot(self):
        self.assertEqual(rollout(POLICIES["phantom_shortcut"], learned=False)["terminal"], "collision")
        self.assertEqual(rollout(POLICIES["phantom_shortcut"], learned=True)["terminal"], "goal")

    def test_high_transition_accuracy_can_hide_critical_error(self):
        agreement = transition_agreement()
        self.assertEqual(agreement["matching_count"], 8)
        self.assertEqual(agreement["case_count"], 9)
        self.assertEqual(agreement["mismatches"], [{"position": 0, "action": "shortcut"}])

    def test_model_selection_exploits_the_blind_spot(self):
        metrics = evaluate()
        self.assertEqual(metrics["learned_model_selected_policy"], "phantom_shortcut")
        self.assertEqual(metrics["true_best_policy"], "safe_route")
        self.assertEqual(metrics["selected_policy_true_terminal"], "collision")
        self.assertAlmostEqual(metrics["model_exploitation_regret"], 1.85)

    def test_policy_ranking_reverses(self):
        true_returns = policy_returns(learned=False)
        model_returns = policy_returns(learned=True)
        self.assertAlmostEqual(spearman_rank_correlation(true_returns, model_returns), -0.5)

    def test_invalid_actions_and_terminal_reuse_are_rejected(self):
        with self.assertRaises(ValueError):
            transition(State(), "teleport", learned=False)
        with self.assertRaises(ValueError):
            transition(State(terminal="goal"), "wait", learned=False)


if __name__ == "__main__":
    unittest.main()
