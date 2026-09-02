from math import pi, sin
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
    compose_transform,
    control_audit,
    geometry_audit,
    inverse_transform,
    interpolate_planar_pose,
    occupancy_cells,
    pose_interpolation_audit,
    project,
    temporal_alignment_audit,
    temporal_transform_error,
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

    def test_transform_composition_matches_sequential_application(self):
        rotation_world_body = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        translation_world_body = (10.0, -2.0, 0.0)
        rotation_world_camera, translation_world_camera = compose_transform(
            rotation_world_body,
            translation_world_body,
            R_BODY_CAMERA,
            T_BODY_CAMERA_M,
        )
        point_camera = (-0.02, -0.01, 2.0)
        sequential = transform_point(
            transform_point(point_camera, R_BODY_CAMERA, T_BODY_CAMERA_M),
            rotation_world_body,
            translation_world_body,
        )
        composed = transform_point(point_camera, rotation_world_camera, translation_world_camera)
        self.assertEqual(sequential, composed)

    def test_scaling_reflection_and_shear_are_not_rotations(self):
        invalid_rotations = (
            ((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            ((1.0, 0.2, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        )
        for rotation in invalid_rotations:
            with self.subTest(rotation=rotation), self.assertRaises(ValueError):
                transform_point((0.0, 0.0, 1.0), rotation, (0.0, 0.0, 0.0))

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
        with self.assertRaises(ValueError):
            occupancy_cells([(float("inf"), 0.0, 1.0)])
        with self.assertRaises(ValueError):
            occupancy_cells([(0.0, 0.0, 1.0)], True)

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

    def test_linear_timestamp_error_matches_velocity_times_offset(self):
        result = temporal_alignment_audit()["translation_only"]
        self.assertEqual(result["timestamp_offset_s"], -0.1)
        self.assertEqual(result["spatial_error_m"], 0.2)

    def test_rotational_timestamp_error_matches_chord_distance(self):
        result = temporal_alignment_audit()["rotation_only"]
        expected = 2.0 * 10.0 * sin(0.05 / 2.0)
        self.assertAlmostEqual(result["spatial_error_m"], expected)

    def test_timestamp_matched_transform_has_zero_error(self):
        result = temporal_alignment_audit()["timestamp_matched"]
        self.assertEqual(result["timestamp_offset_s"], 0.0)
        self.assertEqual(result["spatial_error_m"], 0.0)

    def test_temporal_transform_rejects_invalid_point_time_and_velocity(self):
        valid = {
            "world_x_velocity_mps": 2.0,
            "yaw_rate_radps": 0.5,
            "sensor_time_s": 1.0,
            "pose_time_s": 0.9,
        }
        with self.assertRaises(ValueError):
            temporal_transform_error((1.0, 2.0), **valid)
        for field, value in (
            ("world_x_velocity_mps", True),
            ("yaw_rate_radps", float("nan")),
            ("sensor_time_s", float("inf")),
        ):
            changed = dict(valid)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                temporal_transform_error((10.0, 0.0, 0.0), **changed)

    def test_pose_interpolation_uses_shortest_yaw_arc_across_wrap(self):
        result = pose_interpolation_audit()["interpolated_pose"]
        self.assertAlmostEqual(abs(result["yaw_rad"]), pi)
        self.assertAlmostEqual(result["shortest_arc_delta_rad"], pi / 9.0)

    def test_naive_angle_average_creates_twenty_metre_point_error(self):
        result = pose_interpolation_audit()
        self.assertEqual(result["shortest_arc_interpolation_error_m"], 0.0)
        self.assertEqual(result["naive_angle_interpolation_error_m"], 20.0)

    def test_pose_interpolation_matches_registered_midpoint_translation(self):
        result = pose_interpolation_audit()["interpolated_pose"]
        self.assertEqual(result["timestamp_s"], 0.5)
        self.assertEqual(result["x_m"], 1.0)
        self.assertEqual(result["y_m"], 0.0)
        self.assertEqual(result["alpha"], 0.5)

    def test_pose_interpolation_rejects_extrapolation_and_unordered_samples(self):
        samples = ((0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.1))
        for query_time in (-0.1, 1.1, float("nan")):
            with self.subTest(query_time=query_time), self.assertRaises(ValueError):
                interpolate_planar_pose(samples, query_time)
        for invalid_samples in (
            ((0.0, 0.0, 0.0, 0.0),),
            ((0.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.1)),
            ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.1)),
        ):
            with self.subTest(samples=invalid_samples), self.assertRaises(ValueError):
                interpolate_planar_pose(invalid_samples, 0.0)


if __name__ == "__main__":
    unittest.main()
