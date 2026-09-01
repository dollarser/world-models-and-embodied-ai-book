"""Deterministic representation/probing counterexample for Chapter 10."""

from __future__ import annotations

from math import isfinite, sqrt


TRAIN = tuple(
    {"task": task, "texture": 10.0 * task}
    for task in (-2.0, -1.0, 1.0, 2.0)
)
TEST = tuple(
    {"task": task, "texture": -10.0 * task}
    for task in (-2.0, -1.0, 1.0, 2.0)
)
ID_TEST = tuple(
    {"task": task, "texture": 10.0 * task}
    for task in (-1.5, -0.5, 0.5, 1.5)
)
PROBE_SPLITS = {"in_distribution": ID_TEST, "shifted": TEST}
REPRESENTATIONS = ("appearance", "task_predictive", "collapsed")

TRANSITIONS = tuple(
    {"state": state, "action": action, "next_state": state + action}
    for state in (-2.0, -1.0, 1.0, 2.0)
    for action in (-1.0, 1.0)
)
ACTION_INTERFACES = ("action_blind", "action_conditioned")
TEMPORAL_INTERFACES = ("middle_frame", "ordered_delta")
TEMPORAL_CLIPS = tuple(
    {
        "frames": (center - direction, center, center + direction),
        "current_state": center,
        "direction": direction,
    }
    for center in (-2.0, -1.0, 1.0, 2.0)
    for direction in (-1.0, 1.0)
)


def _require_representation(representation: str) -> None:
    if representation not in REPRESENTATIONS:
        raise ValueError(f"unknown representation: {representation}")


def _require_sample(sample: dict[str, float]) -> None:
    if set(sample) != {"task", "texture"}:
        raise ValueError("sample must contain exactly task and texture")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in sample.values()):
        raise ValueError("sample values must be finite real numbers")


def encode(sample: dict[str, float], representation: str) -> float:
    _require_sample(sample)
    _require_representation(representation)
    if representation == "appearance":
        return sample["texture"]
    if representation == "task_predictive":
        return sample["task"]
    if representation == "collapsed":
        return 0.0
    return 0.0


def reconstruct(feature: float, representation: str) -> tuple[float, float]:
    """Return a deliberately restricted decoder for the two signal components."""
    _require_representation(representation)
    if representation == "appearance":
        return (0.0, feature)
    if representation == "task_predictive":
        return (feature, 0.0)
    if representation == "collapsed":
        return (0.0, 0.0)
    return (0.0, 0.0)


def reconstruction_mse(representation: str) -> float:
    squared_errors = []
    for sample in TEST:
        predicted_task, predicted_texture = reconstruct(encode(sample, representation), representation)
        squared_errors.extend(
            ((predicted_task - sample["task"]) ** 2, (predicted_texture - sample["texture"]) ** 2)
        )
    return sum(squared_errors) / len(squared_errors)


def fit_centroid_probe(representation: str) -> tuple[float, float]:
    negative = [encode(sample, representation) for sample in TRAIN if sample["task"] < 0]
    positive = [encode(sample, representation) for sample in TRAIN if sample["task"] > 0]
    return (sum(negative) / len(negative), sum(positive) / len(positive))


def probe_accuracy(representation: str, split: str = "shifted") -> float:
    """Fit on TRAIN and score on an explicit, held-out evaluation split."""
    if split not in PROBE_SPLITS:
        raise ValueError(f"unknown probe split: {split}")
    negative_centroid, positive_centroid = fit_centroid_probe(representation)
    correct = 0
    evaluation_samples = PROBE_SPLITS[split]
    for sample in evaluation_samples:
        feature = encode(sample, representation)
        predicted_positive = abs(feature - positive_centroid) <= abs(feature - negative_centroid)
        target_positive = sample["task"] > 0
        correct += predicted_positive == target_positive
    return correct / len(evaluation_samples)


def task_regression_rmse(representation: str) -> float:
    """Fit an affine one-dimensional probe on TRAIN, evaluate on shifted TEST."""
    features = [encode(sample, representation) for sample in TRAIN]
    targets = [sample["task"] for sample in TRAIN]
    mean_x, mean_y = sum(features) / len(features), sum(targets) / len(targets)
    denominator = sum((value - mean_x) ** 2 for value in features)
    slope = 0.0 if denominator == 0 else sum(
        (value - mean_x) * (target - mean_y) for value, target in zip(features, targets)
    ) / denominator
    intercept = mean_y - slope * mean_x
    errors = [(slope * encode(sample, representation) + intercept - sample["task"]) ** 2 for sample in TEST]
    return sqrt(sum(errors) / len(errors))


def predict_next_state(state: float, action: float, interface: str) -> float:
    """Two hand-authored predictor interfaces sharing an exact state readout."""
    if interface not in ACTION_INTERFACES:
        raise ValueError(f"unknown action interface: {interface}")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in (state, action)):
        raise ValueError("state and action must be finite real numbers")
    if interface == "action_conditioned":
        return state + action
    return state


def action_interface_metrics(interface: str) -> dict[str, float]:
    """Separate current-state readability from counterfactual transition use."""
    _ = predict_next_state(0.0, 0.0, interface)
    state_probe_errors = [(sample["state"] - sample["state"]) ** 2 for sample in TRANSITIONS]
    transition_errors = [
        (predict_next_state(sample["state"], sample["action"], interface) - sample["next_state"]) ** 2
        for sample in TRANSITIONS
    ]
    sensitivities = [
        abs(predict_next_state(state, 1.0, interface) - predict_next_state(state, -1.0, interface))
        for state in (-2.0, -1.0, 1.0, 2.0)
    ]
    return {
        "current_state_probe_rmse": sqrt(sum(state_probe_errors) / len(state_probe_errors)),
        "counterfactual_transition_rmse": sqrt(sum(transition_errors) / len(transition_errors)),
        "action_sensitivity": sum(sensitivities) / len(sensitivities),
    }


def temporal_features(frames: tuple[float, ...], interface: str) -> tuple[float, float]:
    """Expose the same middle state with or without an ordered temporal delta."""
    if interface not in TEMPORAL_INTERFACES:
        raise ValueError(f"unknown temporal interface: {interface}")
    if not isinstance(frames, tuple) or len(frames) != 3:
        raise ValueError("frames must be a three-element tuple")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
        for value in frames
    ):
        raise ValueError("frames must contain finite real numbers")
    ordered_delta = frames[-1] - frames[0] if interface == "ordered_delta" else 0.0
    return (frames[1], ordered_delta)


def temporal_interface_metrics(interface: str) -> dict[str, float]:
    """Separate current-state readability from time-direction sensitivity."""
    current_state_errors: list[float] = []
    direction_correct = 0
    reversal_changes: list[float] = []
    for sample in TEMPORAL_CLIPS:
        frames = sample["frames"]
        current_state, delta = temporal_features(frames, interface)
        current_state_errors.append((current_state - sample["current_state"]) ** 2)
        predicted_direction = 1.0 if delta >= 0.0 else -1.0
        direction_correct += predicted_direction == sample["direction"]
        reversed_delta = temporal_features(tuple(reversed(frames)), interface)[1]
        reversal_changes.append(abs(delta - reversed_delta))
    return {
        "current_state_probe_rmse": sqrt(sum(current_state_errors) / len(current_state_errors)),
        "temporal_direction_accuracy": direction_correct / len(TEMPORAL_CLIPS),
        "reversal_sensitivity": sum(reversal_changes) / len(reversal_changes),
    }


def evaluate() -> dict[str, dict[str, float] | dict[str, dict[str, float]]]:
    metrics: dict[str, dict[str, float] | dict[str, dict[str, float]]] = {
        representation: {
            "reconstruction_mse": reconstruction_mse(representation),
            "in_distribution_probe_accuracy": probe_accuracy(representation, "in_distribution"),
            "shifted_probe_accuracy": probe_accuracy(representation, "shifted"),
            "shifted_task_rmse": task_regression_rmse(representation),
        }
        for representation in REPRESENTATIONS
    }
    metrics["action_interface"] = {
        interface: action_interface_metrics(interface)
        for interface in ACTION_INTERFACES
    }
    metrics["temporal_interface"] = {
        interface: temporal_interface_metrics(interface)
        for interface in TEMPORAL_INTERFACES
    }
    return metrics
