"""A fixed episode table for exposing evaluation-protocol drift."""

from __future__ import annotations

from itertools import product
from math import isfinite, sqrt
from typing import Sequence


EPISODES = (
    {"id": "easy-1", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "easy-2", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "easy-3", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "easy-4", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "hard-1", "suite": "hard", "goal": True, "collision": False, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "hard-2", "suite": "hard", "goal": False, "collision": False, "intervention": False, "route": 0.7, "terminated": False, "truncated": True, "valid": True, "invalid_reason": None},
    {"id": "hard-3", "suite": "hard", "goal": True, "collision": True, "intervention": False, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
    {"id": "hard-4", "suite": "hard", "goal": True, "collision": False, "intervention": True, "route": 1.0, "terminated": True, "truncated": False, "valid": True, "invalid_reason": None},
)


PROTOCOLS = {
    "easy_goal_only": {"suites": ("easy",), "safety_aware": False},
    "easy_safety_aware": {"suites": ("easy",), "safety_aware": True},
    "full_goal_only": {"suites": ("easy", "hard"), "safety_aware": False},
    "full_safety_aware": {"suites": ("easy", "hard"), "safety_aware": True},
}


PAIRED_CLUSTER_ROWS = (
    {"pair_id": "route-a-1", "cluster": "route-a", "candidate_success": True, "baseline_success": True},
    {"pair_id": "route-a-2", "cluster": "route-a", "candidate_success": True, "baseline_success": True},
    {"pair_id": "route-a-3", "cluster": "route-a", "candidate_success": True, "baseline_success": True},
    {"pair_id": "route-a-4", "cluster": "route-a", "candidate_success": True, "baseline_success": True},
    {"pair_id": "route-b-1", "cluster": "route-b", "candidate_success": True, "baseline_success": False},
    {"pair_id": "route-b-2", "cluster": "route-b", "candidate_success": True, "baseline_success": False},
    {"pair_id": "route-b-3", "cluster": "route-b", "candidate_success": True, "baseline_success": False},
    {"pair_id": "route-b-4", "cluster": "route-b", "candidate_success": True, "baseline_success": False},
    {"pair_id": "route-c-1", "cluster": "route-c", "candidate_success": False, "baseline_success": True},
    {"pair_id": "route-d-1", "cluster": "route-d", "candidate_success": True, "baseline_success": True},
)


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> dict[str, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("successes and trials must be integers, not booleans")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("successes and trials must be integers")
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    if isinstance(z, bool) or not isinstance(z, (int, float)):
        raise TypeError("z must be a real number")
    if not isfinite(z) or z <= 0:
        raise ValueError("z must be finite and positive")

    proportion = successes / trials
    z_squared = z * z
    denominator = 1 + z_squared / trials
    center = (proportion + z_squared / (2 * trials)) / denominator
    variance_term = proportion * (1 - proportion) / trials + z_squared / (4 * trials * trials)
    margin = z * sqrt(variance_term) / denominator
    return {
        "lower": round(max(0.0, center - margin), 6),
        "upper": round(min(1.0, center + margin), 6),
    }


def _linear_quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return ordered[lower_index] + weight * (ordered[upper_index] - ordered[lower_index])


def exact_paired_cluster_bootstrap(
    rows: Sequence[dict[str, object]] = PAIRED_CLUSTER_ROWS,
    confidence: float = 0.95,
    max_exact_resamples: int = 100_000,
) -> dict[str, object]:
    """Enumerate a tiny cluster bootstrap over paired candidate-baseline differences."""
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence) or not rows:
        raise ValueError("paired rows must be a non-empty sequence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise TypeError("confidence must be a real number")
    if not isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one")
    if isinstance(max_exact_resamples, bool) or not isinstance(max_exact_resamples, int):
        raise TypeError("max_exact_resamples must be an integer")
    if max_exact_resamples <= 0:
        raise ValueError("max_exact_resamples must be positive")

    cluster_differences: dict[str, list[float]] = {}
    seen_pair_ids: set[str] = set()
    candidate_successes = 0
    baseline_successes = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"paired row {index} must be a mapping")
        pair_id = row.get("pair_id")
        cluster = row.get("cluster")
        if not isinstance(pair_id, str) or not pair_id or pair_id in seen_pair_ids:
            raise ValueError("pair_id values must be non-empty and unique")
        if not isinstance(cluster, str) or not cluster:
            raise ValueError(f"paired row {pair_id} needs a non-empty cluster")
        candidate = row.get("candidate_success")
        baseline = row.get("baseline_success")
        if not isinstance(candidate, bool) or not isinstance(baseline, bool):
            raise ValueError(f"paired row {pair_id} success fields must be boolean")
        seen_pair_ids.add(pair_id)
        candidate_successes += int(candidate)
        baseline_successes += int(baseline)
        cluster_differences.setdefault(cluster, []).append(float(int(candidate) - int(baseline)))

    cluster_names = sorted(cluster_differences)
    if len(cluster_names) < 2:
        raise ValueError("paired cluster bootstrap requires at least two clusters")
    resample_count = len(cluster_names) ** len(cluster_names)
    if resample_count > max_exact_resamples:
        raise ValueError("exact cluster bootstrap exceeds max_exact_resamples")

    cluster_means = {
        cluster: sum(cluster_differences[cluster]) / len(cluster_differences[cluster])
        for cluster in cluster_names
    }
    bootstrap_values = [
        sum(cluster_means[cluster_names[index]] for index in sample) / len(cluster_names)
        for sample in product(range(len(cluster_names)), repeat=len(cluster_names))
    ]
    alpha = (1 - confidence) / 2
    pair_count = len(rows)
    return {
        "estimand": "candidate minus baseline success; clusters receive equal weight",
        "pair_count": pair_count,
        "cluster_count": len(cluster_names),
        "cluster_pair_counts": {
            cluster: len(cluster_differences[cluster]) for cluster in cluster_names
        },
        "cluster_differences": {
            cluster: round(cluster_means[cluster], 6) for cluster in cluster_names
        },
        "candidate_micro_success_rate": candidate_successes / pair_count,
        "baseline_micro_success_rate": baseline_successes / pair_count,
        "micro_paired_difference": (candidate_successes - baseline_successes) / pair_count,
        "macro_cluster_difference": sum(cluster_means.values()) / len(cluster_names),
        "cluster_bootstrap_95": {
            "lower": round(_linear_quantile(bootstrap_values, alpha), 6),
            "upper": round(_linear_quantile(bootstrap_values, 1 - alpha), 6),
        },
        "bootstrap_resample_count": resample_count,
    }


def audit_episode_rows(episodes: Sequence[dict[str, object]]) -> dict[str, object]:
    """Validate row semantics and expose invalid attempts without dropping them."""
    if isinstance(episodes, (str, bytes)) or not isinstance(episodes, Sequence) or not episodes:
        raise ValueError("episodes must be a non-empty sequence")

    invalid_ids = []
    invalid_reasons = {}
    terminated_count = 0
    truncated_count = 0
    seen_ids = set()
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            raise ValueError(f"episode {index} must be a mapping")
        episode_id = episode.get("id")
        if not isinstance(episode_id, str) or not episode_id or episode_id in seen_ids:
            raise ValueError("episode ids must be non-empty and unique")
        seen_ids.add(episode_id)
        if not isinstance(episode.get("suite"), str) or not episode["suite"]:
            raise ValueError(f"episode {episode_id} needs a non-empty suite")
        for field in ("goal", "collision", "intervention", "terminated", "truncated", "valid"):
            if not isinstance(episode.get(field), bool):
                raise ValueError(f"episode {episode_id} field {field} must be boolean")
        route = episode.get("route")
        if isinstance(route, bool) or not isinstance(route, (int, float)) or not isfinite(route):
            raise ValueError(f"episode {episode_id} route must be finite")
        if route < 0.0 or route > 1.0:
            raise ValueError(f"episode {episode_id} route must lie in [0, 1]")
        if not episode["terminated"] and not episode["truncated"]:
            raise ValueError(f"episode {episode_id} must have terminated or truncated at episode end")
        terminated_count += int(episode["terminated"])
        truncated_count += int(episode["truncated"])

        reason = episode.get("invalid_reason")
        if episode["valid"]:
            if reason is not None:
                raise ValueError(f"valid episode {episode_id} cannot have invalid_reason")
        else:
            if not isinstance(reason, str) or not reason:
                raise ValueError(f"invalid episode {episode_id} needs invalid_reason")
            invalid_ids.append(episode_id)
            invalid_reasons[episode_id] = reason

    return {
        "attempted_count": len(episodes),
        "valid_episode_count": len(episodes) - len(invalid_ids),
        "terminated_episode_count": terminated_count,
        "truncated_episode_count": truncated_count,
        "invalid_episode_count": len(invalid_ids),
        "invalid_episode_ids": invalid_ids,
        "invalid_reasons": invalid_reasons,
    }


def evaluate_protocol(name: str, episodes: Sequence[dict[str, object]] = EPISODES) -> dict[str, object]:
    protocol = PROTOCOLS[name]
    selected = []
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            raise ValueError(f"episode {index} must be a mapping")
        suite = episode.get("suite")
        if not isinstance(suite, str) or not suite:
            raise ValueError(f"episode {index} needs a non-empty suite")
        if suite in protocol["suites"]:
            selected.append(episode)
    audit = audit_episode_rows(selected)
    if audit["invalid_episode_count"]:
        invalid_ids = ", ".join(audit["invalid_episode_ids"])
        raise ValueError(f"protocol {name} contains invalid attempts: {invalid_ids}")

    def success(episode: dict[str, object]) -> bool:
        if not episode["goal"]:
            return False
        return not protocol["safety_aware"] or not (episode["collision"] or episode["intervention"])

    count = audit["valid_episode_count"]
    success_count = sum(success(episode) for episode in selected)
    return {
        **audit,
        "episode_count": count,
        "denominator_policy": "all valid selected attempts; valid truncations remain failures unless success was reached",
        "success_count": success_count,
        "success_rate": success_count / count,
        "success_wilson_95": wilson_interval(success_count, count),
        "collision_rate": sum(episode["collision"] for episode in selected) / count,
        "intervention_rate": sum(episode["intervention"] for episode in selected) / count,
        "mean_route_completion": sum(episode["route"] for episode in selected) / count,
    }


def comparability_warnings(left: str, right: str) -> list[str]:
    first, second = PROTOCOLS[left], PROTOCOLS[right]
    warnings = []
    if first["suites"] != second["suites"]:
        warnings.append("task_population_differs")
    if first["safety_aware"] != second["safety_aware"]:
        warnings.append("success_definition_differs")
    if evaluate_protocol(left)["episode_count"] != evaluate_protocol(right)["episode_count"]:
        warnings.append("denominator_differs")
    return warnings


def factorial_protocol_effects() -> dict[str, float]:
    """Expose population/success-rule effects without pretending they are additive."""
    easy_goal = evaluate_protocol("easy_goal_only")["success_rate"]
    easy_safe = evaluate_protocol("easy_safety_aware")["success_rate"]
    full_goal = evaluate_protocol("full_goal_only")["success_rate"]
    full_safe = evaluate_protocol("full_safety_aware")["success_rate"]
    return {
        "population_effect_under_goal_only": full_goal - easy_goal,
        "population_effect_under_safety_aware": full_safe - easy_safe,
        "safety_rule_effect_on_easy": easy_safe - easy_goal,
        "safety_rule_effect_on_full": full_safe - full_goal,
        "interaction": (full_safe - full_goal) - (easy_safe - easy_goal),
    }


def evaluate() -> dict[str, object]:
    left, right = "easy_goal_only", "full_safety_aware"
    metrics = {name: evaluate_protocol(name) for name in PROTOCOLS}
    metrics["comparability_warnings"] = comparability_warnings(left, right)
    metrics["factorial_protocol_effects"] = factorial_protocol_effects()
    metrics["paired_cluster_comparison"] = exact_paired_cluster_bootstrap()
    return metrics
