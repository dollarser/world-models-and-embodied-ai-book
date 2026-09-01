"""Finite-horizon planning and value-equivalence fixtures for Chapter 7."""

from __future__ import annotations

from itertools import product
from math import ceil, isfinite


ACTIONS = ("advance", "harvest")
TRUE_OBSERVATIONS = {0: "red-start", 1: "blue-middle", 2: "gold-goal"}
SURROGATE_OBSERVATIONS = {0: "latent-a", 1: "latent-b", 2: "latent-c"}
RISK_SCENARIO_RETURNS = {
    "steady": (0.6, 0.6, 0.6, 0.6, 0.6),
    "risky": (1.5, 1.5, 1.5, 1.5, -2.0),
}


def transition(state: int, action: str) -> tuple[int, float, bool]:
    if isinstance(state, bool) or not isinstance(state, int) or state not in (0, 1, 2):
        raise ValueError("state must be 0, 1, or 2")
    if action not in ACTIONS:
        raise ValueError(f"unknown action: {action}")
    if action == "harvest":
        return state, 1.0 if state == 2 else 0.0, True
    return min(state + 1, 2), -0.1, False


def rollout(state: int, actions: tuple[str, ...], terminal_values: dict[int, float] | None = None) -> dict[str, object]:
    if not actions:
        raise ValueError("at least one action is required")
    if terminal_values is not None and (
        any(key not in terminal_values for key in (0, 1, 2))
        or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
            for value in terminal_values.values()
        )
    ):
        raise ValueError("terminal values must cover all states with finite numbers")
    current = state
    environment_return = 0.0
    executed = []
    terminated = False
    for action in actions:
        current, reward, terminated = transition(current, action)
        environment_return += reward
        executed.append(action)
        if terminated:
            break
    terminal_value_contribution = 0.0 if terminated or terminal_values is None else terminal_values[current]
    objective_return = environment_return + terminal_value_contribution
    return {
        "return": round(objective_return, 12),
        "environment_return": round(environment_return, 12),
        "terminal_value_contribution": round(terminal_value_contribution, 12),
        "final_state": current,
        "terminated": terminated,
        "executed_actions": tuple(executed),
    }


def plan(state: int, horizon: int, terminal_values: dict[int, float] | None = None) -> dict[str, object]:
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    candidates = tuple(product(ACTIONS, repeat=horizon))
    scored = [(rollout(state, actions, terminal_values)["return"], actions) for actions in candidates]
    best_return, best_actions = max(scored, key=lambda item: (item[0], tuple(-ACTIONS.index(a) for a in item[1])))
    return {"actions": best_actions, "predicted_return": best_return, "candidate_count": len(candidates)}


def execute_with_disturbance(
    replan: bool,
    post_disturbance_budget: int | None = None,
    terminal_values: dict[int, float] | None = None,
) -> dict[str, object]:
    if not isinstance(replan, bool):
        raise ValueError("replan must be a boolean")
    if post_disturbance_budget is not None and (
        isinstance(post_disturbance_budget, bool)
        or not isinstance(post_disturbance_budget, int)
        or post_disturbance_budget <= 0
    ):
        raise ValueError("post-disturbance budget must be a positive integer or None")
    if terminal_values is not None and post_disturbance_budget is None:
        raise ValueError("terminal values require an explicit post-disturbance budget")
    state = 0
    initial = plan(state, 3)["actions"]
    state, reward, _ = transition(state, initial[0])
    state = 0  # a fixed external disturbance after the first action
    if post_disturbance_budget is None:
        remaining = plan(state, 3)["actions"] if replan else initial[1:]
        available_budget = len(remaining)
    else:
        stale_suffix = initial[1:]
        if post_disturbance_budget > len(stale_suffix):
            raise ValueError("fixed budget cannot exceed the stale suffix length")
        remaining = (
            plan(state, post_disturbance_budget, terminal_values)["actions"]
            if replan
            else stale_suffix[:post_disturbance_budget]
        )
        available_budget = post_disturbance_budget
    result = rollout(state, remaining, terminal_values)
    environment_return = reward + result["environment_return"]
    objective_return = environment_return + result["terminal_value_contribution"]
    return {
        "return": round(objective_return, 12),
        "environment_return": round(environment_return, 12),
        "terminal_value_contribution": result["terminal_value_contribution"],
        "final_state": result["final_state"],
        "terminated": result["terminated"],
        "post_disturbance_actions": remaining,
        "post_disturbance_executed_actions": result["executed_actions"],
        "post_disturbance_action_budget": available_budget,
    }


def bellman_backup(state: int, values: dict[int, float]) -> float:
    if any(key not in values for key in (0, 1, 2)) or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
        for value in values.values()
    ):
        raise ValueError("values must cover all states with finite numbers")
    candidates = []
    for action in ACTIONS:
        next_state, reward, terminated = transition(state, action)
        candidates.append(reward if terminated else reward + values[next_state])
    return max(candidates)


def empirical_lower_tail_mean(values: tuple[float, ...], tail_fraction: float) -> float:
    """Average the lowest-return empirical tail; higher values are preferred."""

    if not values or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
        for value in values
    ):
        raise ValueError("values must be a non-empty tuple of finite numbers")
    if (
        isinstance(tail_fraction, bool)
        or not isinstance(tail_fraction, (int, float))
        or not isfinite(tail_fraction)
        or not 0.0 < tail_fraction <= 1.0
    ):
        raise ValueError("tail_fraction must be finite and in (0, 1]")
    tail_count = ceil(len(values) * tail_fraction)
    return round(sum(sorted(values)[:tail_count]) / tail_count, 12)


def evaluate_risk_objectives() -> dict[str, object]:
    """Compare expected return, lower-tail return, and a fixed chance constraint."""

    tail_fraction = 0.2
    failure_threshold = 0.0
    maximum_failure_probability = 0.1
    summaries = {}
    for action, outcomes in RISK_SCENARIO_RETURNS.items():
        summaries[action] = {
            "scenario_count": len(outcomes),
            "mean_return": round(sum(outcomes) / len(outcomes), 12),
            "worst_20_percent_return": empirical_lower_tail_mean(outcomes, tail_fraction),
            "failure_probability": sum(value < failure_threshold for value in outcomes) / len(outcomes),
        }
    mean_selected = max(summaries, key=lambda action: summaries[action]["mean_return"])
    tail_selected = max(summaries, key=lambda action: summaries[action]["worst_20_percent_return"])
    chance_feasible = [
        action
        for action, summary in summaries.items()
        if summary["failure_probability"] <= maximum_failure_probability
    ]
    return {
        "actions": summaries,
        "mean_selected_action": mean_selected,
        "worst_20_percent_selected_action": tail_selected,
        "chance_constraint_max_failure_probability": maximum_failure_probability,
        "chance_feasible_actions": sorted(chance_feasible),
        "scenario_semantics": "five equally weighted fixed return outcomes per action",
    }


def evaluate() -> dict[str, object]:
    short = plan(0, 1)
    long = plan(0, 3)
    terminal_values = {0: 0.8, 1: 0.9, 2: 1.0}
    value_bootstrapped = plan(0, 1, terminal_values)
    values = {0: 0.8, 1: 0.9, 2: 1.0}
    true_backups = {state: bellman_backup(state, values) for state in TRUE_OBSERVATIONS}
    surrogate_backups = {state: bellman_backup(state, values) for state in SURROGATE_OBSERVATIONS}
    legacy_open_loop = execute_with_disturbance(False)
    legacy_replanning = execute_with_disturbance(True)
    fixed_reward_open_loop = execute_with_disturbance(False, 2)
    fixed_reward_replanning = execute_with_disturbance(True, 2)
    fixed_value_open_loop = execute_with_disturbance(False, 2, terminal_values)
    fixed_value_replanning = execute_with_disturbance(True, 2, terminal_values)
    return {
        "horizon_1": short,
        "horizon_3": long,
        "horizon_1_with_terminal_value": value_bootstrapped,
        "disturbance_protocol_audit": {
            "legacy_unequal_budget": {
                "open_loop": legacy_open_loop,
                "replanning": legacy_replanning,
                "post_disturbance_action_budget_equal": False,
                "reason": "post-disturbance action budgets differ",
            },
            "fixed_budget_reward_only": {
                "open_loop": fixed_reward_open_loop,
                "replanning": fixed_reward_replanning,
                "post_disturbance_action_budget_equal": True,
                "comparison_scope": "one deterministic disturbance fixture",
                "objective": "sum of observed environment rewards within two post-disturbance action slots",
            },
            "fixed_budget_with_terminal_value": {
                "open_loop": fixed_value_open_loop,
                "replanning": fixed_value_replanning,
                "post_disturbance_action_budget_equal": True,
                "comparison_scope": "one deterministic disturbance fixture with frozen terminal values",
                "objective": "environment return plus a frozen terminal value after two post-disturbance action slots",
            },
        },
        "value_equivalence_fixture": {
            "observation_match_rate": sum(
                TRUE_OBSERVATIONS[state] == SURROGATE_OBSERVATIONS[state] for state in TRUE_OBSERVATIONS
            ) / len(TRUE_OBSERVATIONS),
            "max_bellman_backup_gap": max(
                abs(true_backups[state] - surrogate_backups[state]) for state in true_backups
            ),
            "scope": "one fixed transition/reward model and one value function",
        },
        "risk_objective_fixture": evaluate_risk_objectives(),
    }
