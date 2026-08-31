"""Deterministic multimodal-action fixtures for Chapter 14."""

from __future__ import annotations


VALID_MODES = (-1.0, 1.0)
INITIAL_NOISE = (-2.0, -1.5, -1.0, -0.5, -0.25, 0.25, 0.5, 1.0, 1.5, 2.0)
VALID_TOLERANCE = 0.25


def conditional_mean(demonstrations: tuple[float, ...] = VALID_MODES) -> float:
    """The scalar MSE optimum for equally weighted demonstrations."""
    return sum(demonstrations) / len(demonstrations)


def nearest_mode(value: float) -> float:
    """Resolve ties toward the positive mode to keep the fixture deterministic."""
    return min(VALID_MODES, key=lambda mode: (abs(value - mode), -mode))


def nearest_mode_distance(value: float) -> float:
    return min(abs(value - mode) for mode in VALID_MODES)


def mode_refinement(initial: float, steps: int, rate: float = 0.5) -> float:
    """Iteratively approach a mode; an interface fixture, not a DDPM sampler."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    value = initial
    for _ in range(steps):
        value += rate * (nearest_mode(value) - value)
    return value


def oracle_straight_flow(initial: float, steps: int) -> float:
    """Euler-integrate an oracle straight path from base sample to assigned mode."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    target = nearest_mode(initial)
    velocity = target - initial
    dt = 1.0 / steps
    value = initial
    for _ in range(steps):
        value += velocity * dt
    return value


def summarize(samples: tuple[float, ...]) -> dict[str, float | int]:
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


def sampling_fits_budget(steps_per_sample: int, available_evaluations: int = 8) -> bool:
    if steps_per_sample <= 0 or available_evaluations < 0:
        raise ValueError("steps must be positive and budget must be non-negative")
    return steps_per_sample <= available_evaluations


def evaluate() -> dict[str, object]:
    mean_action = conditional_mean()
    mean_samples = tuple(mean_action for _ in INITIAL_NOISE)
    refinement_one = tuple(mode_refinement(value, steps=1) for value in INITIAL_NOISE)
    refinement_four = tuple(mode_refinement(value, steps=4) for value in INITIAL_NOISE)
    flow_one = tuple(oracle_straight_flow(value, steps=1) for value in INITIAL_NOISE)
    return {
        "mse_mean": {
            **summarize(mean_samples),
            "model_evaluations": len(INITIAL_NOISE),
        },
        "mode_refinement_1_step": {
            **summarize(refinement_one),
            "model_evaluations": len(INITIAL_NOISE),
        },
        "mode_refinement_4_steps": {
            **summarize(refinement_four),
            "model_evaluations": 4 * len(INITIAL_NOISE),
        },
        "oracle_straight_flow_1_step": {
            **summarize(flow_one),
            "model_evaluations": len(INITIAL_NOISE),
        },
        "control_budget": {
            "available_model_evaluations_per_replan": 8,
            "refinement_4_steps_feasible": sampling_fits_budget(4),
            "refinement_16_steps_feasible": sampling_fits_budget(16),
        },
    }
