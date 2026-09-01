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


def binary_probability_report(
    outcomes: Sequence[bool],
    probabilities: Sequence[float],
    *,
    bin_edges: Sequence[float],
) -> dict[str, object]:
    """Evaluate binary forecasts with proper losses and an explicit fixed-bin ECE."""
    if isinstance(outcomes, (str, bytes)) or isinstance(probabilities, (str, bytes)):
        raise ValueError("outcomes and probabilities must be non-empty sequences")
    if isinstance(bin_edges, (str, bytes)):
        raise ValueError("bin_edges must be a numeric sequence from zero to one")
    try:
        checked_outcomes = tuple(outcomes)
        checked_probabilities = tuple(probabilities)
        checked_edges = tuple(_finite_real(edge, "bin edge") for edge in bin_edges)
    except TypeError as error:
        raise ValueError("probability audit inputs must be sequences") from error
    if not checked_outcomes or len(checked_outcomes) != len(checked_probabilities):
        raise ValueError("outcomes and probabilities must have the same positive length")
    if any(not isinstance(outcome, bool) for outcome in checked_outcomes):
        raise ValueError("binary outcomes must be booleans")
    checked_probabilities = tuple(
        _finite_real(probability, "probability") for probability in checked_probabilities
    )
    if any(not 0.0 < probability < 1.0 for probability in checked_probabilities):
        raise ValueError("probabilities must lie strictly between zero and one")
    if (
        len(checked_edges) < 2
        or checked_edges[0] != 0.0
        or checked_edges[-1] != 1.0
        or any(left >= right for left, right in zip(checked_edges, checked_edges[1:]))
    ):
        raise ValueError("bin_edges must increase strictly from zero to one")

    sample_count = len(checked_outcomes)
    bins = []
    calibration_error = 0.0
    for index, (lower, upper) in enumerate(zip(checked_edges, checked_edges[1:])):
        upper_inclusive = index == len(checked_edges) - 2
        member_indices = tuple(
            member_index
            for member_index, probability in enumerate(checked_probabilities)
            if lower <= probability < upper or (upper_inclusive and probability == upper)
        )
        if not member_indices:
            continue
        mean_probability = sum(checked_probabilities[i] for i in member_indices) / len(member_indices)
        event_rate = sum(checked_outcomes[i] for i in member_indices) / len(member_indices)
        absolute_gap = abs(mean_probability - event_rate)
        calibration_error += len(member_indices) / sample_count * absolute_gap
        bins.append({
            "lower": lower,
            "upper": upper,
            "upper_inclusive": upper_inclusive,
            "count": len(member_indices),
            "mean_probability": mean_probability,
            "event_rate": event_rate,
            "absolute_gap": absolute_gap,
        })

    numeric_outcomes = tuple(float(outcome) for outcome in checked_outcomes)
    mean_probability = sum(checked_probabilities) / sample_count
    return {
        "sample_count": sample_count,
        "threshold_accuracy_at_0_5": sum(
            (probability >= 0.5) == outcome
            for probability, outcome in zip(checked_probabilities, checked_outcomes, strict=True)
        ) / sample_count,
        "brier_loss": sum(
            (probability - outcome) ** 2
            for probability, outcome in zip(checked_probabilities, numeric_outcomes, strict=True)
        ) / sample_count,
        "log_loss": -sum(
            outcome * math.log(probability) + (1.0 - outcome) * math.log(1.0 - probability)
            for probability, outcome in zip(checked_probabilities, numeric_outcomes, strict=True)
        ) / sample_count,
        "mean_probability": mean_probability,
        "event_rate": sum(numeric_outcomes) / sample_count,
        "probability_variance": sum(
            (probability - mean_probability) ** 2 for probability in checked_probabilities
        ) / sample_count,
        "fixed_bin_ece": calibration_error,
        "bin_edges": list(checked_edges),
        "nonempty_bins": bins,
    }


def probability_metric_diagnostic() -> dict[str, object]:
    """Expose why one coarse calibration error is not a complete forecast score."""
    outcomes = (True, True, False, False)
    forecasts = {
        "uniform_base_rate": (0.5, 0.5, 0.5, 0.5),
        "informative": (0.9, 0.9, 0.1, 0.1),
    }
    report = {}
    for name, probabilities in forecasts.items():
        one_bin = binary_probability_report(outcomes, probabilities, bin_edges=(0.0, 1.0))
        two_bins = binary_probability_report(outcomes, probabilities, bin_edges=(0.0, 0.5, 1.0))
        report[name] = {
            "threshold_accuracy_at_0_5": one_bin["threshold_accuracy_at_0_5"],
            "brier_loss": one_bin["brier_loss"],
            "log_loss": one_bin["log_loss"],
            "probability_variance": one_bin["probability_variance"],
            "one_bin_ece": one_bin["fixed_bin_ece"],
            "two_bin_ece": two_bins["fixed_bin_ece"],
        }
    return {
        **report,
        "proper_score_winner": "informative",
        "one_bin_ece_tie": True,
        "scope": (
            "four authored binary outcomes; fixed-bin ECE mechanics only, not population "
            "calibration or probabilistic world-model performance"
        ),
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
    report["probability_metric_diagnostic"] = probability_metric_diagnostic()
    return report
