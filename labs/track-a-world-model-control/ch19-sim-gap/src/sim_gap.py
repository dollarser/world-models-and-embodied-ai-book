"""Simulator calibration and gap-attribution fixture for Chapter 19."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite


def _is_finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)


@dataclass(frozen=True)
class SystemParams:
    actuator_gain: float
    action_delay_steps: int
    observation_scale: float

    def __post_init__(self) -> None:
        if not _is_finite_number(self.actuator_gain) or self.actuator_gain <= 0.0:
            raise ValueError("actuator gain must be a finite positive number")
        if isinstance(self.action_delay_steps, bool) or not isinstance(self.action_delay_steps, int):
            raise ValueError("action delay must be an integer")
        if self.action_delay_steps < 0:
            raise ValueError("action delay must be non-negative")
        if not _is_finite_number(self.observation_scale) or self.observation_scale <= 0.0:
            raise ValueError("observation scale must be a finite positive number")


NOMINAL = SystemParams(actuator_gain=1.0, action_delay_steps=0, observation_scale=1.0)
TARGET = SystemParams(actuator_gain=0.8, action_delay_steps=1, observation_scale=1.25)
CALIBRATION_ACTIONS = (1.0, 0.5, -0.5, 0.25)
HELD_OUT_ACTIONS = (0.5, 1.0, -0.25, 0.75)


def rollout(params: SystemParams, actions: tuple[float, ...]) -> dict[str, tuple[float, ...]]:
    if not actions:
        raise ValueError("at least one action is required")
    if any(not _is_finite_number(action) for action in actions):
        raise ValueError("actions must be finite numbers")

    position = 0.0
    action_queue = [0.0] * params.action_delay_steps
    states = []
    observations = []
    applied_actions = []
    for command in actions:
        if action_queue:
            applied = action_queue.pop(0)
            action_queue.append(float(command))
        else:
            applied = float(command)
        position += params.actuator_gain * applied
        states.append(position)
        observations.append(params.observation_scale * position)
        applied_actions.append(applied)
    return {
        "states": tuple(states),
        "observations": tuple(observations),
        "applied_actions": tuple(applied_actions),
    }


def mean_absolute_error(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    if len(first) != len(second) or not first:
        raise ValueError("trajectories must have the same non-zero length")
    return sum(abs(a - b) for a, b in zip(first, second)) / len(first)


def compare(candidate: SystemParams, reference: SystemParams, actions: tuple[float, ...]) -> dict[str, float]:
    candidate_rollout = rollout(candidate, actions)
    reference_rollout = rollout(reference, actions)
    return {
        "state_mae": mean_absolute_error(candidate_rollout["states"], reference_rollout["states"]),
        "observation_mae": mean_absolute_error(
            candidate_rollout["observations"], reference_rollout["observations"]
        ),
        "terminal_state_error": abs(candidate_rollout["states"][-1] - reference_rollout["states"][-1]),
    }


def calibrate(observed: tuple[float, ...], actions: tuple[float, ...]) -> tuple[SystemParams, float, int]:
    candidates = tuple(
        SystemParams(gain, delay, scale)
        for gain, delay, scale in product((0.6, 0.8, 1.0), (0, 1), (1.0, 1.25))
    )
    scored = [
        (mean_absolute_error(rollout(candidate, actions)["observations"], observed), candidate)
        for candidate in candidates
    ]
    best_error, best = min(
        scored,
        key=lambda item: (
            item[0],
            item[1].actuator_gain,
            item[1].action_delay_steps,
            item[1].observation_scale,
        ),
    )
    return best, best_error, len(candidates)


def covers(
    params: SystemParams,
    gain_range: tuple[float, float],
    delays: tuple[int, ...],
    observation_scale_range: tuple[float, float],
) -> bool:
    for name, bounds in (("gain", gain_range), ("observation scale", observation_scale_range)):
        if len(bounds) != 2 or not all(_is_finite_number(value) for value in bounds):
            raise ValueError(f"{name} range must contain two finite numbers")
        if bounds[0] > bounds[1]:
            raise ValueError(f"{name} range must be ordered")
    if not delays or any(isinstance(delay, bool) or not isinstance(delay, int) or delay < 0 for delay in delays):
        raise ValueError("delays must contain non-negative integers")
    return (
        gain_range[0] <= params.actuator_gain <= gain_range[1]
        and params.action_delay_steps in delays
        and observation_scale_range[0] <= params.observation_scale <= observation_scale_range[1]
    )


def rounded_comparison(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 12) for key, value in values.items()}


def evaluate() -> dict[str, object]:
    calibration_observations = rollout(TARGET, CALIBRATION_ACTIONS)["observations"]
    calibrated, fit_error, candidate_count = calibrate(calibration_observations, CALIBRATION_ACTIONS)
    nominal_gap = compare(NOMINAL, TARGET, HELD_OUT_ACTIONS)
    calibrated_gap = compare(calibrated, TARGET, HELD_OUT_ACTIONS)
    dynamics_only = SystemParams(
        actuator_gain=TARGET.actuator_gain,
        action_delay_steps=TARGET.action_delay_steps,
        observation_scale=NOMINAL.observation_scale,
    )
    return {
        "calibration_candidate_count": candidate_count,
        "recovered_parameters": {
            "actuator_gain": calibrated.actuator_gain,
            "action_delay_steps": calibrated.action_delay_steps,
            "observation_scale": calibrated.observation_scale,
        },
        "calibration_observation_mae": round(fit_error, 12),
        "nominal_held_out_gap": rounded_comparison(nominal_gap),
        "dynamics_calibrated_visual_uncalibrated_gap": rounded_comparison(
            compare(dynamics_only, TARGET, HELD_OUT_ACTIONS)
        ),
        "calibrated_held_out_gap": rounded_comparison(calibrated_gap),
        "narrow_randomization_covers_target": covers(TARGET, (0.9, 1.1), (0,), (0.95, 1.05)),
        "broad_randomization_covers_target": covers(TARGET, (0.7, 1.1), (0, 1), (0.9, 1.3)),
        "target_held_out_rollout": rollout(TARGET, HELD_OUT_ACTIONS),
    }
