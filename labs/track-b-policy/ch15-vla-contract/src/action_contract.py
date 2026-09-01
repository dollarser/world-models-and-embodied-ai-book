"""Executable action-contract fixture for Chapter 15."""

from __future__ import annotations

import math
from pathlib import Path
import sys

SHARED_ROOT = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(SHARED_ROOT))

from action_schema import ActionField, ActionSchema, MOBILE_BASE_SCHEMA  # noqa: E402,F401

EXECUTABLE_SOURCES = {"continuous", "discrete_tokens", "flow_chunk"}


def unnormalize_action(values: tuple[float, ...], schema: ActionSchema) -> tuple[float, ...]:
    if len(values) != len(schema.fields):
        raise ValueError("action dimension does not match schema")
    physical = []
    for value, field in zip(values, schema.fields):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("normalized action must be numeric")
        if not -1.0 <= value <= 1.0:
            raise ValueError("normalized action must be in [-1, 1]")
        physical.append(field.minimum + (value + 1.0) * (field.maximum - field.minimum) / 2.0)
    return tuple(physical)


def encode_tokens(values: tuple[float, ...], bins: int = 5) -> tuple[int, ...]:
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError("at least two bins are required")
    step = 2.0 / (bins - 1)
    tokens = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("normalized action must be numeric")
        if not -1.0 <= value <= 1.0:
            raise ValueError("normalized action must be in [-1, 1]")
        tokens.append(round((value + 1.0) / step))
    return tuple(tokens)


def decode_tokens(tokens: tuple[int, ...], bins: int = 5) -> tuple[float, ...]:
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError("at least two bins are required")
    if any(
        isinstance(token, bool)
        or not isinstance(token, int)
        or token < 0
        or token >= bins
        for token in tokens
    ):
        raise ValueError("token is outside the action vocabulary")
    step = 2.0 / (bins - 1)
    return tuple(-1.0 + token * step for token in tokens)


def make_packet(
    source: str,
    actions: tuple[tuple[float, ...], ...],
    timestamp_ms: int = 950,
    command_id: int = 7,
    observation_timestep: int = 42,
    first_action_timestep: int = 42,
    schema: ActionSchema = MOBILE_BASE_SCHEMA,
) -> dict[str, object]:
    return {
        "source": source,
        "schema_id": schema.schema_id,
        "frame_id": schema.frame_id,
        "field_names": tuple(field.name for field in schema.fields),
        "units": tuple(field.unit for field in schema.fields),
        "clock_id": schema.clock_id,
        "control_hz": schema.control_hz,
        "prediction_horizon": len(actions),
        "execution_horizon": schema.execution_horizon,
        "timestamp_ms": timestamp_ms,
        "command_id": command_id,
        "observation_timestep": observation_timestep,
        "first_action_timestep": first_action_timestep,
        "actions": actions,
    }


def validate_packet(
    packet: dict[str, object],
    schema: ActionSchema = MOBILE_BASE_SCHEMA,
    now_ms: int = 1000,
    last_accepted_command_id: int | None = None,
    expected_observation_timestep: int = 42,
    expected_first_action_timestep: int = 42,
) -> tuple[str, ...]:
    if not isinstance(packet, dict):
        return ("invalid_packet",)
    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
        raise ValueError("now_ms must be a non-negative integer on the schema clock")
    if last_accepted_command_id is not None and (
        isinstance(last_accepted_command_id, bool)
        or not isinstance(last_accepted_command_id, int)
        or last_accepted_command_id < 0
    ):
        raise ValueError("last_accepted_command_id must be a non-negative integer or None")
    for value, name in (
        (expected_observation_timestep, "expected_observation_timestep"),
        (expected_first_action_timestep, "expected_first_action_timestep"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    issues = []
    if packet.get("source") not in EXECUTABLE_SOURCES:
        issues.append("non_executable_source")
    if packet.get("schema_id") != schema.schema_id:
        issues.append("schema_mismatch")
    if packet.get("frame_id") != schema.frame_id:
        issues.append("frame_mismatch")
    expected_field_names = tuple(field.name for field in schema.fields)
    if packet.get("field_names") != expected_field_names:
        issues.append("field_order_mismatch")
    expected_units = tuple(field.unit for field in schema.fields)
    if packet.get("units") != expected_units:
        issues.append("unit_mismatch")
    if packet.get("clock_id") != schema.clock_id:
        issues.append("clock_mismatch")
    command_id = packet.get("command_id")
    if isinstance(command_id, bool) or not isinstance(command_id, int) or command_id < 0:
        issues.append("invalid_command_id")
    elif last_accepted_command_id is not None and command_id <= last_accepted_command_id:
        issues.append("replay_or_out_of_order_command")
    timestamp = packet.get("timestamp_ms")
    if (
        isinstance(timestamp, bool)
        or not isinstance(timestamp, int)
        or timestamp < 0
        or timestamp > now_ms
        or now_ms - timestamp > schema.max_age_ms
    ):
        issues.append("stale_or_future_timestamp")
    if packet.get("control_hz") != schema.control_hz:
        issues.append("control_rate_mismatch")
    observation_timestep = packet.get("observation_timestep")
    if (
        isinstance(observation_timestep, bool)
        or not isinstance(observation_timestep, int)
        or observation_timestep != expected_observation_timestep
    ):
        issues.append("observation_timestep_mismatch")
    first_action_timestep = packet.get("first_action_timestep")
    if (
        isinstance(first_action_timestep, bool)
        or not isinstance(first_action_timestep, int)
        or first_action_timestep != expected_first_action_timestep
    ):
        issues.append("action_timestep_mismatch")

    actions = packet.get("actions")
    if not isinstance(actions, tuple) or not actions:
        issues.append("missing_action_values")
        return tuple(issues)
    declared_prediction_horizon = packet.get("prediction_horizon")
    if (
        not isinstance(declared_prediction_horizon, int)
        or isinstance(declared_prediction_horizon, bool)
        or declared_prediction_horizon != len(actions)
    ):
        issues.append("prediction_horizon_mismatch")
    if len(actions) > schema.prediction_horizon:
        issues.append("prediction_horizon_exceeded")
    execution_horizon = packet.get("execution_horizon")
    if (
        isinstance(execution_horizon, bool)
        or not isinstance(execution_horizon, int)
        or not 1 <= execution_horizon <= len(actions)
    ):
        issues.append("invalid_execution_horizon")
    elif execution_horizon > schema.execution_horizon:
        issues.append("execution_horizon_exceeded")

    for action in actions:
        if not isinstance(action, tuple) or len(action) != len(schema.fields):
            issues.append("action_dimension_mismatch")
            continue
        for value, field in zip(action, schema.fields):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not field.minimum <= value <= field.maximum
            ):
                issues.append(f"out_of_bounds:{field.name}")
    return tuple(dict.fromkeys(issues))


def evaluate() -> dict[str, object]:
    normalized = (0.6, -0.4)
    continuous = unnormalize_action(normalized, MOBILE_BASE_SCHEMA)
    tokens = encode_tokens(normalized, bins=5)
    token_normalized = decode_tokens(tokens, bins=5)
    token_physical = unnormalize_action(token_normalized, MOBILE_BASE_SCHEMA)

    valid_packets = {
        "continuous": make_packet("continuous", (continuous,)),
        "discrete_tokens": make_packet("discrete_tokens", (token_physical,)),
        "flow_chunk": make_packet("flow_chunk", (continuous, continuous, continuous)),
    }
    malformed_packets = {
        "high_level_text": make_packet("high_level_text", tuple()),
        "stale": make_packet("continuous", (continuous,), timestamp_ms=800),
        "wrong_frame": {**make_packet("continuous", (continuous,)), "frame_id": "camera"},
        "wrong_units": {**make_packet("continuous", (continuous,)), "units": ("km/h", "deg/s")},
        "out_of_bounds": make_packet("continuous", ((0.8, 0.0),)),
        "wrong_clock": {**make_packet("continuous", (continuous,)), "clock_id": "wall_clock_ms"},
        "wrong_field_order": {
            **make_packet("continuous", (continuous,)),
            "field_names": ("yaw_rate", "linear_velocity"),
        },
        "execution_horizon_bypass": {
            **make_packet("flow_chunk", (continuous, continuous, continuous)),
            "execution_horizon": 3,
        },
        "replay": make_packet("continuous", (continuous,), command_id=7),
        "out_of_order": make_packet("continuous", (continuous,), command_id=6),
        "fresh_but_stale_observation": make_packet(
            "continuous", (continuous,), timestamp_ms=990, observation_timestep=40
        ),
        "wrong_action_timestep": make_packet(
            "continuous", (continuous,), timestamp_ms=990, first_action_timestep=43
        ),
    }
    valid_issues = {name: validate_packet(packet) for name, packet in valid_packets.items()}
    malformed_issues = {
        name: validate_packet(
            packet,
            last_accepted_command_id=7 if name in {"replay", "out_of_order"} else None,
        )
        for name, packet in malformed_packets.items()
    }
    next_command_issues = validate_packet(
        make_packet("continuous", (continuous,), command_id=8),
        last_accepted_command_id=7,
    )
    rejected = sum(bool(issues) for issues in malformed_issues.values())
    quantization_error = round(
        sum(abs(a - b) for a, b in zip(normalized, token_normalized)) / len(normalized),
        12,
    )
    executed_prefix = valid_packets["flow_chunk"]["actions"][: MOBILE_BASE_SCHEMA.execution_horizon]

    return {
        "continuous_decoded_action": tuple(round(value, 12) for value in continuous),
        "discrete_tokens": tokens,
        "token_mean_absolute_normalized_error": quantization_error,
        "valid_packet_count": sum(not issues for issues in valid_issues.values()),
        "malformed_packet_count": len(malformed_packets),
        "malformed_rejection_rate": rejected / len(malformed_packets),
        "high_level_text_directly_executable": not bool(malformed_issues["high_level_text"]),
        "flow_chunk_predicted_steps": len(valid_packets["flow_chunk"]["actions"]),
        "flow_chunk_executed_prefix_steps": len(executed_prefix),
        "valid_packet_issues": valid_issues,
        "malformed_packet_issues": malformed_issues,
        "next_ordered_command_accepted": not bool(next_command_issues),
        "replay_command_rejected": bool(malformed_issues["replay"]),
        "out_of_order_command_rejected": bool(malformed_issues["out_of_order"]),
        "execution_horizon_bypass_rejected": bool(malformed_issues["execution_horizon_bypass"]),
        "fresh_but_stale_observation_rejected": bool(malformed_issues["fresh_but_stale_observation"]),
        "wrong_action_timestep_rejected": bool(malformed_issues["wrong_action_timestep"]),
    }
