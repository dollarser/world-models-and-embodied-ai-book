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


def lambda_trace_continuations(
    terminated: Sequence[bool], truncated: Sequence[bool]
) -> tuple[bool, ...]:
    """Keep lambda recursion inside one sampled episode or sequence segment."""

    terminated_ = _boolean_sequence("terminated", terminated)
    truncated_ = _boolean_sequence("truncated", truncated)
    if len(terminated_) != len(truncated_):
        raise ValueError("terminated and truncated must have equal lengths")
    return tuple(not (is_terminal or is_truncated) for is_terminal, is_truncated in zip(terminated_, truncated_))


def lambda_returns(
    rewards: Sequence[float],
    discounts: Sequence[float],
    next_values: Sequence[float],
    lambda_: float,
    trace_continuations: Sequence[bool] | None = None,
) -> tuple[float, ...]:
    """Compute backward lambda returns for a finite imagined trajectory.

    discounts already include both the scalar discount and continuation mask.
    next_values[t] is V(s_{t+1}); the final recursion bootstraps from the final
    next value before applying the same lambda-return equation as other steps.
    trace_continuations[t] is false at any sampled sequence boundary, including
    a truncation that keeps value bootstrap but must not consume the next row's
    return. It defaults to true for a single uninterrupted imagined sequence.
    """

    rewards_ = _finite_sequence("rewards", rewards)
    discounts_ = _finite_sequence("discounts", discounts)
    next_values_ = _finite_sequence("next_values", next_values)
    if not (len(rewards_) == len(discounts_) == len(next_values_)):
        raise ValueError("rewards, discounts, and next_values must have equal lengths")
    if trace_continuations is None:
        trace_continuations_ = (True,) * len(rewards_)
    else:
        trace_continuations_ = _boolean_sequence("trace_continuations", trace_continuations)
        if len(trace_continuations_) != len(rewards_):
            raise ValueError("trace_continuations must have the same length as rewards")
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
        trace_factor = lambda_value * float(trace_continuations_[index])
        mixed_value = (1.0 - trace_factor) * next_values_[index] + trace_factor * recursive_target
        recursive_target = rewards_[index] + discounts_[index] * mixed_value
        targets[index] = round(recursive_target, 12)
    return tuple(targets)


def cumulative_loss_weights(discounts: Sequence[float]) -> tuple[float, ...]:
    """Weight each imagined step by survival up to that step.

    discounts[t] gates the transition after step t. Therefore the loss at the
    first step has weight 1, and the loss at step t receives the product of all
    earlier discounts. This is an interface fixture, not an exact reproduction
    of any Dreamer implementation's reduction or normalization.
    """

    discounts_ = _finite_sequence("discounts", discounts)
    if any(discount < 0.0 or discount > 1.0 for discount in discounts_):
        raise ValueError("discounts must lie in [0, 1]")
    weights = [1.0]
    for discount in discounts_[:-1]:
        weights.append(weights[-1] * discount)
    return tuple(round(weight, 12) for weight in weights)


def weighted_loss_audit(
    losses: Sequence[float], discounts: Sequence[float]
) -> dict[str, object]:
    """Expose post-terminal loss that survives an incorrect continuation mask."""

    losses_ = _finite_sequence("losses", losses)
    weights = cumulative_loss_weights(discounts)
    if len(losses_) != len(weights):
        raise ValueError("losses and discounts must have equal lengths")
    if any(loss < 0.0 for loss in losses_):
        raise ValueError("losses must be non-negative")
    contributions = tuple(round(loss * weight, 12) for loss, weight in zip(losses_, weights))
    return {
        "raw_losses": losses_,
        "cumulative_weights": weights,
        "weighted_contributions": contributions,
        "weighted_loss_sum": round(sum(contributions), 12),
    }


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
    cross_episode_terminated = (False, True)
    cross_episode_truncated = (True, False)
    cross_episode_discounts = bootstrap_discounts(
        cross_episode_terminated,
        cross_episode_truncated,
        (True, False),
    )
    cross_episode_traces = lambda_trace_continuations(
        cross_episode_terminated,
        cross_episode_truncated,
    )
    boundary_safe_targets = lambda_returns(
        (1.0, 100.0),
        cross_episode_discounts,
        (4.0, 0.0),
        1.0,
        cross_episode_traces,
    )
    boundary_ignored_targets = lambda_returns(
        (1.0, 100.0),
        cross_episode_discounts,
        (4.0, 0.0),
        1.0,
    )
    correct_loss_weighting = weighted_loss_audit((1.0, 1.0, 100.0), (1.0, 0.0, 0.0))
    missing_mask_loss_weighting = weighted_loss_audit((1.0, 1.0, 100.0), (1.0, 1.0, 0.0))

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
        "truncation_trace_boundary": {
            "bootstrap_discounts": cross_episode_discounts,
            "lambda_trace_continuations": cross_episode_traces,
            "boundary_safe_targets": boundary_safe_targets,
            "boundary_ignored_targets": boundary_ignored_targets,
            "cross_episode_start_target_leakage": round(
                boundary_ignored_targets[0] - boundary_safe_targets[0], 12
            ),
            "scope": "two adjacent authored rows from different episodes; not an estimated replay corruption rate",
        },
        "imagined_loss_weighting": {
            "correct_mask": correct_loss_weighting,
            "missing_mask": missing_mask_loss_weighting,
            "post_terminal_loss_leakage": round(
                missing_mask_loss_weighting["weighted_loss_sum"]
                - correct_loss_weighting["weighted_loss_sum"],
                12,
            ),
            "scope": "hand-authored per-step losses and cumulative survival weights; not an actor or critic update",
        },
    }
