"""Deterministic representation/probing counterexample for Chapter 10."""

from __future__ import annotations

from math import sqrt


TRAIN = tuple(
    {"task": task, "texture": 10.0 * task}
    for task in (-2.0, -1.0, 1.0, 2.0)
)
TEST = tuple(
    {"task": task, "texture": -10.0 * task}
    for task in (-2.0, -1.0, 1.0, 2.0)
)


def encode(sample: dict[str, float], representation: str) -> float:
    if representation == "appearance":
        return sample["texture"]
    if representation == "task_predictive":
        return sample["task"]
    if representation == "collapsed":
        return 0.0
    raise ValueError(f"unknown representation: {representation}")


def reconstruct(feature: float, representation: str) -> tuple[float, float]:
    """Return a deliberately restricted decoder for the two signal components."""
    if representation == "appearance":
        return (0.0, feature)
    if representation == "task_predictive":
        return (feature, 0.0)
    if representation == "collapsed":
        return (0.0, 0.0)
    raise ValueError(f"unknown representation: {representation}")


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


def probe_accuracy(representation: str) -> float:
    negative_centroid, positive_centroid = fit_centroid_probe(representation)
    correct = 0
    for sample in TEST:
        feature = encode(sample, representation)
        predicted_positive = abs(feature - positive_centroid) <= abs(feature - negative_centroid)
        target_positive = sample["task"] > 0
        correct += predicted_positive == target_positive
    return correct / len(TEST)


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


def evaluate() -> dict[str, dict[str, float]]:
    return {
        representation: {
            "reconstruction_mse": reconstruction_mse(representation),
            "shifted_probe_accuracy": probe_accuracy(representation),
            "shifted_task_rmse": task_regression_rmse(representation),
        }
        for representation in ("appearance", "task_predictive", "collapsed")
    }
