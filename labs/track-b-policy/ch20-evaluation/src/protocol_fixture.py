"""A fixed episode table for exposing evaluation-protocol drift."""

from __future__ import annotations

from math import isfinite, sqrt


EPISODES = (
    {"id": "easy-1", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0},
    {"id": "easy-2", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0},
    {"id": "easy-3", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0},
    {"id": "easy-4", "suite": "easy", "goal": True, "collision": False, "intervention": False, "route": 1.0},
    {"id": "hard-1", "suite": "hard", "goal": True, "collision": False, "intervention": False, "route": 1.0},
    {"id": "hard-2", "suite": "hard", "goal": False, "collision": False, "intervention": False, "route": 0.7},
    {"id": "hard-3", "suite": "hard", "goal": True, "collision": True, "intervention": False, "route": 1.0},
    {"id": "hard-4", "suite": "hard", "goal": True, "collision": False, "intervention": True, "route": 1.0},
)


PROTOCOLS = {
    "easy_goal_only": {"suites": ("easy",), "safety_aware": False},
    "full_safety_aware": {"suites": ("easy", "hard"), "safety_aware": True},
}


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


def evaluate_protocol(name: str) -> dict[str, object]:
    protocol = PROTOCOLS[name]
    selected = [episode for episode in EPISODES if episode["suite"] in protocol["suites"]]

    def success(episode: dict[str, object]) -> bool:
        if not episode["goal"]:
            return False
        return not protocol["safety_aware"] or not (episode["collision"] or episode["intervention"])

    count = len(selected)
    success_count = sum(success(episode) for episode in selected)
    return {
        "episode_count": count,
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


def evaluate() -> dict[str, object]:
    left, right = "easy_goal_only", "full_safety_aware"
    return {
        left: evaluate_protocol(left),
        right: evaluate_protocol(right),
        "comparability_warnings": comparability_warnings(left, right),
    }
