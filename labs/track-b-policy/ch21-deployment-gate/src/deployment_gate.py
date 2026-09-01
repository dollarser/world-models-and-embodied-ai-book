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
    max_uncertainty_score: float = 0.7
    uncertainty_revision: str = "fixture-v1"
    fallback: str = "hold_position"

    def __post_init__(self) -> None:
        for name, value in (
            ("deadline_ms", self.deadline_ms),
            ("max_sensor_age_ms", self.max_sensor_age_ms),
            ("max_abs_action", self.max_abs_action),
        ):
            if not _finite_number(value) or value <= 0.0:
                raise ValueError(f"{name} must be a finite positive number")
        if (
            not _finite_number(self.max_uncertainty_score)
            or not 0.0 <= self.max_uncertainty_score <= 1.0
        ):
            raise ValueError("max_uncertainty_score must lie in [0, 1]")
        if not isinstance(self.uncertainty_revision, str) or not self.uncertainty_revision:
            raise ValueError("uncertainty_revision must be explicit")
        if not self.fallback:
            raise ValueError("fallback must be explicit")


@dataclass(frozen=True)
class ActionPacket:
    sensor_age_ms: float
    pipeline_latency_ms: float
    action: tuple[float, ...]
    current_step: int
    valid_until_step: int
    uncertainty_score: float
    uncertainty_revision: str


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


def selective_metrics(
    cases: tuple[tuple[float, bool], ...], threshold: float
) -> dict[str, float | None]:
    """Summarize a fixed uncertainty threshold without treating its score as a probability."""
    if not cases:
        raise ValueError("at least one selective-evaluation case is required")
    if not _finite_number(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    if any(
        not _finite_number(score)
        or not 0.0 <= score <= 1.0
        or not isinstance(failed, bool)
        for score, failed in cases
    ):
        raise ValueError("cases require normalized finite scores and boolean failure labels")

    accepted = tuple(failed for score, failed in cases if score <= threshold)
    total_failures = sum(failed for _, failed in cases)
    rejected_failures = sum(failed for score, failed in cases if score > threshold)
    return {
        "coverage": round(len(accepted) / len(cases), 6),
        "accepted_failure_rate": round(sum(accepted) / len(accepted), 6) if accepted else None,
        "failure_recall_by_rejection": round(rejected_failures / total_failures, 6) if total_failures else None,
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

    if not _finite_number(packet.uncertainty_score) or not 0.0 <= packet.uncertainty_score <= 1.0:
        reasons.append("invalid_uncertainty_score")
    elif packet.uncertainty_score > config.max_uncertainty_score:
        reasons.append("uncertainty_exceeds_limit")
    if packet.uncertainty_revision != config.uncertainty_revision:
        reasons.append("uncertainty_revision_mismatch")

    return {
        "allowed": not reasons,
        "reasons": reasons,
        "selected_mode": "policy_action" if not reasons else config.fallback,
    }


LATENCIES_MS = (20.0, 22.0, 24.0, 26.0, 28.0, 150.0)


def evaluate() -> dict[str, object]:
    config = GateConfig()
    packets = {
        "healthy": ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5, 0.2, "fixture-v1"),
        "stale": ActionPacket(120.0, 25.0, (0.2, -0.1), 2, 5, 0.2, "fixture-v1"),
        "late": ActionPacket(20.0, 80.0, (0.2, -0.1), 2, 5, 0.2, "fixture-v1"),
        "non_finite": ActionPacket(20.0, 25.0, (float("nan"), 0.0), 2, 5, 0.2, "fixture-v1"),
        "out_of_bounds": ActionPacket(20.0, 25.0, (1.2, 0.0), 2, 5, 0.2, "fixture-v1"),
        "expired": ActionPacket(20.0, 25.0, (0.2, -0.1), 5, 5, 0.2, "fixture-v1"),
        "uncertain": ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5, 0.9, "fixture-v1"),
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
            "uncertainty_exceeds_limit",
        )
    }
    selective_cases = (
        (0.1, False),
        (0.2, False),
        (0.3, False),
        (0.6, True),
        (0.8, True),
        (0.9, True),
    )
    return {
        "latency": latency_summary(LATENCIES_MS, config.deadline_ms),
        "decisions": decisions,
        "allowed_count": sum(decision["allowed"] for decision in decisions.values()),
        "fallback_count": sum(not decision["allowed"] for decision in decisions.values()),
        "reason_counts": reason_counts,
        "selective_evaluation": {
            "threshold_0_5": selective_metrics(selective_cases, 0.5),
            "threshold_0_7": selective_metrics(selective_cases, 0.7),
        },
        "fallback_is_profile_specific": {
            "manipulator": GateConfig(fallback="hold_position").fallback,
            "mobile_robot": GateConfig(fallback="controlled_stop").fallback,
            "vehicle": GateConfig(fallback="request_minimum_risk_maneuver").fallback,
        },
    }
