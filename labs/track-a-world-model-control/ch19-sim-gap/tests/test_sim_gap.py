from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from sim_gap import (  # noqa: E402
    CALIBRATION_ACTIONS,
    HELD_OUT_ACTIONS,
    NOMINAL,
    TARGET,
    CalibrationResult,
    SystemParams,
    calibrate,
    compare,
    covers,
    mean_absolute_error,
    rollout,
)


class SimGapTests(unittest.TestCase):
    def test_delay_and_gain_change_applied_actions(self):
        result = rollout(TARGET, HELD_OUT_ACTIONS)
        self.assertEqual(result["applied_actions"], (0.0, 0.5, 1.0, -0.25))
        self.assertEqual(result["states"], (0.0, 0.4, 1.2000000000000002, 1.0000000000000002))

    def test_observation_scale_is_separate_from_dynamics(self):
        result = rollout(TARGET, HELD_OUT_ACTIONS)
        self.assertEqual(result["observations"], tuple(1.25 * state for state in result["states"]))

    def test_nominal_simulator_has_held_out_gap(self):
        gap = compare(NOMINAL, TARGET, HELD_OUT_ACTIONS)
        self.assertAlmostEqual(gap["state_mae"], 0.6625)
        self.assertAlmostEqual(gap["observation_mae"], 0.625)
        self.assertAlmostEqual(gap["terminal_state_error"], 1.0)

    def test_observation_only_calibration_reports_structural_ambiguity(self):
        target_rollout = rollout(TARGET, CALIBRATION_ACTIONS)
        result = calibrate(target_rollout["observations"], CALIBRATION_ACTIONS)
        self.assertIsInstance(result, CalibrationResult)
        self.assertAlmostEqual(result.fit_error, 0.0)
        self.assertEqual(result.candidate_count, 12)
        self.assertFalse(result.identifiable)
        self.assertEqual(len(result.minimizers), 2)
        self.assertIn(TARGET, result.minimizers)
        self.assertIn(SystemParams(1.0, 1, 1.0), result.minimizers)

    def test_observation_equivalent_alternative_hides_held_out_state_gap(self):
        alternative = SystemParams(1.0, 1, 1.0)
        gap = compare(alternative, TARGET, HELD_OUT_ACTIONS)
        self.assertAlmostEqual(gap["observation_mae"], 0.0)
        self.assertAlmostEqual(gap["state_mae"], 0.1625)
        self.assertAlmostEqual(gap["terminal_state_error"], 0.25)

    def test_state_anchor_disambiguates_and_matches_held_out_fixture(self):
        target_rollout = rollout(TARGET, CALIBRATION_ACTIONS)
        result = calibrate(
            target_rollout["observations"],
            CALIBRATION_ACTIONS,
            observed_states=target_rollout["states"],
        )
        self.assertTrue(result.identifiable)
        self.assertEqual(result.minimizers, (TARGET,))
        self.assertEqual(compare(result.selected, TARGET, HELD_OUT_ACTIONS), {
            "state_mae": 0.0,
            "observation_mae": 0.0,
            "terminal_state_error": 0.0,
        })

    def test_calibration_and_metric_inputs_are_validated(self):
        with self.assertRaises(ValueError):
            calibrate((0.0,), CALIBRATION_ACTIONS)
        with self.assertRaises(ValueError):
            calibrate((0.0,) * 4, CALIBRATION_ACTIONS, observed_states=(0.0,))
        with self.assertRaises(ValueError):
            calibrate((0.0, 0.0, math.nan, 0.0), CALIBRATION_ACTIONS)
        with self.assertRaises(ValueError):
            mean_absolute_error((0.0, math.inf), (0.0, 1.0))

    def test_randomization_coverage_is_explicit(self):
        self.assertFalse(covers(TARGET, (0.9, 1.1), (0,), (0.95, 1.05)))
        self.assertTrue(covers(TARGET, (0.7, 1.1), (0, 1), (0.9, 1.3)))

    def test_invalid_parameters_and_actions_are_rejected(self):
        with self.assertRaises(ValueError):
            SystemParams(0.0, 0, 1.0)
        with self.assertRaises(ValueError):
            SystemParams(1.0, True, 1.0)
        with self.assertRaises(ValueError):
            SystemParams(True, 0, 1.0)
        with self.assertRaises(ValueError):
            SystemParams(1.0, 0, float("nan"))
        with self.assertRaises(ValueError):
            rollout(NOMINAL, (True,))
        with self.assertRaises(ValueError):
            rollout(NOMINAL, (float("inf"),))

    def test_malformed_randomization_support_is_rejected(self):
        with self.assertRaises(ValueError):
            covers(TARGET, (1.0, 0.5), (0,), (0.9, 1.3))
        with self.assertRaises(ValueError):
            covers(TARGET, (0.7, 1.1), (True,), (0.9, 1.3))


if __name__ == "__main__":
    unittest.main()
