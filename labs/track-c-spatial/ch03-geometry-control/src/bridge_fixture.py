"""Zero-download geometry and feedback-control fixtures for Chapter 3."""

from __future__ import annotations

from math import cos, floor, hypot, isclose, isfinite, sin, sqrt


INTRINSICS = {"fx": 100.0, "fy": 100.0, "cx": 1.0, "cy": 0.5}
RGBD_SAMPLES = ((0.0, 0.0, 2.0), (1.0, 0.5, 1.0), (2.0, 1.0, 2.0))
IDENTITY_ROTATION = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
# camera optical (right, down, forward) -> body (forward, left, up)
R_BODY_CAMERA = ((0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0))
T_BODY_CAMERA_M = (0.5, 0.0, 0.2)
R_WORLD_BODY = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
T_WORLD_BODY_M = (10.0, -2.0, 0.0)


def _finite_vector(values: tuple[float, ...], name: str, length: int) -> tuple[float, ...]:
    if not isinstance(values, tuple) or len(values) != length:
        raise ValueError(f"{name} must be a {length}-element tuple")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in values):
        raise ValueError(f"{name} values must be finite real numbers")
    return tuple(float(value) for value in values)


def _checked_intrinsics(intrinsics: dict[str, float]) -> dict[str, float]:
    if set(intrinsics) != {"fx", "fy", "cx", "cy"}:
        raise ValueError("intrinsics must contain exactly fx, fy, cx, and cy")
    checked = {name: _finite_vector((value,), name, 1)[0] for name, value in intrinsics.items()}
    if checked["fx"] <= 0.0 or checked["fy"] <= 0.0:
        raise ValueError("focal lengths must be positive")
    return checked


def _checked_rotation(
    rotation: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], ...]:
    if not isinstance(rotation, tuple) or len(rotation) != 3:
        raise ValueError("rotation must be a 3-by-3 tuple")
    rows = tuple(_finite_vector(row, "rotation row", 3) for row in rotation)
    for row_index in range(3):
        for other_index in range(3):
            dot = sum(rows[row_index][column] * rows[other_index][column] for column in range(3))
            expected = 1.0 if row_index == other_index else 0.0
            if not isclose(dot, expected, rel_tol=0.0, abs_tol=1e-9):
                raise ValueError("rotation must be orthonormal")
    determinant = (
        rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
        - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
        + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])
    )
    if not isclose(determinant, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("rotation must have determinant +1")
    return rows


def backproject(u: float, v: float, depth_m: float, intrinsics: dict[str, float] = INTRINSICS) -> tuple[float, float, float]:
    """Back-project one pinhole-camera pixel into the camera frame."""
    u, v, depth_m = _finite_vector((u, v, depth_m), "pixel and depth", 3)
    intrinsics = _checked_intrinsics(intrinsics)
    if depth_m <= 0:
        raise ValueError("depth must be positive and expressed in metres")
    x = (u - intrinsics["cx"]) * depth_m / intrinsics["fx"]
    y = (v - intrinsics["cy"]) * depth_m / intrinsics["fy"]
    return (x, y, depth_m)


def backproject_range(u: float, v: float, range_m: float, intrinsics: dict[str, float] = INTRINSICS) -> tuple[float, float, float]:
    """Back-project a Euclidean ray range rather than optical-axis z-depth."""
    u, v, range_m = _finite_vector((u, v, range_m), "pixel and range", 3)
    intrinsics = _checked_intrinsics(intrinsics)
    if range_m <= 0.0:
        raise ValueError("range must be positive and expressed in metres")
    nx = (u - intrinsics["cx"]) / intrinsics["fx"]
    ny = (v - intrinsics["cy"]) / intrinsics["fy"]
    z = range_m / sqrt(nx * nx + ny * ny + 1.0)
    return (nx * z, ny * z, z)


def project(point: tuple[float, float, float], intrinsics: dict[str, float] = INTRINSICS) -> tuple[float, float]:
    """Project a camera-frame point back into pixel coordinates."""
    x, y, z = _finite_vector(point, "point", 3)
    intrinsics = _checked_intrinsics(intrinsics)
    if z <= 0:
        raise ValueError("point must lie in front of the camera")
    return (intrinsics["fx"] * x / z + intrinsics["cx"], intrinsics["fy"] * y / z + intrinsics["cy"])


def transform_point(
    point: tuple[float, float, float],
    rotation: tuple[tuple[float, float, float], ...],
    translation: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Apply p_target = R_target_source p_source + t_target_source."""
    point = _finite_vector(point, "point", 3)
    translation = _finite_vector(translation, "translation", 3)
    rows = _checked_rotation(rotation)
    return tuple(sum(row[index] * point[index] for index in range(3)) + translation[row_index] for row_index, row in enumerate(rows))


def compose_transform(
    rotation_target_middle: tuple[tuple[float, float, float], ...],
    translation_target_middle: tuple[float, float, float],
    rotation_middle_source: tuple[tuple[float, float, float], ...],
    translation_middle_source: tuple[float, float, float],
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    """Compose T_target_middle with T_middle_source in that order."""
    target_middle = _checked_rotation(rotation_target_middle)
    middle_source = _checked_rotation(rotation_middle_source)
    translation_target_middle = _finite_vector(
        translation_target_middle, "target-middle translation", 3
    )
    translation_middle_source = _finite_vector(
        translation_middle_source, "middle-source translation", 3
    )
    rotation_target_source = tuple(
        tuple(
            sum(target_middle[row][index] * middle_source[index][column] for index in range(3))
            for column in range(3)
        )
        for row in range(3)
    )
    translation_target_source = transform_point(
        translation_middle_source, target_middle, translation_target_middle
    )
    return _checked_rotation(rotation_target_source), translation_target_source


def inverse_transform(
    rotation: tuple[tuple[float, float, float], ...],
    translation: tuple[float, float, float],
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    """Invert a rigid transform whose rotation is assumed orthonormal."""
    rotation = _checked_rotation(rotation)
    translation = _finite_vector(translation, "translation", 3)
    transpose = tuple(tuple(rotation[column][row] for column in range(3)) for row in range(3))
    inverse_translation = tuple(-sum(transpose[row][column] * translation[column] for column in range(3)) for row in range(3))
    return transpose, inverse_translation


def transform_yaw_translation(
    point: tuple[float, float, float], yaw_rad: float, translation_m: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Apply p_target = R_target_source p_source + t_target_source."""
    if isinstance(yaw_rad, bool) or not isinstance(yaw_rad, (int, float)) or not isfinite(yaw_rad):
        raise ValueError("yaw must be a finite real number")
    rotation = (
        (cos(yaw_rad), -sin(yaw_rad), 0.0),
        (sin(yaw_rad), cos(yaw_rad), 0.0),
        (0.0, 0.0, 1.0),
    )
    return transform_point(point, rotation, translation_m)


def temporal_transform_error(
    point_body_m: tuple[float, float, float],
    *,
    world_x_velocity_mps: float,
    yaw_rate_radps: float,
    sensor_time_s: float,
    pose_time_s: float,
) -> dict[str, object]:
    """Measure using a pose from the wrong time for one body-frame point.

    The authored motion model uses constant world-x translation and constant
    yaw. It isolates timestamp mechanics; it is not a vehicle-motion model or
    a sensor-calibration routine.
    """

    point_body_m = _finite_vector(point_body_m, "body point", 3)
    world_x_velocity_mps, yaw_rate_radps, sensor_time_s, pose_time_s = _finite_vector(
        (world_x_velocity_mps, yaw_rate_radps, sensor_time_s, pose_time_s),
        "temporal transform parameters",
        4,
    )

    def world_point_at(timestamp_s: float) -> tuple[float, float, float]:
        return transform_yaw_translation(
            point_body_m,
            yaw_rate_radps * timestamp_s,
            (world_x_velocity_mps * timestamp_s, 0.0, 0.0),
        )

    timestamp_matched_point = world_point_at(sensor_time_s)
    pose_time_point = world_point_at(pose_time_s)
    spatial_error = sqrt(
        sum(
            (pose_time_point[index] - timestamp_matched_point[index]) ** 2
            for index in range(3)
        )
    )
    return {
        "sensor_time_s": sensor_time_s,
        "pose_time_s": pose_time_s,
        "timestamp_offset_s": round(pose_time_s - sensor_time_s, 12),
        "world_x_velocity_mps": world_x_velocity_mps,
        "yaw_rate_radps": yaw_rate_radps,
        "point_range_m": sqrt(sum(value * value for value in point_body_m)),
        "timestamp_matched_world_point_m": tuple(round(value, 12) for value in timestamp_matched_point),
        "pose_time_world_point_m": tuple(round(value, 12) for value in pose_time_point),
        "spatial_error_m": round(spatial_error, 12),
    }


def temporal_alignment_audit() -> dict[str, object]:
    """Return fixed translation-only, rotation-only, and matched-time cases."""

    point = (10.0, 0.0, 0.0)
    return {
        "translation_only": temporal_transform_error(
            point,
            world_x_velocity_mps=2.0,
            yaw_rate_radps=0.0,
            sensor_time_s=1.0,
            pose_time_s=0.9,
        ),
        "rotation_only": temporal_transform_error(
            point,
            world_x_velocity_mps=0.0,
            yaw_rate_radps=0.5,
            sensor_time_s=1.0,
            pose_time_s=0.9,
        ),
        "timestamp_matched": temporal_transform_error(
            point,
            world_x_velocity_mps=2.0,
            yaw_rate_radps=0.5,
            sensor_time_s=1.0,
            pose_time_s=1.0,
        ),
        "scope": "constant world-x velocity and yaw-rate timestamp fixture; not motion estimation",
    }


def occupancy_cells(points: list[tuple[float, float, float]], cell_size_m: float = 0.25) -> list[tuple[int, int]]:
    """Rasterize horizontal x-y positions into occupied BEV cells."""
    if (
        isinstance(cell_size_m, bool)
        or not isinstance(cell_size_m, (int, float))
        or not isfinite(cell_size_m)
        or cell_size_m <= 0
    ):
        raise ValueError("cell size must be a positive finite number")
    if not isinstance(points, (list, tuple)):
        raise ValueError("points must be a list or tuple of 3D tuples")
    checked_points = tuple(_finite_vector(point, "point", 3) for point in points)
    return sorted({(floor(x / cell_size_m), floor(y / cell_size_m)) for x, y, _ in checked_points})


def geometry_audit() -> dict[str, object]:
    camera_points = [backproject(*sample) for sample in RGBD_SAMPLES]
    body_points = [transform_point(point, R_BODY_CAMERA, T_BODY_CAMERA_M) for point in camera_points]
    reprojection_errors = [
        hypot(project(point)[0] - sample[0], project(point)[1] - sample[1])
        for point, sample in zip(camera_points, RGBD_SAMPLES)
    ]
    scale_fault_points = [backproject(u, v, depth * 1000.0) for u, v, depth in RGBD_SAMPLES]
    scale_ratio = sum(point[2] for point in scale_fault_points) / sum(point[2] for point in camera_points)
    shifted = [transform_point(point, R_BODY_CAMERA, (0.6, 0.0, 0.2)) for point in camera_points]
    mean_extrinsic_shift = sum(abs(bad[0] - good[0]) for bad, good in zip(shifted, body_points)) / len(body_points)
    inverse_rotation, inverse_translation = inverse_transform(R_BODY_CAMERA, T_BODY_CAMERA_M)
    recovered_camera_points = [transform_point(point, inverse_rotation, inverse_translation) for point in body_points]
    transform_roundtrip_errors = [
        sqrt(sum((recovered[index] - original[index]) ** 2 for index in range(3)))
        for recovered, original in zip(recovered_camera_points, camera_points, strict=True)
    ]
    identity_axis_points = [transform_point(point, IDENTITY_ROTATION, T_BODY_CAMERA_M) for point in camera_points]
    identity_axis_error = sum(
        sqrt(sum((bad[index] - good[index]) ** 2 for index in range(3)))
        for bad, good in zip(identity_axis_points, body_points, strict=True)
    ) / len(body_points)
    off_axis_z_depth = backproject(101.0, 0.5, 1.0)
    rotation_world_camera, translation_world_camera = compose_transform(
        R_WORLD_BODY,
        T_WORLD_BODY_M,
        R_BODY_CAMERA,
        T_BODY_CAMERA_M,
    )
    sequential_world_points = [
        transform_point(point, R_WORLD_BODY, T_WORLD_BODY_M) for point in body_points
    ]
    composed_world_points = [
        transform_point(point, rotation_world_camera, translation_world_camera)
        for point in camera_points
    ]
    transform_chain_errors = [
        sqrt(sum((sequential[index] - composed[index]) ** 2 for index in range(3)))
        for sequential, composed in zip(sequential_world_points, composed_world_points, strict=True)
    ]
    return {
        "point_count": len(camera_points),
        "max_reprojection_error_px": max(reprojection_errors),
        "depth_unit_fault_scale_ratio": scale_ratio,
        "extrinsic_fault_mean_shift_m": mean_extrinsic_shift,
        "max_transform_roundtrip_error_m": max(transform_roundtrip_errors),
        "identity_axis_mapping_mean_error_m": identity_axis_error,
        "off_axis_z_depth_to_range_ratio": sqrt(sum(value * value for value in off_axis_z_depth)),
        "max_transform_chain_gap_m": max(transform_chain_errors),
        "optical_forward_axis_in_body": transform_point((0.0, 0.0, 1.0), R_BODY_CAMERA, (0.0, 0.0, 0.0)),
        "occupied_bev_cells": occupancy_cells(body_points),
        "camera_points_m": camera_points,
        "body_points_m": body_points,
        "temporal_alignment": temporal_alignment_audit(),
    }


def forward_kinematics(joints_rad: tuple[float, float], links_m: tuple[float, float] = (1.0, 0.7)) -> tuple[float, float]:
    q1, q2 = joints_rad
    l1, l2 = links_m
    return (l1 * cos(q1) + l2 * cos(q1 + q2), l1 * sin(q1) + l2 * sin(q1 + q2))


def control_audit(steps: int = 20) -> dict[str, float]:
    """Compare fixed open-loop increments with proportional observation feedback."""
    if isinstance(steps, bool) or not isinstance(steps, int) or steps <= 0:
        raise ValueError("steps must be a positive integer")
    target = (0.6, -0.4)
    actuator_bias = (0.005, -0.003)
    noise = ((0.02, -0.01), (-0.015, 0.012), (0.01, 0.0), (-0.005, -0.008))

    open_joints = [0.0, 0.0]
    fixed_action = (target[0] / steps, target[1] / steps)
    for _ in range(steps):
        open_joints[0] += fixed_action[0] + actuator_bias[0]
        open_joints[1] += fixed_action[1] + actuator_bias[1]

    feedback_joints = [0.0, 0.0]
    for step in range(steps):
        observed = (feedback_joints[0] + noise[step % len(noise)][0], feedback_joints[1] + noise[step % len(noise)][1])
        action = (0.35 * (target[0] - observed[0]), 0.35 * (target[1] - observed[1]))
        feedback_joints[0] += action[0] + actuator_bias[0]
        feedback_joints[1] += action[1] + actuator_bias[1]

    target_xy = forward_kinematics(target)
    open_xy = forward_kinematics((open_joints[0], open_joints[1]))
    feedback_xy = forward_kinematics((feedback_joints[0], feedback_joints[1]))
    return {
        "open_loop_endpoint_error_m": hypot(open_xy[0] - target_xy[0], open_xy[1] - target_xy[1]),
        "feedback_endpoint_error_m": hypot(feedback_xy[0] - target_xy[0], feedback_xy[1] - target_xy[1]),
        "open_loop_q1_error_rad": abs(open_joints[0] - target[0]),
        "feedback_q1_error_rad": abs(feedback_joints[0] - target[0]),
    }


def evaluate() -> dict[str, object]:
    return {"geometry": geometry_audit(), "control": control_audit()}
