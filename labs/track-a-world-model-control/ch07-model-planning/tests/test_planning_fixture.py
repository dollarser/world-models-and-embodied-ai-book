from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from planning_fixture import (  # noqa: E402
    bellman_backup,
    evaluate,
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

    def test_replanning_recovers_from_fixed_disturbance(self):
        open_loop = execute_with_disturbance(False)
        receding = execute_with_disturbance(True)
        self.assertEqual(open_loop["return"], -0.2)
        self.assertEqual(receding["return"], 0.7)

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


if __name__ == "__main__":
    unittest.main()
