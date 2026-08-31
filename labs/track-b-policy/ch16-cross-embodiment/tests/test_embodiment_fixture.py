from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from embodiment_fixture import (  # noqa: E402
    ADAPTERS,
    EmbodimentAdapter,
    canonicalize,
    mean_action,
    maximum_round_trip_error,
    naive_raw_pooling_error,
    schema_aware_pooling_error,
)


class EmbodimentAdapterTests(unittest.TestCase):
    def test_arm_a_uses_controller_delta_and_positive_gripper(self):
        self.assertEqual(ADAPTERS["arm_a"].to_canonical((0.2, 1.0)), (0.020000000000000004, 1.0))

    def test_arm_b_uses_centimeters_and_reversed_gripper(self):
        self.assertEqual(ADAPTERS["arm_b"].to_canonical((2.0, -1.0)), (0.02, 1.0))

    def test_each_adapter_round_trips_its_own_convention(self):
        self.assertAlmostEqual(maximum_round_trip_error(), 0.0)

    def test_naive_raw_pooling_changes_semantics(self):
        self.assertAlmostEqual(naive_raw_pooling_error(), 0.28375)

    def test_schema_aware_pooling_aligns_targets(self):
        self.assertAlmostEqual(schema_aware_pooling_error(), 0.0)

    def test_missing_embodiment_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            canonicalize({"episode_id": "x", "task": "forward_open", "raw_action": (0.2, 1.0)})

    def test_gripper_ranges_are_validated(self):
        with self.assertRaises(ValueError):
            ADAPTERS["arm_a"].to_canonical((0.0, 2.0))
        with self.assertRaises(ValueError):
            ADAPTERS["arm_a"].from_canonical((0.0, -0.1))

    def test_non_finite_boolean_and_malformed_actions_are_rejected(self):
        invalid_actions = ((True, 0.0), (math.nan, 0.0), (math.inf, 0.0), (0.0,))
        for action in invalid_actions:
            with self.subTest(action=action), self.assertRaises(ValueError):
                ADAPTERS["arm_a"].to_canonical(action)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            mean_action(())

    def test_invalid_adapter_metadata_is_rejected(self):
        invalid_configs = (
            {"embodiment_id": "", "delta_x_unit": "m", "delta_x_scale_to_m": 1.0, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": 0.0, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": math.inf, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": 1.0, "gripper_polarity": True},
        )
        for config in invalid_configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                EmbodimentAdapter(**config)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
