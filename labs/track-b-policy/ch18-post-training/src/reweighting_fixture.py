"""Offline trajectory reweighting fixtures for Chapter 18."""

from __future__ import annotations

from math import isfinite
from typing import Sequence


TRAJECTORIES = (
    {"id": "success-a", "reward": 1.0, "actions": (0.2, 0.8), "final_event": "grasp"},
    {"id": "success-b", "reward": 1.0, "actions": (0.3, 0.7), "final_event": "grasp"},
    {"id": "failure-recovery-a", "reward": 0.0, "actions": (0.8, 0.2), "final_event": "recover"},
    {"id": "failure-recovery-b", "reward": 0.0, "actions": (0.9, 0.1), "final_event": "recover"},
)


def _finite_weights(weights: Sequence[float], expected_length: int) -> tuple[float, ...]:
    if isinstance(weights, (str, bytes)) or not isinstance(weights, Sequence) or len(weights) != expected_length:
        raise ValueError("weights must match the trajectory count")
    converted = []
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not isfinite(weight) or weight < 0:
            raise ValueError("weights must be finite non-negative numbers")
        converted.append(float(weight))
    if sum(converted) <= 0:
        raise ValueError("at least one weight must be positive")
    return tuple(converted)


def summarize(weights: Sequence[float]) -> dict[str, object]:
    weights_ = _finite_weights(weights, len(TRAJECTORIES))
    total = sum(weights_)
    action_target = tuple(
        round(sum(weight * trajectory["actions"][step] for weight, trajectory in zip(weights_, TRAJECTORIES)) / total, 12)
        for step in range(2)
    )
    effective_sample_size = total * total / sum(weight * weight for weight in weights_)
    recovery_mass = sum(
        weight for weight, trajectory in zip(weights_, TRAJECTORIES) if trajectory["final_event"] == "recover"
    ) / total
    return {
        "weights": weights_,
        "action_target": action_target,
        "effective_sample_size": round(effective_sample_size, 12),
        "recovery_mass": round(recovery_mass, 12),
    }


def mean_absolute_error(values: Sequence[float], reference: Sequence[float]) -> float:
    if len(values) != len(reference) or not values:
        raise ValueError("values and reference must have the same non-zero length")
    pairs = zip(values, reference)
    errors = []
    for value, target in pairs:
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not isfinite(item) for item in (value, target)):
            raise ValueError("values and reference must contain finite numbers")
        errors.append(abs(float(value) - float(target)))
    return round(sum(errors) / len(errors), 12)


def within_dataset_support(actions: Sequence[float]) -> bool:
    if isinstance(actions, (str, bytes)) or not isinstance(actions, Sequence) or len(actions) != 2:
        raise ValueError("actions must contain exactly two phases")
    for value in actions:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError("actions must contain finite numbers")
    for step, value in enumerate(actions):
        observed = tuple(trajectory["actions"][step] for trajectory in TRAJECTORIES)
        if value < min(observed) or value > max(observed):
            return False
    return True


def evaluate() -> dict[str, object]:
    uniform = summarize((1.0, 1.0, 1.0, 1.0))
    reward_weighted = summarize((3.0, 3.0, 1.0, 1.0))
    success_only = summarize((1.0, 1.0, 0.0, 0.0))
    successful_reference = (0.25, 0.75)
    return {
        "uniform": {**uniform, "reference_mae": mean_absolute_error(uniform["action_target"], successful_reference)},
        "reward_weighted": {
            **reward_weighted,
            "reference_mae": mean_absolute_error(reward_weighted["action_target"], successful_reference),
        },
        "success_only": {
            **success_only,
            "reference_mae": mean_absolute_error(success_only["action_target"], successful_reference),
        },
        "support_gate": {
            "successful_reference_in_support": within_dataset_support(successful_reference),
            "out_of_support_proposal_accepted": within_dataset_support((-0.1, 1.1)),
        },
    }
