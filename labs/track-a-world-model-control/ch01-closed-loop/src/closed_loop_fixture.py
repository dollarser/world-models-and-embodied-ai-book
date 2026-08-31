"""Offline-error versus closed-loop-outcome fixture for Chapter 1."""

from __future__ import annotations

from math import isfinite
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


def evaluate() -> dict[str, object]:
    persistent = rollout((0.1, 0.1, 0.1, 0.1, 0.1))
    alternating = rollout((0.1, -0.1, 0.1, -0.1, 0.1))
    return {
        "persistent_residual": persistent,
        "alternating_residual": alternating,
        "offline_mae_gap": round(
            persistent["offline_residual_mae"] - alternating["offline_residual_mae"], 12
        ),
        "final_state_gap": round(
            persistent["final_lateral_state"] - alternating["final_lateral_state"], 12
        ),
        "scope": "unit-gain scalar integrator with hand-authored residual actions",
    }
