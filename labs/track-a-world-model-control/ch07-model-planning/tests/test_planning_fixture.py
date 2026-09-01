from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from planning_fixture import (  # noqa: E402
    bellman_backup,
    empirical_lower_tail_mean,
    evaluate,
    evaluate_risk_objectives,
    execute_with_disturbance,
    plan,
    rollout,
    transition,
)


class ModelPlanningTests(unittest.TestCase):
    def test_short_horizon_is_myopic(self):
        result = plan(0, 1)
        self.assertEqual(result["actions"], ("harvest",))
        self.assertEqual(result["predicted_return"], 0.0)

    def test_long_horizon_finds_delayed_reward(self):
        result = plan(0, 3)
        self.assertEqual(result["actions"], ("advance", "advance", "harvest"))
        self.assertEqual(result["predicted_return"], 0.8)
        self.assertEqual(result["candidate_count"], 8)

    def test_terminal_value_extends_short_horizon(self):
        result = plan(0, 1, {0: 0.8, 1: 0.9, 2: 1.0})
        self.assertEqual(result["actions"], ("advance",))
        self.assertEqual(result["predicted_return"], 0.8)

    def test_legacy_replanning_result_exposes_unequal_budget(self):
        open_loop = execute_with_disturbance(False)
        receding = execute_with_disturbance(True)
        self.assertEqual(open_loop["return"], -0.2)
        self.assertEqual(receding["return"], 0.7)
        self.assertEqual(open_loop["post_disturbance_action_budget"], 2)
        self.assertEqual(receding["post_disturbance_action_budget"], 3)

    def test_fixed_budget_reward_only_comparison_is_like_for_like(self):
        open_loop = execute_with_disturbance(False, 2)
        receding = execute_with_disturbance(True, 2)
        self.assertEqual(open_loop["post_disturbance_action_budget"], 2)
        self.assertEqual(receding["post_disturbance_action_budget"], 2)
        self.assertEqual(open_loop["environment_return"], -0.2)
        self.assertEqual(receding["environment_return"], -0.1)
        self.assertEqual(receding["post_disturbance_executed_actions"], ("harvest",))

    def test_fixed_budget_terminal_value_is_not_environment_return(self):
        values = {0: 0.8, 1: 0.9, 2: 1.0}
        open_loop = execute_with_disturbance(False, 2, values)
        receding = execute_with_disturbance(True, 2, values)
        self.assertEqual(open_loop["return"], -0.2)
        self.assertEqual(receding["environment_return"], -0.3)
        self.assertEqual(receding["terminal_value_contribution"], 1.0)
        self.assertEqual(receding["return"], 0.7)
        self.assertFalse(receding["terminated"])

    def test_disturbance_protocol_rejects_ambiguous_or_invalid_budgets(self):
        with self.assertRaises(ValueError):
            execute_with_disturbance(1)
        with self.assertRaises(ValueError):
            execute_with_disturbance(True, 0)
        with self.assertRaises(ValueError):
            execute_with_disturbance(True, 3)
        with self.assertRaises(ValueError):
            execute_with_disturbance(True, terminal_values={0: 0.8, 1: 0.9, 2: 1.0})

    def test_value_fixture_ignores_observation_labels(self):
        result = evaluate()["value_equivalence_fixture"]
        self.assertEqual(result["observation_match_rate"], 0.0)
        self.assertEqual(result["max_bellman_backup_gap"], 0.0)

    def test_rollout_stops_after_terminal_action(self):
        result = rollout(0, ("harvest", "advance"))
        self.assertEqual(result["executed_actions"], ("harvest",))
        self.assertTrue(result["terminated"])

    def test_invalid_state_action_and_horizon_are_rejected(self):
        with self.assertRaises(ValueError):
            transition(True, "advance")
        with self.assertRaises(ValueError):
            transition(0, "teleport")
        with self.assertRaises(ValueError):
            plan(0, 0)
        with self.assertRaises(ValueError):
            bellman_backup(0, {0: 0.0})

    def test_mean_return_and_lower_tail_select_different_actions(self):
        result = evaluate_risk_objectives()
        self.assertEqual(result["mean_selected_action"], "risky")
        self.assertEqual(result["worst_20_percent_selected_action"], "steady")
        self.assertEqual(result["actions"]["risky"]["mean_return"], 0.8)
        self.assertEqual(result["actions"]["risky"]["worst_20_percent_return"], -2.0)

    def test_chance_constraint_rejects_the_risky_action(self):
        result = evaluate_risk_objectives()
        self.assertEqual(result["chance_feasible_actions"], ["steady"])
        self.assertEqual(result["actions"]["risky"]["failure_probability"], 0.2)

    def test_tail_metric_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            empirical_lower_tail_mean((), 0.2)
        with self.assertRaises(ValueError):
            empirical_lower_tail_mean((1.0, float("nan")), 0.2)
        with self.assertRaises(ValueError):
            empirical_lower_tail_mean((1.0,), True)


if __name__ == "__main__":
    unittest.main()
