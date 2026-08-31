"""Cross-embodiment action adapter fixture for Chapter 16."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


CanonicalAction = tuple[float, float]  # (delta_x_m, gripper_open_fraction)
RawAction = tuple[float, float]


@dataclass(frozen=True)
class EmbodimentAdapter:
    embodiment_id: str
    delta_x_unit: str
    delta_x_scale_to_m: float
    gripper_polarity: int

    def __post_init__(self) -> None:
        if not self.embodiment_id or not self.delta_x_unit:
            raise ValueError("embodiment_id and delta_x_unit must be explicit")
        if (
            isinstance(self.delta_x_scale_to_m, bool)
            or not isinstance(self.delta_x_scale_to_m, (int, float))
            or not isfinite(self.delta_x_scale_to_m)
            or self.delta_x_scale_to_m <= 0.0
        ):
            raise ValueError("delta_x_scale_to_m must be a finite positive number")
        if isinstance(self.gripper_polarity, bool) or self.gripper_polarity not in (-1, 1):
            raise ValueError("gripper_polarity must be -1 or 1")

    @staticmethod
    def _validated_action(action: tuple[float, float], name: str) -> tuple[float, float]:
        if not isinstance(action, tuple) or len(action) != 2:
            raise ValueError(f"{name} must be a two-value tuple")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in action):
            raise ValueError(f"{name} must contain finite numbers")
        return float(action[0]), float(action[1])

    def to_canonical(self, raw: RawAction) -> CanonicalAction:
        delta_x, gripper = self._validated_action(raw, "raw action")
        if not -1.0 <= gripper <= 1.0:
            raise ValueError("raw gripper value must be in [-1, 1]")
        open_fraction = (self.gripper_polarity * gripper + 1.0) / 2.0
        return (delta_x * self.delta_x_scale_to_m, open_fraction)

    def from_canonical(self, action: CanonicalAction) -> RawAction:
        delta_x_m, open_fraction = self._validated_action(action, "canonical action")
        if not 0.0 <= open_fraction <= 1.0:
            raise ValueError("canonical gripper fraction must be in [0, 1]")
        return (
            delta_x_m / self.delta_x_scale_to_m,
            self.gripper_polarity * (2.0 * open_fraction - 1.0),
        )


ADAPTERS = {
    "arm_a": EmbodimentAdapter("arm_a", "controller_delta", 0.1, 1),
    "arm_b": EmbodimentAdapter("arm_b", "centimeter", 0.01, -1),
}

TARGETS = {
    "forward_open": (0.02, 1.0),
    "back_close": (-0.01, 0.0),
}

RECORDS = (
    {"episode_id": "a-1", "task": "forward_open", "embodiment_id": "arm_a", "raw_action": (0.2, 1.0)},
    {"episode_id": "a-2", "task": "back_close", "embodiment_id": "arm_a", "raw_action": (-0.1, -1.0)},
    {"episode_id": "b-1", "task": "forward_open", "embodiment_id": "arm_b", "raw_action": (2.0, -1.0)},
    {"episode_id": "b-2", "task": "back_close", "embodiment_id": "arm_b", "raw_action": (-1.0, 1.0)},
)


def canonicalize(record: dict[str, object]) -> CanonicalAction:
    embodiment_id = record.get("embodiment_id")
    if embodiment_id not in ADAPTERS:
        raise ValueError("missing or unknown embodiment metadata")
    raw_action = record.get("raw_action")
    if not isinstance(raw_action, tuple) or len(raw_action) != 2:
        raise ValueError("invalid raw action")
    return ADAPTERS[embodiment_id].to_canonical(raw_action)


def mean_action(actions: tuple[RawAction, ...]) -> RawAction:
    if not actions:
        raise ValueError("at least one action is required")
    validated = tuple(EmbodimentAdapter._validated_action(action, "pooled action") for action in actions)
    return tuple(sum(action[index] for action in validated) / len(validated) for index in range(2))  # type: ignore[return-value]


def mean_absolute_error(first: CanonicalAction, second: CanonicalAction) -> float:
    first_ = EmbodimentAdapter._validated_action(first, "first action")
    second_ = EmbodimentAdapter._validated_action(second, "second action")
    return sum(abs(a - b) for a, b in zip(first_, second_)) / len(first_)


def naive_raw_pooling_error() -> float:
    """Pool incompatible raw fields, then incorrectly decode using arm_a metadata."""
    errors = []
    for task, target in TARGETS.items():
        raw_actions = tuple(record["raw_action"] for record in RECORDS if record["task"] == task)
        pooled_raw = mean_action(raw_actions)  # type: ignore[arg-type]
        decoded = ADAPTERS["arm_a"].to_canonical(pooled_raw)
        errors.append(mean_absolute_error(decoded, target))
    return sum(errors) / len(errors)


def schema_aware_pooling_error() -> float:
    errors = []
    for task, target in TARGETS.items():
        canonical_actions = tuple(canonicalize(record) for record in RECORDS if record["task"] == task)
        pooled = mean_action(canonical_actions)  # type: ignore[arg-type]
        errors.append(mean_absolute_error(pooled, target))
    return sum(errors) / len(errors)


def maximum_round_trip_error() -> float:
    errors = []
    for record in RECORDS:
        adapter = ADAPTERS[record["embodiment_id"]]
        raw = record["raw_action"]
        restored = adapter.from_canonical(adapter.to_canonical(raw))
        errors.extend(abs(first - second) for first, second in zip(raw, restored))
    return max(errors)


def evaluate() -> dict[str, object]:
    rejected_missing_metadata = False
    try:
        canonicalize({"episode_id": "unknown-1", "task": "forward_open", "raw_action": (0.2, 1.0)})
    except ValueError:
        rejected_missing_metadata = True

    canonical_actions = {
        record["episode_id"]: tuple(round(value, 12) for value in canonicalize(record))
        for record in RECORDS
    }
    return {
        "record_count": len(RECORDS),
        "raw_action_dimension": 2,
        "canonical_actions": canonical_actions,
        "same_shape_but_semantics_differ": True,
        "naive_raw_pooling_semantic_mae": round(naive_raw_pooling_error(), 12),
        "schema_aware_pooling_semantic_mae": round(schema_aware_pooling_error(), 12),
        "maximum_adapter_round_trip_error": round(maximum_round_trip_error(), 12),
        "missing_embodiment_metadata_rejected": rejected_missing_metadata,
    }
