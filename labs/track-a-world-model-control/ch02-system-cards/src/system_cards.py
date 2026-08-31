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
    "unsupported_claims",
}
REQUIRED_AXES = {"representation", "dynamics", "conditioning", "use"}


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
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
        if card["id"] in identifiers:
            errors.append(f"duplicate card id: {card['id']}")
        identifiers.add(card["id"])
        categories.add(card["category"])

        axes = card["axes"]
        if not isinstance(axes, dict) or set(axes) != REQUIRED_AXES:
            errors.append(f"{label} axes must be exactly {sorted(REQUIRED_AXES)}")
        evidence = card["evidence"]
        if not isinstance(evidence, dict) or not all(evidence.get(key) for key in ("source_type", "snapshot", "url")):
            errors.append(f"{label} evidence must include source_type, snapshot, and url")
        if not isinstance(card["unsupported_claims"], list) or not card["unsupported_claims"]:
            errors.append(f"{label} must record at least one unsupported claim")
        elif any(not isinstance(claim, str) or not claim for claim in card["unsupported_claims"]):
            errors.append(f"{label} unsupported claims must be non-empty strings")
        for field in ("action_conditioning", "learned_dynamics"):
            if card[field] is not None and not isinstance(card[field], bool):
                errors.append(f"{label} {field} must be boolean or null when scope-dependent")

    if categories != EXPECTED_CATEGORIES:
        errors.append(f"category coverage mismatch: {sorted(categories)}")

    by_category = {card["category"]: card for card in cards if isinstance(card, dict) and "category" in card}
    if by_category.get("vla_policy", {}).get("relation") != "policy_not_automatically_world_model":
        errors.append("VLA card must not be classified as an automatic world model")
    if by_category.get("physical_simulator", {}).get("learned_dynamics") is not False:
        errors.append("physical simulator card must distinguish explicit from learned dynamics")
    if by_category.get("no_action_video_predictor", {}).get("action_conditioning") is not False:
        errors.append("no-action video predictor must not claim action conditioning")
    return errors


def summarize(fixture: dict[str, Any]) -> dict[str, int]:
    cards = fixture["cards"]
    return {
        "system_card_count": len(cards),
        "category_count": len({card["category"] for card in cards}),
        "cards_with_evidence": sum(bool(card["evidence"].get("url")) for card in cards),
        "cards_with_unsupported_claims": sum(bool(card["unsupported_claims"]) for card in cards),
    }
