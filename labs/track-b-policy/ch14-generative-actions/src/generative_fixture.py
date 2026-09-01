"""Deterministic multimodal-action fixtures for Chapter 14."""

from __future__ import annotations

import math


VALID_MODES = (-1.0, 1.0)
INITIAL_NOISE = (-2.0, -1.5, -1.0, -0.5, -0.25, 0.25, 0.5, 1.0, 1.5, 2.0)
VALID_TOLERANCE = 0.25


def _finite_number(value: float, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _positive_integer(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def conditional_mean(demonstrations: tuple[float, ...] = VALID_MODES) -> float:
    """The scalar MSE optimum for equally weighted demonstrations."""
    if not demonstrations:
        raise ValueError("demonstrations must not be empty")
    values = tuple(_finite_number(value, name="demonstration") for value in demonstrations)
    return sum(values) / len(values)


def nearest_mode(value: float) -> float:
    """Resolve ties toward the positive mode to keep the fixture deterministic."""
    value = _finite_number(value, name="value")
    return min(VALID_MODES, key=lambda mode: (abs(value - mode), -mode))


def nearest_mode_distance(value: float) -> float:
    value = _finite_number(value, name="value")
    return min(abs(value - mode) for mode in VALID_MODES)


def mode_refinement(initial: float, steps: int, rate: float = 0.5) -> float:
    """Iteratively approach a mode; an interface fixture, not a DDPM sampler."""
    initial = _finite_number(initial, name="initial")
    rate = _finite_number(rate, name="rate")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("steps must be non-negative")
    if not 0.0 < rate <= 1.0:
        raise ValueError("rate must be in (0, 1]")
    value = initial
    for _ in range(steps):
        value += rate * (nearest_mode(value) - value)
    return value


def oracle_straight_flow(initial: float, steps: int) -> float:
    """Euler-integrate an oracle straight path from base sample to assigned mode."""
    initial = _finite_number(initial, name="initial")
    _positive_integer(steps, name="steps")
    target = nearest_mode(initial)
    velocity = target - initial
    dt = 1.0 / steps
    value = initial
    for _ in range(steps):
        value += velocity * dt
    return value


def summarize(samples: tuple[float, ...]) -> dict[str, float | int]:
    if not samples:
        raise ValueError("samples must not be empty")
    samples = tuple(_finite_number(value, name="sample") for value in samples)
    distances = tuple(nearest_mode_distance(value) for value in samples)
    valid = tuple(distance <= VALID_TOLERANCE for distance in distances)
    covered = {
        nearest_mode(value)
        for value, is_valid in zip(samples, valid)
        if is_valid
    }
    return {
        "sample_count": len(samples),
        "mean_nearest_mode_distance": sum(distances) / len(distances),
        "invalid_action_rate": 1.0 - sum(valid) / len(valid),
        "covered_mode_count": len(covered),
        "sample_mean": sum(samples) / len(samples),
    }


def mode_frequency_report(
    samples: tuple[float, ...],
    target_mode_probabilities: tuple[float, float] = (0.5, 0.5),
) -> dict[str, float | int]:
    """Audit mode frequencies after holding every generated sample valid."""
    if not samples:
        raise ValueError("samples must not be empty")
    samples = tuple(_finite_number(value, name="sample") for value in samples)
    if any(nearest_mode_distance(value) > VALID_TOLERANCE for value in samples):
        raise ValueError("mode-frequency audit requires every sample to be mode-valid")
    if not isinstance(target_mode_probabilities, tuple) or len(target_mode_probabilities) != len(VALID_MODES):
        raise ValueError("target_mode_probabilities must provide one probability per mode")
    targets = tuple(
        _finite_number(value, name="target mode probability") for value in target_mode_probabilities
    )
    if any(value < 0.0 for value in targets) or not math.isclose(sum(targets), 1.0, abs_tol=1e-12):
        raise ValueError("target mode probabilities must be non-negative and sum to one")

    counts = tuple(sum(nearest_mode(value) == mode for value in samples) for mode in VALID_MODES)
    empirical = tuple(count / len(samples) for count in counts)
    total_variation = 0.5 * sum(abs(observed - target) for observed, target in zip(empirical, targets))
    return {
        "sample_count": len(samples),
        "valid_action_rate": 1.0,
        "covered_mode_count": sum(count > 0 for count in counts),
        "negative_mode_count": counts[0],
        "positive_mode_count": counts[1],
        "negative_mode_empirical_probability": empirical[0],
        "positive_mode_empirical_probability": empirical[1],
        "target_negative_mode_probability": targets[0],
        "target_positive_mode_probability": targets[1],
        "empirical_total_variation_to_target": round(total_variation, 12),
    }


def sampling_budget_report(
    solver_steps: int,
    candidate_count: int,
    batch_capacity: int,
    available_forward_passes: int,
) -> dict[str, int | bool]:
    """Count abstract forwards without equating batching to measured latency."""
    solver_steps = _positive_integer(solver_steps, name="solver_steps")
    candidate_count = _positive_integer(candidate_count, name="candidate_count")
    batch_capacity = _positive_integer(batch_capacity, name="batch_capacity")
    if (
        isinstance(available_forward_passes, bool)
        or not isinstance(available_forward_passes, int)
        or available_forward_passes < 0
    ):
        raise ValueError("available_forward_passes must be a non-negative integer")
    batches_per_solver_step = math.ceil(candidate_count / batch_capacity)
    forward_pass_count = solver_steps * batches_per_solver_step
    return {
        "solver_step_count": solver_steps,
        "candidate_count": candidate_count,
        "batch_capacity": batch_capacity,
        "sample_model_evaluation_count": solver_steps * candidate_count,
        "batches_per_solver_step": batches_per_solver_step,
        "forward_pass_count": forward_pass_count,
        "available_forward_pass_count": available_forward_passes,
        "fits_abstract_forward_budget": forward_pass_count <= available_forward_passes,
    }


def candidate_availability_audit(
    per_candidate_acceptance_probability: float = 0.2,
    candidate_counts: tuple[int, ...] = (1, 4, 16),
    solver_steps: int = 4,
    batch_capacity: int = 10,
) -> list[dict[str, float | int]]:
    """Compare iid and perfectly correlated best-of-N availability.

    The probability is authored and the two dependence structures are analytic
    endpoints. They diagnose an assumption in candidate-count arguments; they
    do not estimate any generator, selector, or safety-gate performance.
    """
    probability = _finite_number(
        per_candidate_acceptance_probability,
        name="per_candidate_acceptance_probability",
    )
    if not 0.0 <= probability <= 1.0:
        raise ValueError("per_candidate_acceptance_probability must be in [0, 1]")
    if (
        not isinstance(candidate_counts, tuple)
        or not candidate_counts
        or any(
            isinstance(count, bool) or not isinstance(count, int) or count <= 0
            for count in candidate_counts
        )
        or len(set(candidate_counts)) != len(candidate_counts)
    ):
        raise ValueError("candidate_counts must be a non-empty tuple of unique positive integers")
    solver_steps = _positive_integer(solver_steps, name="solver_steps")
    batch_capacity = _positive_integer(batch_capacity, name="batch_capacity")

    rows = []
    for count in candidate_counts:
        iid_any = 1.0 - (1.0 - probability) ** count
        correlated_any = probability
        rows.append(
            {
                "candidate_count": count,
                "solver_step_count": solver_steps,
                "batch_capacity": batch_capacity,
                "sample_model_evaluation_count": solver_steps * count,
                "forward_pass_count": solver_steps * math.ceil(count / batch_capacity),
                "per_candidate_acceptance_probability": probability,
                "iid_any_accepted_probability": round(iid_any, 12),
                "iid_fallback_probability": round(1.0 - iid_any, 12),
                "perfectly_correlated_any_accepted_probability": round(correlated_any, 12),
                "perfectly_correlated_fallback_probability": round(1.0 - correlated_any, 12),
            }
        )
    return rows


def screen_candidates(
    samples: tuple[float, ...],
    blocked_interval: tuple[float, float] = (-1.25, -0.75),
    fallback_action: float = 0.0,
) -> dict[str, int | float | bool]:
    """Apply an independent hand-authored safety gate to generated candidates."""
    if not samples:
        raise ValueError("samples must not be empty")
    samples = tuple(_finite_number(value, name="sample") for value in samples)
    if not isinstance(blocked_interval, tuple) or len(blocked_interval) != 2:
        raise ValueError("blocked_interval must contain lower and upper bounds")
    lower = _finite_number(blocked_interval[0], name="blocked lower bound")
    upper = _finite_number(blocked_interval[1], name="blocked upper bound")
    if lower > upper:
        raise ValueError("blocked_interval lower bound must not exceed upper bound")
    fallback_action = _finite_number(fallback_action, name="fallback_action")

    validity = tuple(nearest_mode_distance(value) <= VALID_TOLERANCE for value in samples)
    blocked = tuple(lower <= value <= upper for value in samples)
    accepted = tuple(valid and not is_blocked for valid, is_blocked in zip(validity, blocked))
    selected = next((value for value, allowed in zip(samples, accepted) if allowed), fallback_action)
    return {
        "candidate_count": len(samples),
        "valid_action_count": sum(validity),
        "invalid_action_count": len(samples) - sum(validity),
        "safety_rejected_valid_count": sum(valid and is_blocked for valid, is_blocked in zip(validity, blocked)),
        "safety_accepted_count": sum(accepted),
        "fallback_used": not any(accepted),
        "selected_action": selected,
    }


def evaluate() -> dict[str, object]:
    mean_action = conditional_mean()
    mean_samples = tuple(mean_action for _ in INITIAL_NOISE)
    refinement_one = tuple(mode_refinement(value, steps=1) for value in INITIAL_NOISE)
    refinement_four = tuple(mode_refinement(value, steps=4) for value in INITIAL_NOISE)
    flow_one = tuple(oracle_straight_flow(value, steps=1) for value in INITIAL_NOISE)
    return {
        "mse_mean": {
            **summarize(mean_samples),
            "sample_model_evaluations": len(INITIAL_NOISE),
        },
        "mode_refinement_1_step": {
            **summarize(refinement_one),
            "sample_model_evaluations": len(INITIAL_NOISE),
        },
        "mode_refinement_4_steps": {
            **summarize(refinement_four),
            "sample_model_evaluations": 4 * len(INITIAL_NOISE),
        },
        "oracle_straight_flow_1_step": {
            **summarize(flow_one),
            "sample_model_evaluations": len(INITIAL_NOISE),
        },
        "mode_frequency_calibration": {
            "balanced_5_to_5": mode_frequency_report((-1.0,) * 5 + (1.0,) * 5),
            "imbalanced_9_to_1": mode_frequency_report((-1.0,) * 9 + (1.0,)),
        },
        "control_budget": {
            "sequential_10_candidates_4_steps": sampling_budget_report(4, 10, 1, 8),
            "single_batch_10_candidates_4_steps": sampling_budget_report(4, 10, 10, 8),
            "single_batch_10_candidates_16_steps": sampling_budget_report(16, 10, 10, 8),
        },
        "candidate_availability": candidate_availability_audit(),
        "safety_screen": {
            "mixed_modes": screen_candidates(flow_one),
            "all_candidates_blocked": screen_candidates((-1.0, -1.0)),
        },
    }
