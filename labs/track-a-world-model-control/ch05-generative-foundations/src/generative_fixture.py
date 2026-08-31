"""Distributional prediction and probability-path fixtures for Chapter 5."""

from __future__ import annotations

from collections import Counter
from math import isfinite, log, sqrt


DATA = (
    ("fork", -1.0),
    ("fork", -1.0),
    ("fork", 1.0),
    ("fork", 1.0),
    ("left_only", -1.0),
    ("left_only", -1.0),
    ("left_only", -1.0),
    ("left_only", -1.0),
)


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)


def empirical_distribution(values: tuple[float, ...]) -> dict[float, float]:
    if not values:
        raise ValueError("at least one value is required")
    if any(not _finite_number(value) for value in values):
        raise ValueError("values must be finite numbers")
    counts = Counter(float(value) for value in values)
    return {value: count / len(values) for value, count in sorted(counts.items())}


def conditional_distribution(context: str) -> dict[float, float]:
    values = tuple(value for sample_context, value in DATA if sample_context == context)
    if not values:
        raise ValueError(f"unknown context: {context}")
    return empirical_distribution(values)


def point_mean(context: str) -> float:
    distribution = conditional_distribution(context)
    return sum(value * probability for value, probability in distribution.items())


def expected_squared_error(prediction: float, context: str) -> float:
    distribution = conditional_distribution(context)
    return sum(probability * (prediction - value) ** 2 for value, probability in distribution.items())


def negative_log_likelihood(distribution: dict[float, float], values: tuple[float, ...]) -> float:
    if not values:
        raise ValueError("at least one target is required")
    if any(not _finite_number(probability) or probability < 0.0 for probability in distribution.values()):
        raise ValueError("distribution probabilities must be finite and non-negative")
    probabilities = []
    for value in values:
        probability = distribution.get(float(value), 0.0)
        if probability <= 0.0:
            raise ValueError("distribution assigns zero probability to an observed value")
        probabilities.append(probability)
    return -sum(log(probability) for probability in probabilities) / len(probabilities)


def quantile_samples(distribution: dict[float, float], quantiles: tuple[float, ...]) -> tuple[float, ...]:
    if (
        not distribution
        or any(not _finite_number(probability) or probability < 0.0 for probability in distribution.values())
        or abs(sum(distribution.values()) - 1.0) > 1e-12
    ):
        raise ValueError("distribution must be normalized")
    if any(not 0.0 <= quantile < 1.0 for quantile in quantiles):
        raise ValueError("quantiles must lie in [0, 1)")
    items = sorted(distribution.items())
    samples = []
    for quantile in quantiles:
        cumulative = 0.0
        for value, probability in items:
            cumulative += probability
            if quantile < cumulative:
                samples.append(value)
                break
    return tuple(samples)


def diffusion_forward(data: float, noise: float, alpha_bar: float) -> float:
    if not _finite_number(data) or not _finite_number(noise):
        raise ValueError("data and noise must be finite numbers")
    if not _finite_number(alpha_bar) or not 0.0 <= alpha_bar <= 1.0:
        raise ValueError("alpha_bar must lie in [0, 1]")
    return sqrt(alpha_bar) * data + sqrt(1.0 - alpha_bar) * noise


def flow_path(noise: float, data: float, time: float) -> tuple[float, float]:
    if not _finite_number(data) or not _finite_number(noise):
        raise ValueError("data and noise must be finite numbers")
    if not _finite_number(time) or not 0.0 <= time <= 1.0:
        raise ValueError("time must lie in [0, 1]")
    return ((1.0 - time) * noise + time * data, data - noise)


def evaluate() -> dict[str, object]:
    fork = conditional_distribution("fork")
    fork_targets = tuple(value for context, value in DATA if context == "fork")
    unconditional = empirical_distribution(tuple(value for _, value in DATA))
    conditional_nll = sum(
        -log(conditional_distribution(context)[value]) for context, value in DATA
    ) / len(DATA)
    mean = point_mean("fork")
    samples = quantile_samples(fork, (0.125, 0.375, 0.625, 0.875))
    return {
        "fork_distribution": {str(key): value for key, value in fork.items()},
        "point_mean": mean,
        "point_mean_expected_mse": expected_squared_error(mean, "fork"),
        "point_mean_distance_to_nearest_supported_future": min(abs(mean - value) for value in fork),
        "fork_categorical_nll": round(negative_log_likelihood(fork, fork_targets), 12),
        "fork_quantile_samples": samples,
        "fork_sample_support_coverage": len(set(samples) & set(fork)) / len(fork),
        "conditional_dataset_nll": round(conditional_nll, 12),
        "unconditional_dataset_nll": round(
            negative_log_likelihood(unconditional, tuple(value for _, value in DATA)), 12
        ),
        "diffusion_endpoints": {
            "clean": diffusion_forward(1.0, -2.0, 1.0),
            "noise": diffusion_forward(1.0, -2.0, 0.0),
        },
        "flow_endpoints_and_velocity": {
            "start": flow_path(-2.0, 1.0, 0.0),
            "end": flow_path(-2.0, 1.0, 1.0),
        },
    }
