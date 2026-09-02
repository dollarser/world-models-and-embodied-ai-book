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

JOINT_SUPPORT_MAX_MAE = 0.1


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


def joint_support_report(
    actions: Sequence[float], max_mean_absolute_distance: float = JOINT_SUPPORT_MAX_MAE
) -> dict[str, object]:
    """Compare a proposal with complete observed trajectories, not marginal ranges."""
    if (
        isinstance(max_mean_absolute_distance, bool)
        or not isinstance(max_mean_absolute_distance, (int, float))
        or not isfinite(max_mean_absolute_distance)
        or max_mean_absolute_distance < 0.0
    ):
        raise ValueError("joint-support distance must be a finite non-negative number")
    # Reuse the marginal validator before computing distances.
    marginal_accepted = within_dataset_support(actions)
    distances = tuple(
        (trajectory["id"], mean_absolute_error(actions, trajectory["actions"]))
        for trajectory in TRAJECTORIES
    )
    nearest_id, nearest_distance = min(distances, key=lambda item: (item[1], item[0]))
    return {
        "marginal_range_accepted": marginal_accepted,
        "nearest_trajectory_id": nearest_id,
        "nearest_trajectory_mae": nearest_distance,
        "maximum_allowed_mae": float(max_mean_absolute_distance),
        "joint_support_accepted": nearest_distance <= max_mean_absolute_distance,
    }


def leave_one_out_advantages(rewards: Sequence[float]) -> tuple[float, ...]:
    """Compute an unnormalized reward-minus-other-samples baseline per group."""
    if isinstance(rewards, (str, bytes)) or not isinstance(rewards, Sequence) or len(rewards) < 2:
        raise ValueError("leave-one-out rewards require at least two samples")
    converted = []
    for reward in rewards:
        if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not isfinite(reward):
            raise ValueError("rewards must be finite numbers")
        converted.append(float(reward))
    total = sum(converted)
    count_other = len(converted) - 1
    return tuple(round(reward - (total - reward) / count_other, 12) for reward in converted)


def advantage_group_report(rewards: Sequence[float]) -> dict[str, object]:
    advantages = leave_one_out_advantages(rewards)
    return {
        "rewards": tuple(float(reward) for reward in rewards),
        "advantages": advantages,
        "has_nonzero_learning_signal": any(abs(value) > 0.0 for value in advantages),
    }


def dynamic_rejection_report(
    groups: Sequence[tuple[str, Sequence[float]]],
) -> dict[str, object]:
    """Expose how rejecting zero-advantage groups changes the used context mix."""
    if isinstance(groups, (str, bytes)) or not isinstance(groups, Sequence) or not groups:
        raise ValueError("dynamic-sampling groups must be a non-empty sequence")
    attempted_counts: dict[str, int] = {}
    used_counts: dict[str, int] = {}
    rejected_group_ids = []
    used_group_ids = []
    attempted_rollout_count = 0
    used_rollout_count = 0
    for index, group in enumerate(groups):
        if not isinstance(group, tuple) or len(group) != 2:
            raise ValueError("each group must contain a difficulty label and rewards")
        difficulty, rewards = group
        if not isinstance(difficulty, str) or not difficulty.strip():
            raise ValueError("difficulty labels must be non-empty strings")
        report = advantage_group_report(rewards)
        attempted_counts[difficulty] = attempted_counts.get(difficulty, 0) + 1
        attempted_rollout_count += len(rewards)
        group_id = f"{difficulty}-{index}"
        if report["has_nonzero_learning_signal"]:
            used_counts[difficulty] = used_counts.get(difficulty, 0) + 1
            used_group_ids.append(group_id)
            used_rollout_count += len(rewards)
        else:
            rejected_group_ids.append(group_id)

    labels = tuple(sorted(attempted_counts))
    attempted_group_count = len(groups)
    used_group_count = len(used_group_ids)
    if used_group_count == 0:
        raise ValueError("at least one group must retain non-zero advantage signal")
    return {
        "attempted_group_count": attempted_group_count,
        "used_group_count": used_group_count,
        "rejected_group_count": len(rejected_group_ids),
        "group_acceptance_rate": round(used_group_count / attempted_group_count, 12),
        "attempted_rollout_count": attempted_rollout_count,
        "used_rollout_count": used_rollout_count,
        "rejected_rollout_count": attempted_rollout_count - used_rollout_count,
        "attempted_difficulty_distribution": {
            label: round(attempted_counts[label] / attempted_group_count, 12) for label in labels
        },
        "used_difficulty_distribution": {
            label: round(used_counts.get(label, 0) / used_group_count, 12) for label in labels
        },
        "rejection_rate_by_difficulty": {
            label: round(1.0 - used_counts.get(label, 0) / attempted_counts[label], 12) for label in labels
        },
        "used_group_ids": tuple(used_group_ids),
        "rejected_group_ids": tuple(rejected_group_ids),
    }


def resampling_history_audit() -> dict[str, object]:
    """Contrast two attempt histories that yield the same used training batch."""
    clean = dynamic_rejection_report(
        (
            ("medium", (1.0, 0.0, 0.0)),
            ("medium", (0.0, 1.0, 0.0)),
        )
    )
    rejection_heavy = dynamic_rejection_report(
        (
            ("easy", (1.0, 1.0, 1.0)),
            ("hard", (0.0, 0.0, 0.0)),
            ("medium", (1.0, 0.0, 0.0)),
            ("medium", (0.0, 1.0, 0.0)),
        )
    )
    clean_nonzero_used = {
        label: fraction
        for label, fraction in clean["used_difficulty_distribution"].items()
        if fraction > 0.0
    }
    rejection_heavy_nonzero_used = {
        label: fraction
        for label, fraction in rejection_heavy["used_difficulty_distribution"].items()
        if fraction > 0.0
    }
    same_used_batch_summary = (
        clean["used_group_count"] == rejection_heavy["used_group_count"]
        and clean["used_rollout_count"] == rejection_heavy["used_rollout_count"]
        and clean_nonzero_used == rejection_heavy_nonzero_used
    )
    summary_keys = (
        "attempted_group_count",
        "attempted_rollout_count",
        "rejected_group_count",
        "rejected_rollout_count",
        "used_group_count",
        "used_rollout_count",
        "attempted_difficulty_distribution",
        "used_difficulty_distribution",
    )
    return {
        "same_used_batch_summary": same_used_batch_summary,
        "clean_history": {key: clean[key] for key in summary_keys},
        "rejection_heavy_history": {key: rejection_heavy[key] for key in summary_keys},
        "attempted_rollout_ratio": round(
            rejection_heavy["attempted_rollout_count"] / clean["attempted_rollout_count"],
            12,
        ),
        "hidden_extra_attempted_rollouts": (
            rejection_heavy["attempted_rollout_count"] - clean["attempted_rollout_count"]
        ),
        "scope": "two authored deterministic attempt streams; not an expected resampling cost",
    }


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
            "successful_reference": joint_support_report(successful_reference),
            "marginal_extreme": joint_support_report((-0.1, 1.1)),
            "unseen_hybrid": joint_support_report((0.9, 0.8)),
        },
        "leave_one_out_advantage": {
            "all_success": advantage_group_report((1.0, 1.0, 1.0)),
            "all_failure": advantage_group_report((0.0, 0.0, 0.0)),
            "mixed": advantage_group_report((1.0, 0.0, 0.0)),
        },
        "dynamic_rejection": dynamic_rejection_report(
            (
                ("easy", (1.0, 1.0, 1.0)),
                ("medium", (1.0, 0.0, 0.0)),
                ("hard", (0.0, 0.0, 0.0)),
                ("medium", (0.0, 1.0, 0.0)),
            )
        ),
        "resampling_history_audit": resampling_history_audit(),
    }
