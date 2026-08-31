from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from embodiment_fixture import (  # noqa: E402
    ADAPTERS,
    canonicalize,
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


if __name__ == "__main__":
    unittest.main()
