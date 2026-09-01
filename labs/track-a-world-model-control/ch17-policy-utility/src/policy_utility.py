"""Decision-utility and model-exploitation fixture for Chapter 17."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt


GOAL_POSITION = 4
STEP_COST = -0.05


@dataclass(frozen=True)
class State:
    position: int = 0
    terminal: str = "running"

    def __post_init__(self) -> None:
        if isinstance(self.position, bool) or not isinstance(self.position, int):
            raise ValueError("position must be an integer")
        if not 0 <= self.position <= GOAL_POSITION:
            raise ValueError("position is outside the corridor")
        if self.terminal not in {"running", "goal", "collision"}:
            raise ValueError("unknown terminal state")
        if self.terminal == "goal" and self.position != GOAL_POSITION:
            raise ValueError("goal terminal requires the goal position")
        if self.terminal == "running" and self.position == GOAL_POSITION:
            raise ValueError("goal position cannot remain running")


POLICIES = {
    "safe_route": ("advance",) * GOAL_POSITION,
    "phantom_shortcut": ("shortcut",),
    "idle": ("wait",) * GOAL_POSITION,
}

# Observed state-action support for the didactic learned model. The shortcut is
# deliberately outside support even though the model returns a confident future.
SUPPORTED_STATE_ACTIONS = frozenset(
    (position, action)
    for position in range(GOAL_POSITION)
    for action in ("advance", "wait")
)
SUPPORT_WITH_SHORTCUT = SUPPORTED_STATE_ACTIONS | {(0, "shortcut")}
ATTRIBUTION_FAULTS = (
    "action_grounding",
    "transition_model",
    "state_decoder",
    "outcome_scorer",
)
DECISION_FAULTS = ("critical_shortcut", "unvisited_wait")


def transition(state: State, action: str, learned: bool) -> tuple[State, float]:
    if not isinstance(learned, bool):
        raise ValueError("learned must be a boolean")
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


def transition_with_fault(state: State, action: str, fault: str) -> tuple[State, float]:
    """Inject one of two equally frequent transition faults at different queries."""
    if fault not in DECISION_FAULTS:
        raise ValueError("unknown decision-utility fault")
    true_next = transition(state, action, learned=False)
    if fault == "critical_shortcut" and state.position == 0 and action == "shortcut":
        return State(GOAL_POSITION, "goal"), 1.0
    if fault == "unvisited_wait" and state.position == 3 and action == "wait":
        return State(GOAL_POSITION, "goal"), 1.0
    return true_next


def rollout_with_fault(actions: tuple[str, ...], fault: str) -> dict[str, object]:
    state = State()
    total_return = 0.0
    executed_actions = []
    for action in actions:
        state, reward = transition_with_fault(state, action, fault)
        total_return += reward
        executed_actions.append(action)
        if state.terminal != "running":
            break
    return {
        "return": round(total_return, 12),
        "terminal": state.terminal,
        "executed_steps": len(executed_actions),
    }


def policy_returns(learned: bool) -> dict[str, float]:
    return {name: float(rollout(actions, learned)["return"]) for name, actions in POLICIES.items()}


def descending_ranks(scores: dict[str, float]) -> dict[str, float]:
    """Return average descending ranks so Spearman remains valid with ties."""
    if len(scores) < 2 or any(not isinstance(name, str) or not name for name in scores):
        raise ValueError("scores must contain two or more named policies")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
        for value in scores.values()
    ):
        raise ValueError("scores must be finite numbers")
    ordered = sorted(scores, key=lambda name: (-scores[name], name))
    ranks: dict[str, float] = {}
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and scores[ordered[end]] == scores[ordered[start]]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0
        for name in ordered[start:end]:
            ranks[name] = average_rank
        start = end
    return ranks


def spearman_rank_correlation(first: dict[str, float], second: dict[str, float]) -> float:
    if first.keys() != second.keys() or len(first) < 2:
        raise ValueError("score tables must contain the same two or more policies")
    first_ranks = descending_ranks(first)
    second_ranks = descending_ranks(second)
    first_mean = sum(first_ranks.values()) / len(first_ranks)
    second_mean = sum(second_ranks.values()) / len(second_ranks)
    covariance = sum(
        (first_ranks[name] - first_mean) * (second_ranks[name] - second_mean)
        for name in first
    )
    first_scale = sqrt(sum((rank - first_mean) ** 2 for rank in first_ranks.values()))
    second_scale = sqrt(sum((rank - second_mean) ** 2 for rank in second_ranks.values()))
    if first_scale == 0.0 or second_scale == 0.0:
        raise ValueError("Spearman correlation is undefined for a constant ranking")
    return covariance / (first_scale * second_scale)


def _validate_support(supported_state_actions: frozenset[tuple[int, str]]) -> None:
    if not isinstance(supported_state_actions, frozenset) or any(
        not isinstance(item, tuple)
        or len(item) != 2
        or isinstance(item[0], bool)
        or not isinstance(item[0], int)
        or not 0 <= item[0] < GOAL_POSITION
        or item[1] not in {"advance", "wait", "shortcut"}
        for item in supported_state_actions
    ):
        raise ValueError("support must be a frozenset of valid running state-action pairs")


def support_issues(
    actions: tuple[str, ...],
    supported_state_actions: frozenset[tuple[int, str]] = SUPPORTED_STATE_ACTIONS,
) -> tuple[dict[str, object], ...]:
    """Find state-action queries outside the learned model's observed support."""
    _validate_support(supported_state_actions)
    state = State()
    issues = []
    for step, action in enumerate(actions):
        if (state.position, action) not in supported_state_actions:
            issues.append({"step": step, "position": state.position, "action": action})
            break
        state, _ = transition(state, action, learned=True)
        if state.terminal != "running":
            break
    return tuple(issues)


def support_gated_selection(
    supported_state_actions: frozenset[tuple[int, str]] = SUPPORTED_STATE_ACTIONS,
) -> dict[str, object]:
    """Select only among policies whose learned rollouts stay in observed support."""
    _validate_support(supported_state_actions)
    accepted_returns = {}
    rejected = {}
    for name, actions in POLICIES.items():
        issues = support_issues(actions, supported_state_actions)
        if issues:
            rejected[name] = issues
        else:
            accepted_returns[name] = float(rollout(actions, learned=True)["return"])
    if not accepted_returns:
        raise ValueError("support gate rejected every policy")
    selected = max(accepted_returns, key=accepted_returns.get)  # type: ignore[arg-type]
    true_returns = policy_returns(learned=False)
    true_best = max(true_returns, key=true_returns.get)  # type: ignore[arg-type]
    return {
        "accepted_policy_count": len(accepted_returns),
        "rejected_policy_count": len(rejected),
        "rejected_policies": rejected,
        "selected_policy": selected,
        "selected_policy_true_terminal": rollout(POLICIES[selected], learned=False)["terminal"],
        "model_exploitation_regret": true_returns[true_best] - true_returns[selected],
    }


def support_gate_audit() -> dict[str, object]:
    """Contrast an out-of-support error with the same error declared in support."""

    return {
        "out_of_support_error": support_gated_selection(SUPPORTED_STATE_ACTIONS),
        "in_support_model_error": support_gated_selection(SUPPORT_WITH_SHORTCUT),
        "scope": "same deterministic model error under two authored support declarations",
    }


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


def decision_fault_allocation_audit() -> dict[str, object]:
    """Hold uniform transition accuracy fixed while moving the sole model error."""
    cases = [
        (State(position), action)
        for position in range(GOAL_POSITION)
        for action in ("advance", "wait")
    ]
    cases.append((State(), "shortcut"))
    candidate_queries = []
    for actions in POLICIES.values():
        state = State()
        for action in actions:
            candidate_queries.append((state.position, action))
            state, _ = transition(state, action, learned=False)
            if state.terminal != "running":
                break

    true_returns = policy_returns(learned=False)
    true_best = max(true_returns, key=true_returns.get)  # type: ignore[arg-type]
    scenarios = {}
    for fault in DECISION_FAULTS:
        mismatches = [
            {"position": state.position, "action": action}
            for state, action in cases
            if transition_with_fault(state, action, fault)
            != transition(state, action, learned=False)
        ]
        model_returns = {
            name: float(rollout_with_fault(actions, fault)["return"])
            for name, actions in POLICIES.items()
        }
        selected = max(model_returns, key=model_returns.get)  # type: ignore[arg-type]
        mismatch_query = (mismatches[0]["position"], mismatches[0]["action"])
        scenarios[fault] = {
            "uniform_transition_accuracy": (len(cases) - len(mismatches)) / len(cases),
            "mismatches": mismatches,
            "candidate_panel_visit_count": candidate_queries.count(mismatch_query),
            "model_returns": model_returns,
            "selected_policy": selected,
            "selected_policy_true_terminal": rollout(POLICIES[selected], learned=False)["terminal"],
            "model_exploitation_regret": round(true_returns[true_best] - true_returns[selected], 12),
        }
    return {
        "case_count": len(cases),
        "scenarios": scenarios,
        "equal_uniform_accuracy": (
            scenarios["critical_shortcut"]["uniform_transition_accuracy"]
            == scenarios["unvisited_wait"]["uniform_transition_accuracy"]
        ),
        "scope": "two single-fault authored models on one fixed candidate-policy panel",
    }


def proxy_evaluation_scenario(fault_component: str | None = None) -> dict[str, object]:
    """Run a four-component proxy evaluator with at most one named injected fault."""

    if fault_component is not None and fault_component not in ATTRIBUTION_FAULTS:
        raise ValueError("unknown proxy-evaluation fault component")

    proxy_scores: dict[str, float] = {}
    traces: dict[str, dict[str, object]] = {}
    for policy_name, commanded_actions in POLICIES.items():
        grounded_actions = commanded_actions
        if fault_component == "action_grounding" and policy_name == "safe_route":
            grounded_actions = ("shortcut",)

        predicted = rollout(
            grounded_actions,
            learned=fault_component == "transition_model",
        )
        decoded_terminal = str(predicted["terminal"])
        if (
            fault_component == "state_decoder"
            and policy_name == "phantom_shortcut"
            and decoded_terminal == "collision"
        ):
            decoded_terminal = "goal"

        executed_steps = int(predicted["executed_steps"])
        if fault_component == "outcome_scorer" and policy_name == "phantom_shortcut":
            score = 1.0
        elif decoded_terminal == "goal":
            score = 1.0 + STEP_COST * (executed_steps - 1)
        elif decoded_terminal == "collision":
            score = -1.0
        else:
            score = float(predicted["return"])
        proxy_scores[policy_name] = round(score, 12)
        traces[policy_name] = {
            "commanded_actions": commanded_actions,
            "grounded_actions": grounded_actions,
            "predicted_terminal": predicted["terminal"],
            "decoded_terminal": decoded_terminal,
            "proxy_score": proxy_scores[policy_name],
        }

    selected = max(proxy_scores, key=proxy_scores.get)  # type: ignore[arg-type]
    true_returns = policy_returns(learned=False)
    true_best = max(true_returns, key=true_returns.get)  # type: ignore[arg-type]
    return {
        "fault_component": fault_component or "none",
        "proxy_scores": proxy_scores,
        "selected_policy": selected,
        "selected_policy_true_terminal": rollout(POLICIES[selected], learned=False)["terminal"],
        "model_exploitation_regret": round(true_returns[true_best] - true_returns[selected], 12),
        "spearman_rank_correlation": round(
            spearman_rank_correlation(true_returns, proxy_scores),
            12,
        ),
        "policy_traces": traces,
    }


def component_attribution_audit() -> dict[str, object]:
    """Expose component faults that are distinguishable only with intermediate traces."""

    detailed_scenarios = {
        "oracle": proxy_evaluation_scenario(),
        **{fault: proxy_evaluation_scenario(fault) for fault in ATTRIBUTION_FAULTS},
    }
    equivalent_faults = ("transition_model", "state_decoder", "outcome_scorer")
    reference_scores = detailed_scenarios[equivalent_faults[0]]["proxy_scores"]
    scenarios = {
        name: {
            "selected_policy": scenario["selected_policy"],
            "selected_policy_true_terminal": scenario["selected_policy_true_terminal"],
            "model_exploitation_regret": scenario["model_exploitation_regret"],
            "spearman_rank_correlation": scenario["spearman_rank_correlation"],
            "proxy_scores": scenario["proxy_scores"],
        }
        for name, scenario in detailed_scenarios.items()
    }
    return {
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "observationally_equivalent_failure_group": list(equivalent_faults),
        "equivalent_end_to_end_scores": all(
            detailed_scenarios[fault]["proxy_scores"] == reference_scores
            for fault in equivalent_faults[1:]
        ),
        "phantom_shortcut_localization_traces": {
            fault: detailed_scenarios[fault]["policy_traces"]["phantom_shortcut"]
            for fault in equivalent_faults
        },
        "scope": "single-fault deterministic component ledger; intermediate traces localize faults but do not estimate field rates",
    }


def prospective_policy_ranking_audit(
    calibration_policies: tuple[str, ...] = ("safe_route", "idle"),
    held_out_policies: tuple[str, ...] = ("phantom_shortcut",),
) -> dict[str, object]:
    """Freeze a retrospective policy panel before adding held-out candidates."""

    for name, panel in (
        ("calibration", calibration_policies),
        ("held_out", held_out_policies),
    ):
        if not isinstance(panel, tuple) or not panel:
            raise ValueError(f"{name} policies must be a non-empty tuple")
        if len(panel) != len(set(panel)):
            raise ValueError(f"{name} policies must not contain duplicates")
        if any(policy not in POLICIES for policy in panel):
            raise ValueError(f"{name} policies contain an unknown policy")
    if set(calibration_policies) & set(held_out_policies):
        raise ValueError("calibration and held-out policies must be disjoint")

    true_returns = policy_returns(learned=False)
    model_returns = policy_returns(learned=True)
    calibration_true = {name: true_returns[name] for name in calibration_policies}
    calibration_model = {name: model_returns[name] for name in calibration_policies}
    prospective_names = calibration_policies + held_out_policies
    prospective_true = {name: true_returns[name] for name in prospective_names}
    prospective_model = {name: model_returns[name] for name in prospective_names}
    selected = max(prospective_model, key=prospective_model.get)  # type: ignore[arg-type]
    true_best = max(prospective_true, key=prospective_true.get)  # type: ignore[arg-type]

    return {
        "calibration_policy_count": len(calibration_policies),
        "held_out_policy_count": len(held_out_policies),
        "calibration_policies": list(calibration_policies),
        "held_out_policies": list(held_out_policies),
        "calibration_spearman": round(
            spearman_rank_correlation(calibration_true, calibration_model),
            12,
        ),
        "calibration_maximum_absolute_return_gap": max(
            abs(calibration_model[name] - calibration_true[name])
            for name in calibration_policies
        ),
        "prospective_spearman": round(
            spearman_rank_correlation(prospective_true, prospective_model),
            12,
        ),
        "prospective_selected_policy": selected,
        "prospective_selected_policy_true_terminal": rollout(
            POLICIES[selected],
            learned=False,
        )["terminal"],
        "prospective_model_exploitation_regret": round(
            prospective_true[true_best] - prospective_true[selected],
            12,
        ),
        "held_out_return_gaps": {
            name: round(model_returns[name] - true_returns[name], 12)
            for name in held_out_policies
        },
        "scope": "model frozen before a disjoint authored policy is added; not learned-policy generalization",
    }


def evaluate() -> dict[str, object]:
    true_returns = policy_returns(learned=False)
    model_returns = policy_returns(learned=True)
    model_selected = max(model_returns, key=model_returns.get)  # type: ignore[arg-type]
    true_best = max(true_returns, key=true_returns.get)  # type: ignore[arg-type]
    absolute_gaps = {name: abs(model_returns[name] - true_returns[name]) for name in POLICIES}
    agreement = transition_agreement()
    selected_action = POLICIES[model_selected][0]
    gate_audit = support_gate_audit()
    return {
        "true_returns": true_returns,
        "learned_model_returns": model_returns,
        "true_best_policy": true_best,
        "learned_model_selected_policy": model_selected,
        "selected_policy_true_terminal": rollout(POLICIES[model_selected], learned=False)["terminal"],
        "policy_ranking_matches": descending_ranks(true_returns) == descending_ranks(model_returns),
        "spearman_rank_correlation": round(spearman_rank_correlation(true_returns, model_returns), 12),
        "mean_absolute_return_gap": sum(absolute_gaps.values()) / len(absolute_gaps),
        "maximum_absolute_return_gap": max(absolute_gaps.values()),
        "model_exploitation_regret": true_returns[true_best] - true_returns[model_selected],
        "model_selected_first_transition_matches": (
            transition(State(), selected_action, learned=False)
            == transition(State(), selected_action, learned=True)
        ),
        "support_gate_audit": gate_audit,
        "transition_agreement": agreement,
        "component_attribution_audit": component_attribution_audit(),
        "prospective_policy_ranking_audit": prospective_policy_ranking_audit(),
        "decision_fault_allocation_audit": decision_fault_allocation_audit(),
    }
