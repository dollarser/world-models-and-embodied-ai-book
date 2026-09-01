"""Deterministic fixtures for imitation-learning evaluation contracts."""

from __future__ import annotations

from math import exp, isfinite, sqrt
from typing import Sequence


def compounding_error(horizon: int = 20, action_bias: float = 0.02) -> dict[str, float]:
    """Compare teacher-forced action error with its integrated rollout effect."""
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("horizon must be positive")
    if isinstance(action_bias, bool) or not isinstance(action_bias, (int, float)) or not isfinite(action_bias):
        raise ValueError("action_bias must be a finite number")
    errors = [action_bias] * horizon
    state = sum(errors)
    return {
        "horizon": horizon,
        "open_loop_action_rmse": sqrt(sum(error * error for error in errors) / horizon),
        "closed_loop_final_state_error": abs(state),
        "amplification_factor": abs(state) / abs(action_bias) if action_bias else 0.0,
    }


def chunk_tradeoff(
    horizon: int = 16,
    prediction_horizon: int = 8,
    execution_horizons: Sequence[int] = (1, 4, 8),
    deadline_steps: int = 2,
) -> list[dict[str, float]]:
    """Hold prediction length fixed and vary how much of each chunk is executed."""
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 1:
        raise ValueError("horizon must exceed one step")
    if isinstance(prediction_horizon, bool) or not isinstance(prediction_horizon, int) or prediction_horizon <= 0:
        raise ValueError("prediction_horizon must be a positive integer")
    if isinstance(deadline_steps, bool) or not isinstance(deadline_steps, int) or deadline_steps < 0:
        raise ValueError("deadline_steps must be a non-negative integer")
    if (
        isinstance(execution_horizons, (str, bytes))
        or not isinstance(execution_horizons, Sequence)
        or not execution_horizons
    ):
        raise ValueError("execution_horizons must be a non-empty sequence")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > prediction_horizon
        for value in execution_horizons
    ):
        raise ValueError("execution horizons must be positive integers no greater than prediction_horizon")
    if len(set(execution_horizons)) != len(execution_horizons):
        raise ValueError("execution_horizons must be unique")

    rows = []
    perturbation_steps = range(1, horizon)
    for execution_horizon in execution_horizons:
        delays = [
            (execution_horizon - (step % execution_horizon)) % execution_horizon
            for step in perturbation_steps
        ]
        rows.append(
            {
                "prediction_horizon_steps": prediction_horizon,
                "execution_horizon_steps": execution_horizon,
                "discarded_prediction_steps_per_full_query": prediction_horizon - execution_horizon,
                "policy_queries": (horizon + execution_horizon - 1) // execution_horizon,
                "mean_reaction_delay_steps": sum(delays) / len(delays),
                "max_reaction_delay_steps": max(delays),
                "deadline_steps": deadline_steps,
                "deadline_pass_rate": sum(delay <= deadline_steps for delay in delays) / len(delays),
            }
        )
    return rows


def temporal_ensemble(predictions_oldest_to_newest: Sequence[float], coefficient: float = 0.01) -> float:
    """Exponentially aggregate overlapping predictions for the same action step.

    This mirrors the ACT/LeRobot convention where index zero is the oldest
    prediction and therefore receives the largest weight for positive values.
    """
    if (
        isinstance(predictions_oldest_to_newest, (str, bytes))
        or not isinstance(predictions_oldest_to_newest, Sequence)
        or not predictions_oldest_to_newest
    ):
        raise ValueError("predictions must be a non-empty numeric sequence")
    predictions = []
    for value in predictions_oldest_to_newest:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError("predictions must contain only finite numbers")
        predictions.append(float(value))
    if isinstance(coefficient, bool) or not isinstance(coefficient, (int, float)) or not isfinite(coefficient):
        raise ValueError("coefficient must be a finite number")
    if coefficient < 0.0:
        raise ValueError("coefficient must be non-negative")
    weights = [exp(-float(coefficient) * index) for index in range(len(predictions))]
    return sum(value * weight for value, weight in zip(predictions, weights)) / sum(weights)


def evaluate() -> dict[str, object]:
    stationary_predictions = (0.8, 1.2, 0.8, 1.2)
    changed_predictions = (0.0, 0.0, 0.0, 1.0)
    stationary_ensemble = temporal_ensemble(stationary_predictions)
    changed_ensemble = temporal_ensemble(changed_predictions)
    return {
        "compounding_error": compounding_error(),
        "chunk_tradeoff": chunk_tradeoff(),
        "temporal_ensemble": {
            "coefficient": 0.01,
            "stationary_target": 1.0,
            "stationary_latest_action": stationary_predictions[-1],
            "stationary_ensembled_action": round(stationary_ensemble, 12),
            "stationary_latest_absolute_error": round(abs(stationary_predictions[-1] - 1.0), 12),
            "stationary_ensemble_absolute_error": round(abs(stationary_ensemble - 1.0), 12),
            "changed_target": 1.0,
            "changed_latest_action": changed_predictions[-1],
            "changed_ensembled_action": round(changed_ensemble, 12),
            "changed_latest_absolute_error": round(abs(changed_predictions[-1] - 1.0), 12),
            "changed_ensemble_absolute_error": round(abs(changed_ensemble - 1.0), 12),
        },
    }
