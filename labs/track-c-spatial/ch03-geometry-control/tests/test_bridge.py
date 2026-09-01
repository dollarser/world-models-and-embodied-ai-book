from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from bridge_fixture import (  # noqa: E402
    R_BODY_CAMERA,
    T_BODY_CAMERA_M,
    backproject,
    backproject_range,
    control_audit,
    geometry_audit,
    inverse_transform,
    occupancy_cells,
    project,
    transform_point,
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

    def test_optical_axes_are_explicitly_mapped_to_body_axes(self):
        self.assertEqual(transform_point((0.0, 0.0, 1.0), R_BODY_CAMERA, (0.0, 0.0, 0.0)), (1.0, 0.0, 0.0))
        self.assertEqual(transform_point((1.0, 0.0, 0.0), R_BODY_CAMERA, (0.0, 0.0, 0.0)), (0.0, -1.0, 0.0))
        self.assertEqual(transform_point((0.0, 1.0, 0.0), R_BODY_CAMERA, (0.0, 0.0, 0.0)), (0.0, 0.0, -1.0))

    def test_rigid_transform_inverse_round_trip(self):
        point = (-0.02, -0.01, 2.0)
        inverse_rotation, inverse_translation = inverse_transform(R_BODY_CAMERA, T_BODY_CAMERA_M)
        body = transform_point(point, R_BODY_CAMERA, T_BODY_CAMERA_M)
        recovered = transform_point(body, inverse_rotation, inverse_translation)
        for actual, expected in zip(recovered, point, strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_z_depth_and_ray_range_are_not_interchangeable_off_axis(self):
        z_depth_point = backproject(101.0, 0.5, 1.0)
        range_point = backproject_range(101.0, 0.5, 1.0)
        self.assertAlmostEqual(sum(value * value for value in range_point), 1.0)
        self.assertAlmostEqual(sum(value * value for value in z_depth_point), 2.0)

    def test_invalid_depth_and_cell_size_are_rejected(self):
        with self.assertRaises(ValueError):
            backproject(0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            occupancy_cells([(0.0, 0.0, 1.0)], 0.0)

    def test_faults_are_measured_in_physical_units(self):
        result = geometry_audit()
        self.assertEqual(result["depth_unit_fault_scale_ratio"], 1000.0)
        self.assertAlmostEqual(result["extrinsic_fault_mean_shift_m"], 0.1)
        self.assertAlmostEqual(result["max_transform_roundtrip_error_m"], 0.0)
        self.assertGreater(result["identity_axis_mapping_mean_error_m"], 0.0)

    def test_invalid_intrinsics_and_nonfinite_transform_are_rejected(self):
        with self.assertRaises(ValueError):
            backproject(0.0, 0.0, 1.0, {"fx": 0.0, "fy": 1.0, "cx": 0.0, "cy": 0.0})
        with self.assertRaises(ValueError):
            transform_point((0.0, 0.0, 1.0), R_BODY_CAMERA, (float("nan"), 0.0, 0.0))

    def test_feedback_reduces_fixed_bias_error(self):
        result = control_audit()
        self.assertLess(result["feedback_endpoint_error_m"], result["open_loop_endpoint_error_m"])

    def test_invalid_control_horizon_is_rejected(self):
        for steps in (0, -1, True, 1.5):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                control_audit(steps)


if __name__ == "__main__":
    unittest.main()
