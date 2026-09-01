"""Deterministic action-conditioned rollout fixture for Chapter 11."""

from __future__ import annotations

from itertools import combinations
from math import hypot, isfinite, sqrt


ACTIONS = ("forward", "left", "right", "brake")
TRUE_DELTAS = {
    "forward": (1.0, 0.0),
    "left": (1.0, -1.0),
    "right": (1.0, 1.0),
    "brake": (0.0, 0.0),
}
GRID_MAX = 6.0
MODELS = ("action_blind", "left_right_swapped", "action_conditioned")


def _finite_state(state: tuple[float, float]) -> tuple[float, float]:
    if not isinstance(state, tuple) or len(state) != 2:
        raise ValueError("state must be a two-element tuple")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        for value in state
    ):
        raise ValueError("state values must be finite real numbers")
    return (float(state[0]), float(state[1]))


def transition(state: tuple[float, float], action: str) -> tuple[float, float]:
    state = _finite_state(state)
    if action not in TRUE_DELTAS:
        raise ValueError(f"unknown action: {action}")
    dx, dy = TRUE_DELTAS[action]
    return (min(GRID_MAX, max(0.0, state[0] + dx)), min(GRID_MAX, max(0.0, state[1] + dy)))


def render_state(state: tuple[float, float], size: int = 7) -> str:
    """Render a discrete observation after rounding the state to the fixture grid."""
    state = _finite_state(state)
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    x, y = round(state[0]), round(state[1])
    if not (0 <= x < size and 0 <= y < size):
        raise ValueError("rounded state must lie inside the render grid")
    rows = []
    for row in reversed(range(size)):
        rows.append("".join("A" if (column, row) == (x, y) else "." for column in range(size)))
    return "\n".join(rows)


def training_transitions() -> list[tuple[tuple[float, float], str, tuple[float, float]]]:
    """Cover every individual action while withholding test action sequences."""
    starts = ((1.0, 2.0), (2.0, 3.0), (3.0, 2.0))
    return [(state, action, transition(state, action)) for state in starts for action in ACTIONS]


def fit_action_deltas() -> dict[str, tuple[float, float]]:
    grouped: dict[str, list[tuple[float, float]]] = {action: [] for action in ACTIONS}
    for state, action, next_state in training_transitions():
        grouped[action].append((next_state[0] - state[0], next_state[1] - state[1]))
    return {
        action: (
            sum(delta[0] for delta in deltas) / len(deltas),
            sum(delta[1] for delta in deltas) / len(deltas),
        )
        for action, deltas in grouped.items()
    }


def fit_action_blind_delta() -> tuple[float, float]:
    deltas = [
        (next_state[0] - state[0], next_state[1] - state[1])
        for state, _, next_state in training_transitions()
    ]
    return (
        sum(delta[0] for delta in deltas) / len(deltas),
        sum(delta[1] for delta in deltas) / len(deltas),
    )


def predict_next(state: tuple[float, float], action: str, model: str) -> tuple[float, float]:
    state = _finite_state(state)
    if action not in ACTIONS:
        raise ValueError(f"unknown action: {action}")
    if model == "action_conditioned":
        delta = fit_action_deltas()[action]
    elif model == "left_right_swapped":
        swapped_action = {"left": "right", "right": "left"}.get(action, action)
        delta = fit_action_deltas()[swapped_action]
    elif model == "action_blind":
        delta = fit_action_blind_delta()
    else:
        raise ValueError(f"unknown model: {model}")
    return (min(GRID_MAX, max(0.0, state[0] + delta[0])), min(GRID_MAX, max(0.0, state[1] + delta[1])))


def rollout(start: tuple[float, float], actions: tuple[str, ...], model: str | None = None) -> list[tuple[float, float]]:
    start = _finite_state(start)
    if isinstance(actions, (str, bytes)) or not isinstance(actions, tuple) or not actions:
        raise ValueError("actions must be a non-empty tuple")
    if model is not None and model not in MODELS:
        raise ValueError(f"unknown model: {model}")
    states = [start]
    for action in actions:
        states.append(transition(states[-1], action) if model is None else predict_next(states[-1], action, model))
    return states


def evaluate_model(model: str) -> dict[str, float | int]:
    one_step_squared = []
    frame_matches = 0
    counterfactual_start = (2.0, 3.0)
    expected_counterfactuals = []
    predicted_counterfactuals = []
    for action in ACTIONS:
        expected = transition(counterfactual_start, action)
        predicted = predict_next(counterfactual_start, action, model)
        one_step_squared.extend(((predicted[0] - expected[0]) ** 2, (predicted[1] - expected[1]) ** 2))
        frame_matches += render_state(predicted) == render_state(expected)
        expected_counterfactuals.append(expected)
        predicted_counterfactuals.append(predicted)

    pairwise_vector_squared = []
    for first, second in combinations(range(len(ACTIONS)), 2):
        expected_delta = (
            expected_counterfactuals[second][0] - expected_counterfactuals[first][0],
            expected_counterfactuals[second][1] - expected_counterfactuals[first][1],
        )
        predicted_delta = (
            predicted_counterfactuals[second][0] - predicted_counterfactuals[first][0],
            predicted_counterfactuals[second][1] - predicted_counterfactuals[first][1],
        )
        pairwise_vector_squared.extend(
            (
                (predicted_delta[0] - expected_delta[0]) ** 2,
                (predicted_delta[1] - expected_delta[1]) ** 2,
            )
        )

    sequences = (
        ("forward", "forward", "right"),
        ("left", "forward", "right"),
        ("brake", "right", "right"),
    )
    endpoint_errors = []
    trajectory_squared = []
    transition_count = 0
    for actions in sequences:
        expected_rollout = rollout((1.0, 3.0), actions)
        predicted_rollout = rollout((1.0, 3.0), actions, model)
        expected_endpoint = expected_rollout[-1]
        predicted_endpoint = predicted_rollout[-1]
        endpoint_errors.append(
            hypot(
                predicted_endpoint[0] - expected_endpoint[0],
                predicted_endpoint[1] - expected_endpoint[1],
            )
        )
        for expected, predicted in zip(expected_rollout[1:], predicted_rollout[1:], strict=True):
            trajectory_squared.extend(((predicted[0] - expected[0]) ** 2, (predicted[1] - expected[1]) ** 2))
            transition_count += 1

    left = predict_next(counterfactual_start, "left", model)
    right = predict_next(counterfactual_start, "right", model)
    pairwise_distances = [
        hypot(
            predicted_counterfactuals[second][0] - predicted_counterfactuals[first][0],
            predicted_counterfactuals[second][1] - predicted_counterfactuals[first][1],
        )
        for first, second in combinations(range(len(ACTIONS)), 2)
    ]
    return {
        "one_step_state_rmse": sqrt(sum(one_step_squared) / len(one_step_squared)),
        "one_step_frame_accuracy": frame_matches / len(ACTIONS),
        "action_sensitivity": max(pairwise_distances),
        "left_right_separation": hypot(left[0] - right[0], left[1] - right[1]),
        "left_to_right_signed_separation": right[1] - left[1],
        "counterfactual_vector_rmse": sqrt(sum(pairwise_vector_squared) / len(pairwise_vector_squared)),
        "unseen_sequence_count": len(sequences),
        "unseen_transition_count": transition_count,
        "unseen_sequence_trajectory_rmse": sqrt(sum(trajectory_squared) / len(trajectory_squared)),
        "mean_unseen_sequence_endpoint_error": sum(endpoint_errors) / len(endpoint_errors),
    }


def evaluate() -> dict[str, dict[str, float | int]]:
    return {model: evaluate_model(model) for model in MODELS}
