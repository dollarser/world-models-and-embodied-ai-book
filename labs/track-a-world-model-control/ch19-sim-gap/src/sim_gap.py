"""Simulator calibration and gap-attribution fixture for Chapter 19."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isclose, isfinite


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


@dataclass(frozen=True)
class CalibrationResult:
    selected: SystemParams
    fit_error: float
    candidate_count: int
    minimizers: tuple[SystemParams, ...]

    @property
    def identifiable(self) -> bool:
        return len(self.minimizers) == 1


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
    if any(not _is_finite_number(value) for value in (*first, *second)):
        raise ValueError("trajectories must contain finite numbers")
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


def calibrate(
    observed: tuple[float, ...],
    actions: tuple[float, ...],
    observed_states: tuple[float, ...] | None = None,
) -> CalibrationResult:
    if len(observed) != len(actions) or not observed:
        raise ValueError("observations and actions must have the same non-zero length")
    mean_absolute_error(observed, observed)
    if observed_states is not None:
        if len(observed_states) != len(actions):
            raise ValueError("state anchors and actions must have the same length")
        mean_absolute_error(observed_states, observed_states)
    candidates = tuple(
        SystemParams(gain, delay, scale)
        for gain, delay, scale in product((0.6, 0.8, 1.0), (0, 1), (1.0, 1.25))
    )
    scored = []
    for candidate in candidates:
        candidate_rollout = rollout(candidate, actions)
        error = mean_absolute_error(candidate_rollout["observations"], observed)
        if observed_states is not None:
            error += mean_absolute_error(candidate_rollout["states"], observed_states)
        scored.append((error, candidate))
    best_error, best = min(
        scored,
        key=lambda item: (
            item[0],
            item[1].actuator_gain,
            item[1].action_delay_steps,
            item[1].observation_scale,
        ),
    )
    minimizers = tuple(
        candidate
        for error, candidate in scored
        if isclose(error, best_error, rel_tol=1e-12, abs_tol=1e-12)
    )
    return CalibrationResult(best, best_error, len(candidates), minimizers)


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


def params_dict(params: SystemParams) -> dict[str, float | int]:
    return {
        "actuator_gain": params.actuator_gain,
        "action_delay_steps": params.action_delay_steps,
        "observation_scale": params.observation_scale,
    }


def evaluate() -> dict[str, object]:
    calibration_rollout = rollout(TARGET, CALIBRATION_ACTIONS)
    observation_only = calibrate(calibration_rollout["observations"], CALIBRATION_ACTIONS)
    state_anchored = calibrate(
        calibration_rollout["observations"],
        CALIBRATION_ACTIONS,
        observed_states=calibration_rollout["states"],
    )
    alternative = next(params for params in observation_only.minimizers if params != TARGET)
    nominal_gap = compare(NOMINAL, TARGET, HELD_OUT_ACTIONS)
    calibrated_gap = compare(state_anchored.selected, TARGET, HELD_OUT_ACTIONS)
    dynamics_only = SystemParams(
        actuator_gain=TARGET.actuator_gain,
        action_delay_steps=TARGET.action_delay_steps,
        observation_scale=NOMINAL.observation_scale,
    )
    return {
        "calibration_candidate_count": observation_only.candidate_count,
        "observation_only_calibration": {
            "fit_error": round(observation_only.fit_error, 12),
            "identifiable": observation_only.identifiable,
            "minimizer_count": len(observation_only.minimizers),
            "minimizers": tuple(params_dict(params) for params in observation_only.minimizers),
        },
        "observation_only_alternative": {
            "parameters": params_dict(alternative),
            "held_out_gap": rounded_comparison(compare(alternative, TARGET, HELD_OUT_ACTIONS)),
        },
        "state_observation_calibration": {
            "fit_error": round(state_anchored.fit_error, 12),
            "identifiable": state_anchored.identifiable,
            "minimizer_count": len(state_anchored.minimizers),
            "recovered_parameters": params_dict(state_anchored.selected),
        },
        "nominal_held_out_gap": rounded_comparison(nominal_gap),
        "dynamics_calibrated_visual_uncalibrated_gap": rounded_comparison(
            compare(dynamics_only, TARGET, HELD_OUT_ACTIONS)
        ),
        "calibrated_held_out_gap": rounded_comparison(calibrated_gap),
        "narrow_randomization_covers_target": covers(TARGET, (0.9, 1.1), (0,), (0.95, 1.05)),
        "broad_randomization_covers_target": covers(TARGET, (0.7, 1.1), (0, 1), (0.9, 1.3)),
        "target_held_out_rollout": rollout(TARGET, HELD_OUT_ACTIONS),
    }
