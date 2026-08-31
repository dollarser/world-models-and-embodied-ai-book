"""A fixed episode table for exposing evaluation-protocol drift."""

from __future__ import annotations


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


def evaluate_protocol(name: str) -> dict[str, float]:
    protocol = PROTOCOLS[name]
    selected = [episode for episode in EPISODES if episode["suite"] in protocol["suites"]]

    def success(episode: dict[str, object]) -> bool:
        if not episode["goal"]:
            return False
        return not protocol["safety_aware"] or not (episode["collision"] or episode["intervention"])

    count = len(selected)
    return {
        "episode_count": count,
        "success_rate": sum(success(episode) for episode in selected) / count,
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
