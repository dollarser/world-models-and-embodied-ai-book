"""Cross-embodiment action adapter fixture for Chapter 16."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from typing import Mapping, Sequence


CanonicalAction = tuple[float, float]  # (delta_x_m, gripper_open_fraction)
RawAction = tuple[float, float]


@dataclass(frozen=True)
class EmbodimentAdapter:
    embodiment_id: str
    delta_x_unit: str
    delta_x_scale_to_m: float
    gripper_polarity: int
    canonical_schema_version: str = "ee-delta-v1"
    raw_action_fields: tuple[str, str] = ("delta_x", "gripper")

    def __post_init__(self) -> None:
        if not self.embodiment_id or not self.delta_x_unit or not self.canonical_schema_version:
            raise ValueError("embodiment_id, delta_x_unit, and canonical_schema_version must be explicit")
        if (
            not isinstance(self.raw_action_fields, tuple)
            or len(self.raw_action_fields) != 2
            or any(not isinstance(field, str) or not field for field in self.raw_action_fields)
            or len(set(self.raw_action_fields)) != 2
        ):
            raise ValueError("raw_action_fields must contain two distinct non-empty names")
        if (
            isinstance(self.delta_x_scale_to_m, bool)
            or not isinstance(self.delta_x_scale_to_m, (int, float))
            or not isfinite(self.delta_x_scale_to_m)
            or self.delta_x_scale_to_m <= 0.0
        ):
            raise ValueError("delta_x_scale_to_m must be a finite positive number")
        if isinstance(self.gripper_polarity, bool) or self.gripper_polarity not in (-1, 1):
            raise ValueError("gripper_polarity must be -1 or 1")

    @property
    def schema_fingerprint(self) -> str:
        """Bind records to every field that changes raw-to-canonical semantics."""
        payload = {
            "canonical_schema_version": self.canonical_schema_version,
            "delta_x_scale_to_m": self.delta_x_scale_to_m,
            "delta_x_unit": self.delta_x_unit,
            "embodiment_id": self.embodiment_id,
            "gripper_polarity": self.gripper_polarity,
            "raw_action_fields": self.raw_action_fields,
        }
        canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

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

def _record(episode_id: str, task: str, embodiment_id: str, raw_action: RawAction) -> dict[str, object]:
    return {
        "episode_id": episode_id,
        "task": task,
        "embodiment_id": embodiment_id,
        "adapter_schema_fingerprint": ADAPTERS[embodiment_id].schema_fingerprint,
        "raw_action": raw_action,
    }


RECORDS = (
    _record("a-1", "forward_open", "arm_a", (0.2, 1.0)),
    _record("a-2", "back_close", "arm_a", (-0.1, -1.0)),
    _record("b-1", "forward_open", "arm_b", (2.0, -1.0)),
    _record("b-2", "back_close", "arm_b", (-1.0, 1.0)),
)


def canonicalize(record: object) -> CanonicalAction:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")
    embodiment_id = record.get("embodiment_id")
    if embodiment_id not in ADAPTERS:
        raise ValueError("missing or unknown embodiment metadata")
    adapter = ADAPTERS[embodiment_id]
    if record.get("adapter_schema_fingerprint") != adapter.schema_fingerprint:
        raise ValueError("missing or stale adapter schema fingerprint")
    raw_action = record.get("raw_action")
    if not isinstance(raw_action, tuple) or len(raw_action) != 2:
        raise ValueError("invalid raw action")
    return adapter.to_canonical(raw_action)


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


def mixture_exposure_report(dataset_episode_lengths: Mapping[str, Sequence[int]]) -> dict[str, object]:
    """Compare dataset-, episode-, and transition-uniform sampling denominators."""
    if not isinstance(dataset_episode_lengths, Mapping) or not dataset_episode_lengths:
        raise ValueError("dataset episode lengths must be a non-empty mapping")
    episode_counts: dict[str, int] = {}
    transition_counts: dict[str, int] = {}
    for dataset, lengths in dataset_episode_lengths.items():
        if not isinstance(dataset, str) or not dataset:
            raise ValueError("dataset names must be non-empty strings")
        if isinstance(lengths, (str, bytes)) or not isinstance(lengths, Sequence) or not lengths:
            raise ValueError("each dataset must contain at least one episode length")
        validated_lengths = []
        for length in lengths:
            if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
                raise ValueError("episode lengths must be positive integers")
            validated_lengths.append(length)
        episode_counts[dataset] = len(validated_lengths)
        transition_counts[dataset] = sum(validated_lengths)

    labels = tuple(sorted(episode_counts))
    dataset_count = len(labels)
    episode_count = sum(episode_counts.values())
    transition_count = sum(transition_counts.values())
    return {
        "dataset_count": dataset_count,
        "episode_count": episode_count,
        "transition_count": transition_count,
        "episode_counts_by_dataset": {label: episode_counts[label] for label in labels},
        "transition_counts_by_dataset": {label: transition_counts[label] for label in labels},
        "dataset_uniform_exposure": {label: round(1.0 / dataset_count, 12) for label in labels},
        "episode_uniform_exposure": {
            label: round(episode_counts[label] / episode_count, 12) for label in labels
        },
        "transition_uniform_exposure": {
            label: round(transition_counts[label] / transition_count, 12) for label in labels
        },
    }


def evaluate() -> dict[str, object]:
    malformed_records = {
        "missing_embodiment": {
            "episode_id": "unknown-1",
            "task": "forward_open",
            "raw_action": (0.2, 1.0),
        },
        "missing_fingerprint": {
            "episode_id": "a-old-1",
            "task": "forward_open",
            "embodiment_id": "arm_a",
            "raw_action": (0.2, 1.0),
        },
        "stale_fingerprint": {
            "episode_id": "a-stale-1",
            "task": "forward_open",
            "embodiment_id": "arm_a",
            "adapter_schema_fingerprint": "sha256:" + "0" * 64,
            "raw_action": (0.2, 1.0),
        },
    }
    rejected_contract_records = {}
    for name, record in malformed_records.items():
        try:
            canonicalize(record)
        except ValueError as error:
            rejected_contract_records[name] = str(error)

    altered_arm_a = EmbodimentAdapter("arm_a", "controller_delta", 0.01, 1)

    canonical_actions = {
        record["episode_id"]: tuple(round(value, 12) for value in canonicalize(record))
        for record in RECORDS
    }
    return {
        "record_count": len(RECORDS),
        "raw_action_dimension": 2,
        "canonical_schema_version": ADAPTERS["arm_a"].canonical_schema_version,
        "adapter_schema_fingerprints": {
            name: adapter.schema_fingerprint for name, adapter in ADAPTERS.items()
        },
        "canonical_actions": canonical_actions,
        "same_shape_but_semantics_differ": True,
        "naive_raw_pooling_semantic_mae": round(naive_raw_pooling_error(), 12),
        "schema_aware_pooling_semantic_mae": round(schema_aware_pooling_error(), 12),
        "maximum_adapter_round_trip_error": round(maximum_round_trip_error(), 12),
        "rejected_contract_records": rejected_contract_records,
        "contract_rejection_rate": len(rejected_contract_records) / len(malformed_records),
        "semantic_change_changes_fingerprint": (
            altered_arm_a.schema_fingerprint != ADAPTERS["arm_a"].schema_fingerprint
        ),
        "mixture_exposure": mixture_exposure_report(
            {
                "short_dataset": (2,),
                "long_dataset": (4, 4, 4),
            }
        ),
    }
