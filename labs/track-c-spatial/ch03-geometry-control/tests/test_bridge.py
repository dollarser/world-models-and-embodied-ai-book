from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from bridge_fixture import (  # noqa: E402
    backproject,
    control_audit,
    geometry_audit,
    occupancy_cells,
    project,
    transform_yaw_translation,
)


class GeometryControlBridgeTests(unittest.TestCase):
    def test_projection_round_trip(self):
        point = backproject(0.0, 0.0, 2.0)
        self.assertEqual(point, (-0.02, -0.01, 2.0))
        u, v = project(point)
        self.assertAlmostEqual(u, 0.0)
        self.assertAlmostEqual(v, 0.0)

    def test_transform_direction_is_explicit(self):
        self.assertEqual(transform_yaw_translation((1.0, 2.0, 3.0), 0.0, (0.5, -0.5, 1.0)), (1.5, 1.5, 4.0))

    def test_invalid_depth_and_cell_size_are_rejected(self):
        with self.assertRaises(ValueError):
            backproject(0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            occupancy_cells([(0.0, 0.0, 1.0)], 0.0)

    def test_faults_are_measured_in_physical_units(self):
        result = geometry_audit()
        self.assertEqual(result["depth_unit_fault_scale_ratio"], 1000.0)
        self.assertAlmostEqual(result["extrinsic_fault_mean_shift_m"], 0.1)

    def test_feedback_reduces_fixed_bias_error(self):
        result = control_audit()
        self.assertLess(result["feedback_endpoint_error_m"], result["open_loop_endpoint_error_m"])


if __name__ == "__main__":
    unittest.main()
