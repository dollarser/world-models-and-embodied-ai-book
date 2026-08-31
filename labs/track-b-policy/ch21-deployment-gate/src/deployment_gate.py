"""Deterministic deadline and deployment-safety gate for Chapter 21."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)


@dataclass(frozen=True)
class GateConfig:
    deadline_ms: float = 50.0
    max_sensor_age_ms: float = 100.0
    max_abs_action: float = 1.0
    fallback: str = "hold_position"

    def __post_init__(self) -> None:
        for name, value in (
            ("deadline_ms", self.deadline_ms),
            ("max_sensor_age_ms", self.max_sensor_age_ms),
            ("max_abs_action", self.max_abs_action),
        ):
            if not _finite_number(value) or value <= 0.0:
                raise ValueError(f"{name} must be a finite positive number")
        if not self.fallback:
            raise ValueError("fallback must be explicit")


@dataclass(frozen=True)
class ActionPacket:
    sensor_age_ms: float
    pipeline_latency_ms: float
    action: tuple[float, ...]
    current_step: int
    valid_until_step: int


def nearest_rank(values: tuple[float, ...], percentile: float) -> float:
    if not values or not 0.0 < percentile <= 1.0:
        raise ValueError("values must be non-empty and percentile in (0, 1]")
    if any(not _finite_number(value) or value < 0.0 for value in values):
        raise ValueError("latencies must be finite non-negative numbers")
    ordered = sorted(float(value) for value in values)
    return ordered[ceil(percentile * len(ordered)) - 1]


def latency_summary(latencies_ms: tuple[float, ...], deadline_ms: float) -> dict[str, float | bool]:
    if not _finite_number(deadline_ms) or deadline_ms <= 0.0:
        raise ValueError("deadline must be a finite positive number")
    if not latencies_ms:
        raise ValueError("at least one latency sample is required")
    if any(not _finite_number(value) or value < 0.0 for value in latencies_ms):
        raise ValueError("latencies must be finite non-negative numbers")
    mean = sum(latencies_ms) / len(latencies_ms)
    misses = sum(value > deadline_ms for value in latencies_ms)
    return {
        "mean_ms": round(mean, 6),
        "p95_ms": round(nearest_rank(latencies_ms, 0.95), 6),
        "max_ms": round(max(latencies_ms), 6),
        "deadline_miss_rate": round(misses / len(latencies_ms), 6),
        "mean_passes_deadline": mean <= deadline_ms,
        "all_cycles_meet_deadline": misses == 0,
    }


def gate(packet: ActionPacket, config: GateConfig) -> dict[str, object]:
    reasons = []
    if not _finite_number(packet.sensor_age_ms) or packet.sensor_age_ms < 0.0:
        reasons.append("invalid_sensor_age")
    elif packet.sensor_age_ms > config.max_sensor_age_ms:
        reasons.append("stale_observation")

    if not _finite_number(packet.pipeline_latency_ms) or packet.pipeline_latency_ms < 0.0:
        reasons.append("invalid_latency")
    elif packet.pipeline_latency_ms > config.deadline_ms:
        reasons.append("deadline_miss")

    if not packet.action or any(not _finite_number(value) for value in packet.action):
        reasons.append("invalid_action")
    elif any(abs(value) > config.max_abs_action for value in packet.action):
        reasons.append("action_out_of_bounds")

    if (
        isinstance(packet.current_step, bool)
        or isinstance(packet.valid_until_step, bool)
        or not isinstance(packet.current_step, int)
        or not isinstance(packet.valid_until_step, int)
        or packet.current_step < 0
        or packet.valid_until_step < 0
    ):
        reasons.append("invalid_action_horizon")
    elif packet.current_step >= packet.valid_until_step:
        reasons.append("action_chunk_expired")

    return {
        "allowed": not reasons,
        "reasons": reasons,
        "selected_mode": "policy_action" if not reasons else config.fallback,
    }


LATENCIES_MS = (20.0, 22.0, 24.0, 26.0, 28.0, 150.0)


def evaluate() -> dict[str, object]:
    config = GateConfig()
    packets = {
        "healthy": ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5),
        "stale": ActionPacket(120.0, 25.0, (0.2, -0.1), 2, 5),
        "late": ActionPacket(20.0, 80.0, (0.2, -0.1), 2, 5),
        "non_finite": ActionPacket(20.0, 25.0, (float("nan"), 0.0), 2, 5),
        "out_of_bounds": ActionPacket(20.0, 25.0, (1.2, 0.0), 2, 5),
        "expired": ActionPacket(20.0, 25.0, (0.2, -0.1), 5, 5),
    }
    decisions = {name: gate(packet, config) for name, packet in packets.items()}
    reason_counts = {
        reason: sum(reason in decision["reasons"] for decision in decisions.values())
        for reason in (
            "stale_observation",
            "deadline_miss",
            "invalid_action",
            "action_out_of_bounds",
            "action_chunk_expired",
        )
    }
    return {
        "latency": latency_summary(LATENCIES_MS, config.deadline_ms),
        "decisions": decisions,
        "allowed_count": sum(decision["allowed"] for decision in decisions.values()),
        "fallback_count": sum(not decision["allowed"] for decision in decisions.values()),
        "reason_counts": reason_counts,
        "fallback_is_profile_specific": {
            "manipulator": GateConfig(fallback="hold_position").fallback,
            "mobile_robot": GateConfig(fallback="controlled_stop").fallback,
            "vehicle": GateConfig(fallback="request_minimum_risk_maneuver").fallback,
        },
    }
