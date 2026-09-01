"""Analytic lambda-return fixtures for Chapter 8."""

from __future__ import annotations

from math import isfinite
from typing import Sequence


def _finite_sequence(name: str, values: Sequence[float]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise ValueError(f"{name} must be a non-empty numeric sequence")
    converted = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{name} must contain only finite numbers")
        converted.append(float(value))
    return tuple(converted)


def _boolean_sequence(name: str, values: Sequence[bool]) -> tuple[bool, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise ValueError(f"{name} must be a non-empty boolean sequence")
    if any(not isinstance(value, bool) for value in values):
        raise ValueError(f"{name} must contain only booleans")
    return tuple(values)


def bootstrap_discounts(
    terminated: Sequence[bool],
    truncated: Sequence[bool],
    next_observation_valid: Sequence[bool],
    gamma: float = 1.0,
) -> tuple[float, ...]:
    """Build value-target discounts without collapsing episode-end semantics.

    Both termination and truncation end a sampled sequence. Only an MDP terminal
    state closes value bootstrap. A truncated or continuing transition needs a
    valid next observation; otherwise the target is invalid rather than a zero-
    bootstrap target.
    """

    terminated_ = _boolean_sequence("terminated", terminated)
    truncated_ = _boolean_sequence("truncated", truncated)
    observation_valid_ = _boolean_sequence("next_observation_valid", next_observation_valid)
    if not (len(terminated_) == len(truncated_) == len(observation_valid_)):
        raise ValueError("end flags and next_observation_valid must have equal lengths")
    if isinstance(gamma, bool) or not isinstance(gamma, (int, float)) or not isfinite(gamma):
        raise ValueError("gamma must be a finite number")
    gamma_ = float(gamma)
    if gamma_ < 0.0 or gamma_ > 1.0:
        raise ValueError("gamma must lie in [0, 1]")

    discounts = []
    for index, (is_terminal, is_truncated, observation_valid) in enumerate(
        zip(terminated_, truncated_, observation_valid_)
    ):
        if not is_terminal and not observation_valid:
            raise ValueError(f"transition {index} needs a valid next observation for bootstrap")
        discounts.append(0.0 if is_terminal else gamma_)
    return tuple(discounts)


def lambda_returns(
    rewards: Sequence[float],
    discounts: Sequence[float],
    next_values: Sequence[float],
    lambda_: float,
) -> tuple[float, ...]:
    """Compute backward lambda returns for a finite imagined trajectory.

    discounts already include both the scalar discount and continuation mask.
    next_values[t] is V(s_{t+1}); the final recursion bootstraps from the final
    next value before applying the same lambda-return equation as other steps.
    """

    rewards_ = _finite_sequence("rewards", rewards)
    discounts_ = _finite_sequence("discounts", discounts)
    next_values_ = _finite_sequence("next_values", next_values)
    if not (len(rewards_) == len(discounts_) == len(next_values_)):
        raise ValueError("rewards, discounts, and next_values must have equal lengths")
    if any(discount < 0.0 or discount > 1.0 for discount in discounts_):
        raise ValueError("discounts must lie in [0, 1]")
    if isinstance(lambda_, bool) or not isinstance(lambda_, (int, float)) or not isfinite(lambda_):
        raise ValueError("lambda_ must be a finite number")
    lambda_value = float(lambda_)
    if lambda_value < 0.0 or lambda_value > 1.0:
        raise ValueError("lambda_ must lie in [0, 1]")

    targets = [0.0] * len(rewards_)
    recursive_target = next_values_[-1]
    for index in range(len(rewards_) - 1, -1, -1):
        mixed_value = (1.0 - lambda_value) * next_values_[index] + lambda_value * recursive_target
        recursive_target = rewards_[index] + discounts_[index] * mixed_value
        targets[index] = round(recursive_target, 12)
    return tuple(targets)


def evaluate() -> dict[str, object]:
    rewards = (0.0, 0.0, 1.0)
    discounts = (1.0, 1.0, 0.0)
    next_values = (0.4, 0.8, 0.0)
    lambda_zero = lambda_returns(rewards, discounts, next_values, 0.0)
    lambda_half = lambda_returns(rewards, discounts, next_values, 0.5)
    lambda_one = lambda_returns(rewards, discounts, next_values, 1.0)

    biased_reward_targets = lambda_returns((0.0, 0.0, 2.0), discounts, next_values, 1.0)
    correct_terminal_targets = lambda_returns((0.0, 1.0, 10.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0)
    missing_terminal_targets = lambda_returns((0.0, 1.0, 10.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0), 1.0)
    terminal_discount = bootstrap_discounts((True,), (False,), (False,))
    truncation_discount = bootstrap_discounts((False,), (True,), (True,))
    simultaneous_end_discount = bootstrap_discounts((True,), (True,), (False,))
    terminal_target = lambda_returns((1.0,), terminal_discount, (4.0,), 0.0)
    truncation_target = lambda_returns((1.0,), truncation_discount, (4.0,), 0.0)
    collapsed_done_target = lambda_returns((1.0,), (0.0,), (4.0,), 0.0)

    return {
        "lambda_targets": {
            "lambda_0": lambda_zero,
            "lambda_0_5": lambda_half,
            "lambda_1": lambda_one,
        },
        "reward_model_bias": {
            "reference_targets": lambda_one,
            "biased_targets": biased_reward_targets,
            "start_target_gap": round(biased_reward_targets[0] - lambda_one[0], 12),
        },
        "continuation_mask": {
            "correct_targets": correct_terminal_targets,
            "missing_mask_targets": missing_terminal_targets,
            "correct_start_target": correct_terminal_targets[0],
            "leaked_start_target": missing_terminal_targets[0],
            "leakage_gap": round(missing_terminal_targets[0] - correct_terminal_targets[0], 12),
        },
        "episode_end_semantics": {
            "terminal_bootstrap_discount": terminal_discount[0],
            "truncation_bootstrap_discount": truncation_discount[0],
            "simultaneous_end_bootstrap_discount": simultaneous_end_discount[0],
            "terminal_target": terminal_target[0],
            "truncation_target": truncation_target[0],
            "collapsed_done_target": collapsed_done_target[0],
            "truncation_bootstrap_loss": round(truncation_target[0] - collapsed_done_target[0], 12),
        },
    }
