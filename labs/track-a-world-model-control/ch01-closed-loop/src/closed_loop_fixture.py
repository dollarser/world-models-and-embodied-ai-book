"""Offline-error versus closed-loop-outcome fixture for Chapter 1."""

from __future__ import annotations

from math import isclose, isfinite
from typing import Sequence


def rollout(residual_actions: Sequence[float], safety_bound: float = 0.3) -> dict[str, object]:
    if isinstance(residual_actions, (str, bytes)) or not isinstance(residual_actions, Sequence) or not residual_actions:
        raise ValueError("residual_actions must be a non-empty numeric sequence")
    if isinstance(safety_bound, bool) or not isinstance(safety_bound, (int, float)) or not isfinite(safety_bound) or safety_bound <= 0:
        raise ValueError("safety_bound must be a finite positive number")
    values = []
    for value in residual_actions:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError("residual_actions must contain finite numbers")
        values.append(float(value))

    lateral_state = 0.0
    state_trace = []
    first_violation_step = None
    for step, residual in enumerate(values, start=1):
        lateral_state += residual
        state_trace.append(round(lateral_state, 12))
        if first_violation_step is None and abs(lateral_state) > safety_bound + 1e-12:
            first_violation_step = step
    offline_mae = sum(abs(value) for value in values) / len(values)
    return {
        "step_count": len(values),
        "offline_residual_mae": round(offline_mae, 12),
        "final_lateral_state": round(lateral_state, 12),
        "maximum_abs_lateral_state": round(max(abs(value) for value in state_trace), 12),
        "safety_bound": float(safety_bound),
        "bound_violated": first_violation_step is not None,
        "first_violation_step": first_violation_step,
        "state_trace": tuple(state_trace),
    }


def feedback_rollout(
    disturbances: Sequence[float],
    *,
    controller_gain: float,
    observation_delay_steps: int = 0,
    action_limit: float = 0.25,
    safety_bound: float = 0.3,
) -> dict[str, object]:
    """Roll out a delayed, saturated proportional controller on a scalar integrator.

    The state update is ``x[t+1] = x[t] + u[t] + d[t]``. The controller sees
    a delayed pre-action state and applies ``clip(-gain * observed_state)``.
    This is a teaching contract, not a controller for any physical platform.
    """

    if isinstance(disturbances, (str, bytes)) or not isinstance(disturbances, Sequence) or not disturbances:
        raise ValueError("disturbances must be a non-empty numeric sequence")
    if (
        isinstance(controller_gain, bool)
        or not isinstance(controller_gain, (int, float))
        or not isfinite(controller_gain)
        or controller_gain < 0
    ):
        raise ValueError("controller_gain must be a finite non-negative number")
    if isinstance(observation_delay_steps, bool) or not isinstance(observation_delay_steps, int):
        raise ValueError("observation_delay_steps must be an integer")
    if observation_delay_steps < 0:
        raise ValueError("observation_delay_steps must be non-negative")
    for name, value in (("action_limit", action_limit), ("safety_bound", safety_bound)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite positive number")

    disturbance_values: list[float] = []
    for value in disturbances:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError("disturbances must contain finite numbers")
        disturbance_values.append(float(value))

    state = 0.0
    state_history = [state]
    observed_state_trace: list[float] = []
    raw_action_trace: list[float] = []
    action_trace: list[float] = []
    saturation_count = 0
    first_violation_step = None

    for step, disturbance in enumerate(disturbance_values, start=1):
        current_index = len(state_history) - 1
        observed_index = max(0, current_index - observation_delay_steps)
        observed_state = state_history[observed_index]
        raw_action = -float(controller_gain) * observed_state
        action = max(-float(action_limit), min(float(action_limit), raw_action))
        if not isclose(action, raw_action, rel_tol=0.0, abs_tol=1e-12):
            saturation_count += 1
        state = state + action + disturbance
        state_history.append(state)
        observed_state_trace.append(round(observed_state, 12))
        raw_action_trace.append(round(raw_action, 12))
        action_trace.append(round(action, 12))
        if first_violation_step is None and abs(state) > safety_bound + 1e-12:
            first_violation_step = step

    state_trace = tuple(round(value, 12) for value in state_history[1:])
    return {
        "step_count": len(disturbance_values),
        "controller_gain": float(controller_gain),
        "observation_delay_steps": observation_delay_steps,
        "action_limit": float(action_limit),
        "disturbance_mean_abs": round(
            sum(abs(value) for value in disturbance_values) / len(disturbance_values), 12
        ),
        "final_state": round(state, 12),
        "maximum_abs_state": round(max(abs(value) for value in state_trace), 12),
        "safety_bound": float(safety_bound),
        "bound_violated": first_violation_step is not None,
        "first_violation_step": first_violation_step,
        "saturation_count": saturation_count,
        "observed_state_trace": tuple(observed_state_trace),
        "raw_action_trace": tuple(raw_action_trace),
        "action_trace": tuple(action_trace),
        "state_trace": state_trace,
    }


def evaluate() -> dict[str, object]:
    persistent = rollout((0.1, 0.1, 0.1, 0.1, 0.1))
    alternating = rollout((0.1, -0.1, 0.1, -0.1, 0.1))
    disturbances = (0.1,) * 12
    return {
        "persistent_residual": persistent,
        "alternating_residual": alternating,
        "offline_mae_gap": round(
            persistent["offline_residual_mae"] - alternating["offline_residual_mae"], 12
        ),
        "final_state_gap": round(
            persistent["final_lateral_state"] - alternating["final_lateral_state"], 12
        ),
        "feedback_comparison": {
            "open_loop": feedback_rollout(disturbances, controller_gain=0.0),
            "timely_feedback": feedback_rollout(disturbances, controller_gain=0.8),
            "delayed_feedback": feedback_rollout(
                disturbances, controller_gain=0.8, observation_delay_steps=2
            ),
            "authority_limited_feedback": feedback_rollout(
                disturbances, controller_gain=0.8, action_limit=0.05
            ),
        },
        "scope": "unit-gain scalar integrator with hand-authored residual actions and proportional feedback",
    }
