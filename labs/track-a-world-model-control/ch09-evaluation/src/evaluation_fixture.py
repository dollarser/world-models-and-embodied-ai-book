"""Deterministic Chapter 9 fixture for metric-ranking reversal.

This is not a learned world model. It isolates a common evaluation failure:
one predictor can have lower average one-step error while discarding the
action dependence required for planning.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable, Sequence


Predictor = Callable[[float, float], float]
ACTIONS = (0.0, -0.1, 0.1)


def _finite_real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite real number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return float(value)


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
    values = tuple(_finite_real(value, "error") for value in values)
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

    if not callable(predictor):
        raise ValueError("predictor must be callable")
    state = _finite_real(state, "state")
    goal = _finite_real(goal, "goal")
    scored_actions = tuple(
        (abs(_finite_real(predictor(state, action), "prediction") - goal), action)
        for action in ACTIONS
    )
    return min(scored_actions, key=lambda item: item[0])[1]


def run_episode(predictor: Predictor, start: float, goal: float, steps: int = 24) -> dict[str, float | bool]:
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    state = _finite_real(start, "start")
    goal = _finite_real(goal, "goal")
    for _ in range(steps):
        action = choose_action(predictor, state, goal)
        state += action
    distance = abs(state - goal)
    return {"final_distance": distance, "success": distance <= 0.11}


def action_sensitivity(predictor: Predictor, state: float = 0.0) -> float:
    """Measure the prediction span under interventions at one fixed state."""

    if not callable(predictor):
        raise ValueError("predictor must be callable")
    state = _finite_real(state, "state")
    predictions = tuple(_finite_real(predictor(state, action), "prediction") for action in ACTIONS)
    return max(predictions) - min(predictions)


def horizon_error_report(
    error_rows: Sequence[Sequence[float | None]],
    *,
    missing_penalty: float,
) -> list[dict[str, float | int]]:
    """Report per-horizon error without silently changing the denominator.

    `None` denotes a rollout that stopped producing valid predictions. Missing
    values must form a suffix, and the protocol must predeclare a penalty when
    a fixed-denominator score is desired.
    """

    missing_penalty = _finite_real(missing_penalty, "missing_penalty")
    if missing_penalty < 0.0:
        raise ValueError("missing_penalty must be non-negative")
    if isinstance(error_rows, (str, bytes)):
        raise ValueError("error_rows must be a non-empty rectangular sequence")
    try:
        rows = tuple(tuple(row) for row in error_rows)
    except TypeError as error:
        raise ValueError("error_rows must be a non-empty rectangular sequence") from error
    if not rows or not rows[0]:
        raise ValueError("error_rows must be a non-empty rectangular sequence")
    horizon_count = len(rows[0])
    if any(len(row) != horizon_count for row in rows):
        raise ValueError("error_rows must be rectangular")

    checked_rows: list[tuple[float | None, ...]] = []
    for row in rows:
        missing_seen = False
        checked: list[float | None] = []
        for value in row:
            if value is None:
                missing_seen = True
                checked.append(None)
                continue
            if missing_seen:
                raise ValueError("missing rollout errors must form a suffix")
            numeric = _finite_real(value, "rollout error")
            if numeric < 0.0:
                raise ValueError("rollout errors must be non-negative")
            checked.append(numeric)
        checked_rows.append(tuple(checked))

    attempted_count = len(checked_rows)
    report: list[dict[str, float | int]] = []
    for index in range(horizon_count):
        available = tuple(row[index] for row in checked_rows if row[index] is not None)
        available_count = len(available)
        if available_count == 0:
            raise ValueError("each horizon must contain at least one valid rollout")
        report.append({
            "horizon": index + 1,
            "attempted_count": attempted_count,
            "available_count": available_count,
            "coverage": available_count / attempted_count,
            "available_case_mean_error": sum(available) / available_count,
            "fixed_denominator_mean_error": (
                sum(available) + (attempted_count - available_count) * missing_penalty
            ) / attempted_count,
        })
    return report


def missing_rollout_diagnostic() -> dict[str, object]:
    """Construct a ranking reversal caused by available-case aggregation."""

    stable_rows = (
        (0.2, 0.4, 0.6, 0.8),
        (0.2, 0.4, 0.6, 0.8),
        (0.2, 0.4, 0.6, 0.8),
    )
    fragile_rows = (
        (0.1, 0.2, 0.3, 0.4),
        (0.1, 0.2, None, None),
        (0.1, None, None, None),
    )
    missing_penalty = 2.0
    stable = horizon_error_report(stable_rows, missing_penalty=missing_penalty)
    fragile = horizon_error_report(fragile_rows, missing_penalty=missing_penalty)
    return {
        "missing_penalty": missing_penalty,
        "stable": stable,
        "fragile": fragile,
        "available_case_terminal_winner": "fragile",
        "fixed_denominator_terminal_winner": "stable",
    }


def evaluate() -> dict[str, object]:
    predictors = {
        "action_blind": action_blind,
        "action_faithful_biased": action_faithful_biased,
    }
    report: dict[str, object] = {}
    episodes = ((-1.0, 1.0), (1.0, -1.0))
    for name, predictor in predictors.items():
        outcomes = [run_episode(predictor, start, goal) for start, goal in episodes]
        report[name] = {
            "one_step_rmse": prediction_rmse(predictor),
            "action_sensitivity": action_sensitivity(predictor),
            "closed_loop_success_rate": sum(bool(item["success"]) for item in outcomes) / len(outcomes),
            "mean_final_distance": sum(float(item["final_distance"]) for item in outcomes) / len(outcomes),
        }
    report["horizon_missingness"] = missing_rollout_diagnostic()
    return report
