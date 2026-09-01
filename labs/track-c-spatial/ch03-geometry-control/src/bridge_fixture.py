"""Zero-download geometry and feedback-control fixtures for Chapter 3."""

from __future__ import annotations

from math import cos, floor, hypot, isfinite, sin, sqrt


INTRINSICS = {"fx": 100.0, "fy": 100.0, "cx": 1.0, "cy": 0.5}
RGBD_SAMPLES = ((0.0, 0.0, 2.0), (1.0, 0.5, 1.0), (2.0, 1.0, 2.0))
IDENTITY_ROTATION = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
# camera optical (right, down, forward) -> body (forward, left, up)
R_BODY_CAMERA = ((0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0))
T_BODY_CAMERA_M = (0.5, 0.0, 0.2)


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
    if not isinstance(rotation, tuple) or len(rotation) != 3:
        raise ValueError("rotation must be a 3-by-3 tuple")
    rows = tuple(_finite_vector(row, "rotation row", 3) for row in rotation)
    return tuple(sum(row[index] * point[index] for index in range(3)) + translation[row_index] for row_index, row in enumerate(rows))


def inverse_transform(
    rotation: tuple[tuple[float, float, float], ...],
    translation: tuple[float, float, float],
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    """Invert a rigid transform whose rotation is assumed orthonormal."""
    _ = transform_point((0.0, 0.0, 0.0), rotation, translation)
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


def occupancy_cells(points: list[tuple[float, float, float]], cell_size_m: float = 0.25) -> list[tuple[int, int]]:
    """Rasterize horizontal x-y positions into occupied BEV cells."""
    if cell_size_m <= 0:
        raise ValueError("cell size must be positive")
    return sorted({(floor(x / cell_size_m), floor(y / cell_size_m)) for x, y, _ in points})


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
    return {
        "point_count": len(camera_points),
        "max_reprojection_error_px": max(reprojection_errors),
        "depth_unit_fault_scale_ratio": scale_ratio,
        "extrinsic_fault_mean_shift_m": mean_extrinsic_shift,
        "max_transform_roundtrip_error_m": max(transform_roundtrip_errors),
        "identity_axis_mapping_mean_error_m": identity_axis_error,
        "off_axis_z_depth_to_range_ratio": sqrt(sum(value * value for value in off_axis_z_depth)),
        "optical_forward_axis_in_body": transform_point((0.0, 0.0, 1.0), R_BODY_CAMERA, (0.0, 0.0, 0.0)),
        "occupied_bev_cells": occupancy_cells(body_points),
        "camera_points_m": camera_points,
        "body_points_m": body_points,
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
