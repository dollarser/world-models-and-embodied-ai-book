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


@dataclass(frozen=True)
class LoadParams:
    force_gain: float
    base_load: float

    def __post_init__(self) -> None:
        if not _is_finite_number(self.force_gain) or self.force_gain <= 0.0:
            raise ValueError("force gain must be a finite positive number")
        if not _is_finite_number(self.base_load) or self.base_load <= 0.0:
            raise ValueError("base load must be a finite positive number")


@dataclass(frozen=True)
class LoadCalibrationResult:
    selected: LoadParams
    fit_error: float
    candidate_count: int
    condition_count: int
    unique_condition_count: int
    minimizers: tuple[LoadParams, ...]

    @property
    def identifiable(self) -> bool:
        return len(self.minimizers) == 1


NOMINAL = SystemParams(actuator_gain=1.0, action_delay_steps=0, observation_scale=1.0)
TARGET = SystemParams(actuator_gain=0.8, action_delay_steps=1, observation_scale=1.25)
TARGET_LOAD = LoadParams(force_gain=1.0, base_load=1.0)
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


def rollout_load_condition(
    params: LoadParams,
    payload: float,
    actions: tuple[float, ...],
) -> tuple[float, ...]:
    """Roll out a scalar response under a known, non-negative payload."""
    if not _is_finite_number(payload) or payload < 0.0:
        raise ValueError("payload must be a finite non-negative number")
    if not actions or any(not _is_finite_number(action) for action in actions):
        raise ValueError("actions must contain finite numbers")
    effective_gain = params.force_gain / (params.base_load + payload)
    position = 0.0
    states = []
    for action in actions:
        position += effective_gain * float(action)
        states.append(position)
    return tuple(states)


def calibrate_load_conditions(
    measured_conditions: tuple[tuple[float, tuple[float, ...]], ...],
    actions: tuple[float, ...],
) -> LoadCalibrationResult:
    """Fit force and base load jointly across declared payload conditions."""
    if not measured_conditions:
        raise ValueError("at least one operating condition is required")
    for payload, measured in measured_conditions:
        if not _is_finite_number(payload) or payload < 0.0:
            raise ValueError("payload must be a finite non-negative number")
        if len(measured) != len(actions):
            raise ValueError("each measured trajectory must match the action length")
        mean_absolute_error(measured, measured)
    candidates = tuple(
        LoadParams(force_gain, base_load)
        for force_gain, base_load in product((0.5, 1.0, 1.5), repeat=2)
    )
    scored = []
    for candidate in candidates:
        error = sum(
            mean_absolute_error(
                rollout_load_condition(candidate, payload, actions),
                measured,
            )
            for payload, measured in measured_conditions
        )
        scored.append((error, candidate))
    best_error, best = min(
        scored,
        key=lambda item: (item[0], item[1].force_gain, item[1].base_load),
    )
    minimizers = tuple(
        candidate
        for error, candidate in scored
        if isclose(error, best_error, rel_tol=1e-12, abs_tol=1e-12)
    )
    return LoadCalibrationResult(
        selected=best,
        fit_error=best_error,
        candidate_count=len(candidates),
        condition_count=len(measured_conditions),
        unique_condition_count=len({payload for payload, _ in measured_conditions}),
        minimizers=minimizers,
    )


def load_params_dict(params: LoadParams) -> dict[str, float]:
    return {"force_gain": params.force_gain, "base_load": params.base_load}


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
    payload_zero = rollout_load_condition(TARGET_LOAD, 0.0, CALIBRATION_ACTIONS)
    payload_one = rollout_load_condition(TARGET_LOAD, 1.0, CALIBRATION_ACTIONS)
    single_load = calibrate_load_conditions(((0.0, payload_zero),), CALIBRATION_ACTIONS)
    repeated_load = calibrate_load_conditions(
        ((0.0, payload_zero), (0.0, payload_zero)), CALIBRATION_ACTIONS
    )
    multi_load = calibrate_load_conditions(
        ((0.0, payload_zero), (1.0, payload_one)), CALIBRATION_ACTIONS
    )
    single_load_alternative = next(
        params for params in single_load.minimizers if params != TARGET_LOAD
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
        "operating_condition_calibration": {
            "candidate_count": single_load.candidate_count,
            "single_load": {
                "condition_count": single_load.condition_count,
                "unique_condition_count": single_load.unique_condition_count,
                "minimizer_count": len(single_load.minimizers),
                "identifiable": single_load.identifiable,
                "minimizers": tuple(load_params_dict(params) for params in single_load.minimizers),
            },
            "repeated_same_load": {
                "condition_count": repeated_load.condition_count,
                "unique_condition_count": repeated_load.unique_condition_count,
                "minimizer_count": len(repeated_load.minimizers),
                "identifiable": repeated_load.identifiable,
            },
            "two_distinct_loads": {
                "condition_count": multi_load.condition_count,
                "unique_condition_count": multi_load.unique_condition_count,
                "minimizer_count": len(multi_load.minimizers),
                "identifiable": multi_load.identifiable,
                "recovered_parameters": load_params_dict(multi_load.selected),
            },
            "single_load_alternative_payload_one_mae": round(
                mean_absolute_error(
                    rollout_load_condition(
                        single_load_alternative, 1.0, CALIBRATION_ACTIONS
                    ),
                    payload_one,
                ),
                12,
            ),
        },
        "target_held_out_rollout": rollout(TARGET, HELD_OUT_ACTIONS),
    }
