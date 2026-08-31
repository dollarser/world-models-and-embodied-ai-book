"""Zero-download geometry and feedback-control fixtures for Chapter 3."""

from __future__ import annotations

from math import cos, floor, hypot, sin


INTRINSICS = {"fx": 100.0, "fy": 100.0, "cx": 1.0, "cy": 0.5}
RGBD_SAMPLES = ((0.0, 0.0, 2.0), (1.0, 0.5, 1.0), (2.0, 1.0, 2.0))


def backproject(u: float, v: float, depth_m: float, intrinsics: dict[str, float] = INTRINSICS) -> tuple[float, float, float]:
    """Back-project one pinhole-camera pixel into the camera frame."""
    if depth_m <= 0:
        raise ValueError("depth must be positive and expressed in metres")
    x = (u - intrinsics["cx"]) * depth_m / intrinsics["fx"]
    y = (v - intrinsics["cy"]) * depth_m / intrinsics["fy"]
    return (x, y, depth_m)


def project(point: tuple[float, float, float], intrinsics: dict[str, float] = INTRINSICS) -> tuple[float, float]:
    """Project a camera-frame point back into pixel coordinates."""
    x, y, z = point
    if z <= 0:
        raise ValueError("point must lie in front of the camera")
    return (intrinsics["fx"] * x / z + intrinsics["cx"], intrinsics["fy"] * y / z + intrinsics["cy"])


def transform_yaw_translation(
    point: tuple[float, float, float], yaw_rad: float, translation_m: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Apply p_target = R_target_source p_source + t_target_source."""
    x, y, z = point
    tx, ty, tz = translation_m
    return (
        cos(yaw_rad) * x - sin(yaw_rad) * y + tx,
        sin(yaw_rad) * x + cos(yaw_rad) * y + ty,
        z + tz,
    )


def occupancy_cells(points: list[tuple[float, float, float]], cell_size_m: float = 0.25) -> list[tuple[int, int]]:
    """Rasterize horizontal x-y positions into occupied BEV cells."""
    if cell_size_m <= 0:
        raise ValueError("cell size must be positive")
    return sorted({(floor(x / cell_size_m), floor(y / cell_size_m)) for x, y, _ in points})


def geometry_audit() -> dict[str, object]:
    camera_points = [backproject(*sample) for sample in RGBD_SAMPLES]
    body_points = [transform_yaw_translation(point, 0.0, (0.5, 0.0, 0.2)) for point in camera_points]
    reprojection_errors = [
        hypot(project(point)[0] - sample[0], project(point)[1] - sample[1])
        for point, sample in zip(camera_points, RGBD_SAMPLES)
    ]
    scale_fault_points = [backproject(u, v, depth * 1000.0) for u, v, depth in RGBD_SAMPLES]
    scale_ratio = sum(point[2] for point in scale_fault_points) / sum(point[2] for point in camera_points)
    shifted = [transform_yaw_translation(point, 0.0, (0.6, 0.0, 0.2)) for point in camera_points]
    mean_extrinsic_shift = sum(abs(bad[0] - good[0]) for bad, good in zip(shifted, body_points)) / len(body_points)
    return {
        "point_count": len(camera_points),
        "max_reprojection_error_px": max(reprojection_errors),
        "depth_unit_fault_scale_ratio": scale_ratio,
        "extrinsic_fault_mean_shift_m": mean_extrinsic_shift,
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
