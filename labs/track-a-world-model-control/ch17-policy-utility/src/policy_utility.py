"""Decision-utility and model-exploitation fixture for Chapter 17."""

from __future__ import annotations

from dataclasses import dataclass


GOAL_POSITION = 4
STEP_COST = -0.05


@dataclass(frozen=True)
class State:
    position: int = 0
    terminal: str = "running"


POLICIES = {
    "safe_route": ("advance",) * GOAL_POSITION,
    "phantom_shortcut": ("shortcut",),
    "idle": ("wait",) * GOAL_POSITION,
}


def transition(state: State, action: str, learned: bool) -> tuple[State, float]:
    if state.terminal != "running":
        raise ValueError("cannot transition a terminal state")
    if action == "wait":
        return state, STEP_COST
    if action == "advance":
        next_position = state.position + 1
        if next_position >= GOAL_POSITION:
            return State(GOAL_POSITION, "goal"), 1.0
        return State(next_position), STEP_COST
    if action == "shortcut":
        if learned and state.position == 0:
            return State(GOAL_POSITION, "goal"), 1.0
        return State(state.position, "collision"), -1.0
    raise ValueError(f"unknown action: {action}")


def rollout(actions: tuple[str, ...], learned: bool) -> dict[str, object]:
    state = State()
    total_return = 0.0
    executed_actions = []
    for action in actions:
        state, reward = transition(state, action, learned=learned)
        total_return += reward
        executed_actions.append(action)
        if state.terminal != "running":
            break
    return {
        "return": round(total_return, 12),
        "final_position": state.position,
        "terminal": state.terminal,
        "executed_steps": len(executed_actions),
    }


def policy_returns(learned: bool) -> dict[str, float]:
    return {name: float(rollout(actions, learned)["return"]) for name, actions in POLICIES.items()}


def descending_ranks(scores: dict[str, float]) -> dict[str, int]:
    ordered = sorted(scores, key=lambda name: (-scores[name], name))
    return {name: index + 1 for index, name in enumerate(ordered)}


def spearman_rank_correlation(first: dict[str, float], second: dict[str, float]) -> float:
    if first.keys() != second.keys() or len(first) < 2:
        raise ValueError("score tables must contain the same two or more policies")
    first_ranks = descending_ranks(first)
    second_ranks = descending_ranks(second)
    count = len(first)
    squared_difference = sum((first_ranks[name] - second_ranks[name]) ** 2 for name in first)
    return 1.0 - 6.0 * squared_difference / (count * (count * count - 1))


def transition_agreement() -> dict[str, object]:
    cases = [(State(position), action) for position in range(GOAL_POSITION) for action in ("advance", "wait")]
    cases.append((State(), "shortcut"))
    matching = 0
    mismatches = []
    for state, action in cases:
        true_next = transition(state, action, learned=False)
        model_next = transition(state, action, learned=True)
        if true_next == model_next:
            matching += 1
        else:
            mismatches.append({"position": state.position, "action": action})
    return {
        "case_count": len(cases),
        "matching_count": matching,
        "accuracy": matching / len(cases),
        "mismatches": mismatches,
    }


def evaluate() -> dict[str, object]:
    true_returns = policy_returns(learned=False)
    model_returns = policy_returns(learned=True)
    model_selected = max(model_returns, key=model_returns.get)  # type: ignore[arg-type]
    true_best = max(true_returns, key=true_returns.get)  # type: ignore[arg-type]
    absolute_gaps = {name: abs(model_returns[name] - true_returns[name]) for name in POLICIES}
    agreement = transition_agreement()
    return {
        "true_returns": true_returns,
        "learned_model_returns": model_returns,
        "true_best_policy": true_best,
        "learned_model_selected_policy": model_selected,
        "selected_policy_true_terminal": rollout(POLICIES[model_selected], learned=False)["terminal"],
        "policy_ranking_matches": descending_ranks(true_returns) == descending_ranks(model_returns),
        "spearman_rank_correlation": spearman_rank_correlation(true_returns, model_returns),
        "mean_absolute_return_gap": sum(absolute_gaps.values()) / len(absolute_gaps),
        "maximum_absolute_return_gap": max(absolute_gaps.values()),
        "model_exploitation_regret": true_returns[true_best] - true_returns[model_selected],
        "transition_agreement": agreement,
    }
