from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from policy_utility import (  # noqa: E402
    POLICIES,
    State,
    component_attribution_audit,
    evaluate,
    policy_returns,
    rollout,
    spearman_rank_correlation,
    support_gate_audit,
    support_gated_selection,
    support_issues,
    transition,
    transition_agreement,
    proxy_evaluation_scenario,
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

    def test_spearman_uses_average_ranks_for_ties(self):
        first = {"a": 1.0, "b": 1.0, "c": 0.0}
        second = {"a": 2.0, "b": 2.0, "c": -1.0}
        self.assertAlmostEqual(spearman_rank_correlation(first, second), 1.0)
        with self.assertRaises(ValueError):
            spearman_rank_correlation(first, {"a": 1.0, "b": 1.0, "c": 1.0})

    def test_invalid_score_tables_are_rejected(self):
        invalid = (
            ({"a": 1.0}, {"a": 1.0}),
            ({"a": 1.0, "b": math.nan}, {"a": 1.0, "b": 0.0}),
            ({"a": 1.0, "b": True}, {"a": 1.0, "b": 0.0}),
            ({"a": 1.0, "b": 0.0}, {"a": 1.0, "c": 0.0}),
        )
        for first, second in invalid:
            with self.subTest(first=first, second=second), self.assertRaises(ValueError):
                spearman_rank_correlation(first, second)  # type: ignore[arg-type]

    def test_support_gate_rejects_unsupported_shortcut(self):
        self.assertEqual(
            support_issues(POLICIES["phantom_shortcut"]),
            ({"step": 0, "position": 0, "action": "shortcut"},),
        )
        gated = support_gated_selection()
        self.assertEqual(gated["selected_policy"], "safe_route")
        self.assertEqual(gated["selected_policy_true_terminal"], "goal")
        self.assertEqual(gated["model_exploitation_regret"], 0.0)

    def test_support_gate_does_not_detect_an_in_support_model_error(self):
        audit = support_gate_audit()
        in_support = audit["in_support_model_error"]
        self.assertEqual(in_support["rejected_policy_count"], 0)
        self.assertEqual(in_support["selected_policy"], "phantom_shortcut")
        self.assertEqual(in_support["selected_policy_true_terminal"], "collision")
        self.assertAlmostEqual(in_support["model_exploitation_regret"], 1.85)

    def test_invalid_support_declarations_are_rejected(self):
        invalid = (
            {(0, "advance")},
            frozenset({(True, "advance")}),
            frozenset({(0, "teleport")}),
            frozenset({(4, "wait")}),
        )
        for support in invalid:
            with self.subTest(support=support), self.assertRaises(ValueError):
                support_gated_selection(support)  # type: ignore[arg-type]

    def test_state_and_model_selector_contracts_are_validated(self):
        invalid_states = (
            {"position": True},
            {"position": -1},
            {"position": 4},
            {"position": 0, "terminal": "goal"},
            {"position": 0, "terminal": "unknown"},
        )
        for kwargs in invalid_states:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                State(**kwargs)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            transition(State(), "wait", learned=1)  # type: ignore[arg-type]

    def test_invalid_actions_and_terminal_reuse_are_rejected(self):
        with self.assertRaises(ValueError):
            transition(State(), "teleport", learned=False)
        with self.assertRaises(ValueError):
            transition(State(terminal="goal"), "wait", learned=False)

    def test_oracle_proxy_pipeline_preserves_the_true_ranking(self):
        oracle = proxy_evaluation_scenario()
        self.assertEqual(oracle["selected_policy"], "safe_route")
        self.assertEqual(oracle["model_exploitation_regret"], 0.0)
        self.assertEqual(oracle["spearman_rank_correlation"], 1.0)

    def test_each_component_fault_can_change_the_selected_policy(self):
        expected = {
            "action_grounding": "idle",
            "transition_model": "phantom_shortcut",
            "state_decoder": "phantom_shortcut",
            "outcome_scorer": "phantom_shortcut",
        }
        for component, selected in expected.items():
            with self.subTest(component=component):
                scenario = proxy_evaluation_scenario(component)
                self.assertEqual(scenario["selected_policy"], selected)
                self.assertGreater(scenario["model_exploitation_regret"], 0.0)

    def test_three_fault_locations_are_observationally_equivalent_end_to_end(self):
        audit = component_attribution_audit()
        self.assertTrue(audit["equivalent_end_to_end_scores"])
        scenarios = audit["scenarios"]
        self.assertEqual(
            scenarios["transition_model"]["proxy_scores"],
            scenarios["state_decoder"]["proxy_scores"],
        )
        self.assertEqual(
            scenarios["state_decoder"]["proxy_scores"],
            scenarios["outcome_scorer"]["proxy_scores"],
        )
        traces = audit["phantom_shortcut_localization_traces"]
        self.assertNotEqual(
            traces["transition_model"],
            traces["state_decoder"],
        )

    def test_proxy_pipeline_rejects_unknown_faults(self):
        with self.assertRaises(ValueError):
            proxy_evaluation_scenario("combined")


if __name__ == "__main__":
    unittest.main()
