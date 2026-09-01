"""Validation for the Chapter 2 four-axis system-card fixture."""

from __future__ import annotations

import json
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


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture(fixture: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(fixture, dict):
        return ["fixture must be an object"]
    if fixture.get("fixture_version") != 2:
        errors.append("fixture_version must be 2")
    if fixture.get("audit_date") != "2026-09-01":
        errors.append("audit_date must match the reviewed source snapshot")
    if not isinstance(fixture.get("scope"), str) or not fixture["scope"].strip():
        errors.append("scope must be a non-empty string")
    cards = fixture.get("cards")
    if not isinstance(cards, list):
        return ["cards must be a list"]
    if len(cards) != 8:
        errors.append(f"expected 8 cards, found {len(cards)}")

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


def summarize(fixture: dict[str, Any]) -> dict[str, int]:
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
    }
