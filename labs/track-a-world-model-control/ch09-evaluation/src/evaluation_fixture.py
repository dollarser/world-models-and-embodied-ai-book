"""Deterministic Chapter 9 fixture for metric-ranking reversal.

This is not a learned world model. It isolates a common evaluation failure:
one predictor can have lower average one-step error while discarding the
action dependence required for planning.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable


Predictor = Callable[[float, float], float]
ACTIONS = (0.0, -0.1, 0.1)


def action_blind(state: float, action: float) -> float:
    """A smooth persistence predictor that ignores the candidate action."""

    del action
    return state


def action_faithful_biased(state: float, action: float) -> float:
    """Preserve action effects but add a visible calibration bias."""

    return state + action + 0.12


def rmse(errors: Iterable[float]) -> float:
    values = tuple(errors)
    if not values:
        raise ValueError("rmse requires at least one value")
    return math.sqrt(sum(value * value for value in values) / len(values))


def prediction_rmse(predictor: Predictor) -> float:
    """Evaluate a low-motion one-step dataset dominated by zero actions."""

    states = (-0.9, -0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 0.2, -0.2)
    actions = (-0.1, 0.0, 0.0, 0.1, 0.0, 0.0, -0.1, 0.0, 0.0, 0.1, 0.0, 0.0)
    errors = []
    for state, action in zip(states, actions, strict=True):
        truth = state + action
        errors.append(predictor(state, action) - truth)
    return rmse(errors)


def choose_action(predictor: Predictor, state: float, goal: float) -> float:
    """One-step planner; tuple order makes ties choose the safe no-op."""

    return min(ACTIONS, key=lambda action: abs(predictor(state, action) - goal))


def run_episode(predictor: Predictor, start: float, goal: float, steps: int = 24) -> dict[str, float | bool]:
    state = start
    for _ in range(steps):
        action = choose_action(predictor, state, goal)
        state += action
    distance = abs(state - goal)
    return {"final_distance": distance, "success": distance <= 0.11}


def evaluate() -> dict[str, dict[str, float]]:
    predictors = {
        "action_blind": action_blind,
        "action_faithful_biased": action_faithful_biased,
    }
    report: dict[str, dict[str, float]] = {}
    episodes = ((-1.0, 1.0), (1.0, -1.0))
    for name, predictor in predictors.items():
        outcomes = [run_episode(predictor, start, goal) for start, goal in episodes]
        report[name] = {
            "one_step_rmse": prediction_rmse(predictor),
            "closed_loop_success_rate": sum(bool(item["success"]) for item in outcomes) / len(outcomes),
            "mean_final_distance": sum(float(item["final_distance"]) for item in outcomes) / len(outcomes),
        }
    return report
