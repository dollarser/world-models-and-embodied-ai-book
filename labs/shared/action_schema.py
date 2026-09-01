"""Shared executable action-schema definitions used by Chapters 15 and 21."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionField:
    name: str
    unit: str
    minimum: float
    maximum: float
    maximum_delta_per_step: float


@dataclass(frozen=True)
class ActionSchema:
    schema_id: str
    frame_id: str
    fields: tuple[ActionField, ...]
    control_hz: float
    prediction_horizon: int
    execution_horizon: int
    max_age_ms: int
    clock_id: str


MOBILE_BASE_SCHEMA = ActionSchema(
    schema_id="mobile-base-v1",
    frame_id="base_link",
    fields=(
        ActionField("linear_velocity", "m/s", -0.5, 0.5, 0.25),
        ActionField("yaw_rate", "rad/s", -1.0, 1.0, 0.25),
    ),
    control_hz=10.0,
    prediction_horizon=3,
    execution_horizon=1,
    max_age_ms=100,
    clock_id="control_monotonic_ms",
)
