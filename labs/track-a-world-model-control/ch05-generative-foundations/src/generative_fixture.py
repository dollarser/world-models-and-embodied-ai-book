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


def _normalized_distribution(distribution: object) -> bool:
    return (
        isinstance(distribution, dict)
        and bool(distribution)
        and all(_finite_number(value) for value in distribution)
        and all(_finite_number(probability) and probability >= 0.0 for probability in distribution.values())
        and abs(sum(distribution.values()) - 1.0) <= 1e-12
    )


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
    if not _normalized_distribution(distribution):
        raise ValueError("distribution must have finite numeric support and normalized probabilities")
    if any(not _finite_number(value) for value in values):
        raise ValueError("targets must be finite numbers")
    probabilities = []
    for value in values:
        probability = distribution.get(float(value), 0.0)
        if probability <= 0.0:
            raise ValueError("distribution assigns zero probability to an observed value")
        probabilities.append(probability)
    return -sum(log(probability) for probability in probabilities) / len(probabilities)


def total_variation_distance(
    first: dict[float, float], second: dict[float, float]
) -> float:
    """Measure how strongly two discrete predictive distributions differ."""
    if not _normalized_distribution(first) or not _normalized_distribution(second):
        raise ValueError("both distributions must be finite and normalized")
    support = set(first) | set(second)
    return 0.5 * sum(abs(first.get(value, 0.0) - second.get(value, 0.0)) for value in support)


def support_diagnostics(
    distribution: dict[float, float],
    observed_values: tuple[float, ...],
    probability_threshold: float = 0.01,
) -> dict[str, float]:
    """Separate observed-mode coverage from probability assigned outside data support."""
    if not _normalized_distribution(distribution):
        raise ValueError("distribution must have finite numeric support and normalized probabilities")
    if not observed_values or any(not _finite_number(value) for value in observed_values):
        raise ValueError("observed values must be non-empty finite numbers")
    if not _finite_number(probability_threshold) or not 0.0 < probability_threshold <= 1.0:
        raise ValueError("probability_threshold must lie in (0, 1]")

    observed_support = {float(value) for value in observed_values}
    covered_modes = sum(distribution.get(value, 0.0) >= probability_threshold for value in observed_support)
    invalid_probability_mass = sum(
        probability for value, probability in distribution.items() if value not in observed_support
    )
    return {
        "observed_mode_recall": covered_modes / len(observed_support),
        "out_of_support_probability_mass": invalid_probability_mass,
    }


def quantile_samples(distribution: dict[float, float], quantiles: tuple[float, ...]) -> tuple[float, ...]:
    if not _normalized_distribution(distribution):
        raise ValueError("distribution must have finite numeric support and normalized probabilities")
    if any(not _finite_number(quantile) or not 0.0 <= quantile < 1.0 for quantile in quantiles):
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


def ensemble_disagreement_diagnostic(
    predictions: tuple[float, ...],
    target: float,
    disagreement_threshold: float,
) -> dict[str, float | int | bool]:
    """Audit a range-based ensemble gate; this is not a calibrated uncertainty model."""

    if (
        not isinstance(predictions, tuple)
        or len(predictions) < 2
        or any(not _finite_number(value) for value in predictions)
    ):
        raise ValueError("predictions must contain at least two finite numbers")
    if not _finite_number(target):
        raise ValueError("target must be a finite number")
    if not _finite_number(disagreement_threshold) or disagreement_threshold < 0.0:
        raise ValueError("disagreement_threshold must be a finite non-negative number")

    mean_prediction = sum(predictions) / len(predictions)
    prediction_range = max(predictions) - min(predictions)
    return {
        "member_count": len(predictions),
        "mean_prediction": round(mean_prediction, 12),
        "ensemble_mean_absolute_error": round(abs(mean_prediction - target), 12),
        "prediction_range": round(prediction_range, 12),
        "deferred_by_range": prediction_range > disagreement_threshold,
    }


def ensemble_disagreement_audit() -> dict[str, object]:
    """Compare useful disagreement with a correlated-error false negative."""

    threshold = 0.25
    return {
        "disagreement_threshold": threshold,
        "in_distribution": ensemble_disagreement_diagnostic(
            (-0.1, 0.0, 0.1), target=0.0, disagreement_threshold=threshold
        ),
        "diverse_ood": ensemble_disagreement_diagnostic(
            (1.0, 2.0, 3.0), target=-2.0, disagreement_threshold=threshold
        ),
        "shared_error_ood": ensemble_disagreement_diagnostic(
            (2.0, 2.0, 2.0), target=-2.0, disagreement_threshold=threshold
        ),
        "scope": (
            "three hand-authored scalar members and a fixed range threshold; "
            "not learned epistemic uncertainty, OOD detection, calibration, or safety evidence"
        ),
    }


def evaluate() -> dict[str, object]:
    fork = conditional_distribution("fork")
    fork_targets = tuple(value for context, value in DATA if context == "fork")
    unconditional = empirical_distribution(tuple(value for _, value in DATA))
    conditional_nll = sum(
        -log(conditional_distribution(context)[value]) for context, value in DATA
    ) / len(DATA)
    mean = point_mean("fork")
    samples = quantile_samples(fork, (0.125, 0.375, 0.625, 0.875))
    left_only = conditional_distribution("left_only")
    context_ignored = unconditional
    collapsed = {-1.0: 0.999, 1.0: 0.001}
    hallucinated = {-1.0: 0.45, 0.0: 0.1, 1.0: 0.45}
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
        "distribution_diagnostics": {
            "faithful": support_diagnostics(fork, fork_targets),
            "collapsed": support_diagnostics(collapsed, fork_targets),
            "hallucinated": support_diagnostics(hallucinated, fork_targets),
            "conditional_context_tv": total_variation_distance(fork, left_only),
            "context_ignored_tv": total_variation_distance(context_ignored, context_ignored),
        },
        "diffusion_endpoints": {
            "clean": diffusion_forward(1.0, -2.0, 1.0),
            "noise": diffusion_forward(1.0, -2.0, 0.0),
        },
        "flow_endpoints_and_velocity": {
            "start": flow_path(-2.0, 1.0, 0.0),
            "end": flow_path(-2.0, 1.0, 1.0),
        },
        "ensemble_disagreement_audit": ensemble_disagreement_audit(),
    }
