"""Validation for the Chapter 2 four-axis system-card fixture."""

from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any


EXPECTED_CATEGORIES = {
    "no_action_video_predictor",
    "action_conditioned_predictor",
    "latent_world_model",
    "value_equivalent_model",
    "vla_policy",
    "physical_simulator",
    "digital_twin",
    "automatic_driving_case",
}

REQUIRED_CARD_FIELDS = {
    "id",
    "name",
    "category",
    "evidence",
    "axes",
    "action_conditioning",
    "learned_dynamics",
    "relation",
    "claim_status",
    "unsupported_claims",
}
REQUIRED_AXES = {"representation", "dynamics", "conditioning", "use"}
REQUIRED_CLAIM_STATUS = {
    "temporal_or_transition_model",
    "candidate_action_intervention",
    "learned_action_conditioned_transition",
    "policy_without_independent_transition",
}
CLAIM_STATUSES = {"supported", "unsupported", "scope_dependent"}


def analyze_state_aliasing(case: Any) -> dict[str, Any]:
    """Compare a current-observation policy with a history-disambiguated policy.

    Contexts are treated as equally likely. Each context must expose the same
    action set and have a unique best action. This is a finite teaching
    counterexample, not a POMDP solver or a learned representation benchmark.
    """

    if not isinstance(case, dict):
        raise ValueError("state_aliasing_case must be an object")
    if not isinstance(case.get("current_observation"), str) or not case["current_observation"].strip():
        raise ValueError("current_observation must be a non-empty string")
    contexts = case.get("contexts")
    if not isinstance(contexts, list) or len(contexts) < 2:
        raise ValueError("contexts must contain at least two entries")

    context_ids: set[str] = set()
    history_cues: set[str] = set()
    action_names: set[str] | None = None
    normalized: list[dict[str, Any]] = []
    for index, context in enumerate(contexts):
        if not isinstance(context, dict):
            raise ValueError(f"contexts[{index}] must be an object")
        context_id = context.get("id")
        history_cue = context.get("history_cue")
        returns = context.get("action_returns")
        if not isinstance(context_id, str) or not context_id.strip() or context_id in context_ids:
            raise ValueError("context ids must be unique non-empty strings")
        if not isinstance(history_cue, str) or not history_cue.strip() or history_cue in history_cues:
            raise ValueError("history cues must be unique non-empty strings")
        if not isinstance(returns, dict) or len(returns) < 2:
            raise ValueError("each context must define at least two action returns")
        if any(not isinstance(action, str) or not action.strip() for action in returns):
            raise ValueError("action names must be non-empty strings")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
            for value in returns.values()
        ):
            raise ValueError("action returns must be finite numbers")
        current_actions = set(returns)
        if action_names is None:
            action_names = current_actions
        elif current_actions != action_names:
            raise ValueError("all contexts must define the same action set")
        best_return = max(float(value) for value in returns.values())
        best_actions = [action for action, value in returns.items() if float(value) == best_return]
        if len(best_actions) != 1:
            raise ValueError("each context must have a unique best action")
        context_ids.add(context_id)
        history_cues.add(history_cue)
        normalized.append(
            {
                "id": context_id,
                "history_cue": history_cue,
                "returns": {action: float(value) for action, value in returns.items()},
                "optimal_action": best_actions[0],
                "optimal_return": best_return,
            }
        )

    assert action_names is not None
    mean_return_by_action = {
        action: sum(context["returns"][action] for context in normalized) / len(normalized)
        for action in sorted(action_names)
    }
    best_aliased_return = max(mean_return_by_action.values())
    best_aliased_actions = [
        action for action, value in mean_return_by_action.items() if value == best_aliased_return
    ]
    if len(best_aliased_actions) != 1:
        raise ValueError("aliased policy must have a unique best shared action")
    aliased_action = best_aliased_actions[0]
    aliased_mean_return = mean_return_by_action[aliased_action]
    oracle_mean_return = sum(context["optimal_return"] for context in normalized) / len(normalized)
    return {
        "current_observation": case["current_observation"],
        "context_weighting": "uniform",
        "context_count": len(normalized),
        "action_count": len(action_names),
        "context_optimal_actions": {
            context["id"]: context["optimal_action"] for context in normalized
        },
        "context_optimal_actions_differ": len(
            {context["optimal_action"] for context in normalized}
        ) > 1,
        "mean_return_by_shared_action": {
            action: round(value, 12) for action, value in mean_return_by_action.items()
        },
        "aliased_selected_action": aliased_action,
        "aliased_mean_return": round(aliased_mean_return, 12),
        "aliased_mean_regret": round(oracle_mean_return - aliased_mean_return, 12),
        "history_aware_mean_return": round(oracle_mean_return, 12),
        "history_aware_mean_regret": 0.0,
        "history_value_gap": round(oracle_mean_return - aliased_mean_return, 12),
    }


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture(fixture: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(fixture, dict):
        return ["fixture must be an object"]
    if fixture.get("fixture_version") != 3:
        errors.append("fixture_version must be 3")
    if fixture.get("audit_date") != "2026-09-01":
        errors.append("audit_date must match the reviewed source snapshot")
    if not isinstance(fixture.get("scope"), str) or not fixture["scope"].strip():
        errors.append("scope must be a non-empty string")
    cards = fixture.get("cards")
    if not isinstance(cards, list):
        return ["cards must be a list"]
    if len(cards) != 8:
        errors.append(f"expected 8 cards, found {len(cards)}")
    try:
        aliasing = analyze_state_aliasing(fixture.get("state_aliasing_case"))
        if not aliasing["context_optimal_actions_differ"]:
            errors.append("state aliasing case must require different context-optimal actions")
    except ValueError as error:
        errors.append(str(error))

    identifiers: set[str] = set()
    categories: set[str] = set()
    for index, card in enumerate(cards):
        label = f"cards[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = REQUIRED_CARD_FIELDS - card.keys()
        if missing:
            errors.append(f"{label} missing fields: {sorted(missing)}")
            continue
        identifier = card["id"]
        category = card["category"]
        for field in ("id", "name", "category", "relation"):
            if not isinstance(card[field], str) or not card[field].strip():
                errors.append(f"{label} {field} must be a non-empty string")
        if isinstance(identifier, str):
            if identifier in identifiers:
                errors.append(f"duplicate card id: {identifier}")
            identifiers.add(identifier)
        if isinstance(category, str):
            categories.add(category)

        axes = card["axes"]
        if not isinstance(axes, dict) or set(axes) != REQUIRED_AXES:
            errors.append(f"{label} axes must be exactly {sorted(REQUIRED_AXES)}")
        elif any(not isinstance(value, str) or not value.strip() for value in axes.values()):
            errors.append(f"{label} axis values must be non-empty strings")
        evidence = card["evidence"]
        if not isinstance(evidence, dict) or not all(evidence.get(key) for key in ("source_type", "snapshot", "url")):
            errors.append(f"{label} evidence must include source_type, snapshot, and url")
        elif not all(isinstance(evidence[key], str) for key in ("source_type", "snapshot", "url")):
            errors.append(f"{label} evidence values must be strings")
        elif not evidence["url"].startswith("https://"):
            errors.append(f"{label} evidence url must use https")
        if not isinstance(card["unsupported_claims"], list) or not card["unsupported_claims"]:
            errors.append(f"{label} must record at least one unsupported claim")
        elif any(not isinstance(claim, str) or not claim for claim in card["unsupported_claims"]):
            errors.append(f"{label} unsupported claims must be non-empty strings")
        elif len(card["unsupported_claims"]) != len(set(card["unsupported_claims"])):
            errors.append(f"{label} unsupported claims must be unique")
        for field in ("action_conditioning", "learned_dynamics"):
            if card[field] is not None and not isinstance(card[field], bool):
                errors.append(f"{label} {field} must be boolean or null when scope-dependent")

        statuses = card["claim_status"]
        if not isinstance(statuses, dict) or set(statuses) != REQUIRED_CLAIM_STATUS:
            errors.append(f"{label} claim_status must be exactly {sorted(REQUIRED_CLAIM_STATUS)}")
        elif any(not isinstance(status, str) or status not in CLAIM_STATUSES for status in statuses.values()):
            errors.append(f"{label} claim_status values must use {sorted(CLAIM_STATUSES)}")
        else:
            if statuses["candidate_action_intervention"] == "supported" and card["action_conditioning"] is not True:
                errors.append(f"{label} action intervention requires explicit action conditioning")
            if statuses["learned_action_conditioned_transition"] == "supported" and not (
                card["action_conditioning"] is True and card["learned_dynamics"] is True
            ):
                errors.append(f"{label} learned action-conditioned transition requires both learned dynamics and action conditioning")
            if statuses["policy_without_independent_transition"] == "supported" and card["category"] != "vla_policy":
                errors.append(f"{label} policy-without-transition status is reserved for the VLA policy card")
            if card["category"] == "vla_policy" and statuses["temporal_or_transition_model"] != "unsupported":
                errors.append("VLA card must not infer an independent transition from action output")

    if categories != EXPECTED_CATEGORIES:
        errors.append(f"category coverage mismatch: {sorted(categories)}")

    by_category = {
        card["category"]: card
        for card in cards
        if isinstance(card, dict) and isinstance(card.get("category"), str)
    }
    if by_category.get("vla_policy", {}).get("relation") != "policy_not_automatically_world_model":
        errors.append("VLA card must not be classified as an automatic world model")
    if by_category.get("physical_simulator", {}).get("learned_dynamics") is not False:
        errors.append("physical simulator card must distinguish explicit from learned dynamics")
    if by_category.get("no_action_video_predictor", {}).get("action_conditioning") is not False:
        errors.append("no-action video predictor must not claim action conditioning")
    if by_category.get("digital_twin", {}).get("claim_status", {}).get("temporal_or_transition_model") != "scope_dependent":
        errors.append("digital twin transition evidence must remain scope-dependent")
    return errors


def summarize(fixture: dict[str, Any]) -> dict[str, Any]:
    cards = fixture["cards"]
    claim_count = lambda key, status: sum(card["claim_status"][key] == status for card in cards)
    return {
        "system_card_count": len(cards),
        "category_count": len({card["category"] for card in cards}),
        "cards_with_evidence": sum(bool(card["evidence"].get("url")) for card in cards),
        "cards_with_unsupported_claims": sum(bool(card["unsupported_claims"]) for card in cards),
        "cards_with_transition_evidence": claim_count("temporal_or_transition_model", "supported"),
        "cards_with_action_intervention": claim_count("candidate_action_intervention", "supported"),
        "learned_action_conditioned_candidates": claim_count("learned_action_conditioned_transition", "supported"),
        "scope_dependent_transition_cards": claim_count("temporal_or_transition_model", "scope_dependent"),
        "policy_without_transition_cards": claim_count("policy_without_independent_transition", "supported"),
        "state_aliasing": analyze_state_aliasing(fixture["state_aliasing_case"]),
    }
