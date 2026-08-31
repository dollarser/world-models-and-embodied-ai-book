"""Executable action-contract fixture for Chapter 15."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionField:
    name: str
    unit: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class ActionSchema:
    schema_id: str
    frame_id: str
    fields: tuple[ActionField, ...]
    control_hz: float
    prediction_horizon: int
    execution_horizon: int
    max_age_ms: int


MOBILE_BASE_SCHEMA = ActionSchema(
    schema_id="mobile-base-v1",
    frame_id="base_link",
    fields=(
        ActionField("linear_velocity", "m/s", -0.5, 0.5),
        ActionField("yaw_rate", "rad/s", -1.0, 1.0),
    ),
    control_hz=10.0,
    prediction_horizon=3,
    execution_horizon=1,
    max_age_ms=100,
)

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
    schema: ActionSchema = MOBILE_BASE_SCHEMA,
) -> dict[str, object]:
    return {
        "source": source,
        "schema_id": schema.schema_id,
        "frame_id": schema.frame_id,
        "units": tuple(field.unit for field in schema.fields),
        "control_hz": schema.control_hz,
        "prediction_horizon": len(actions),
        "execution_horizon": schema.execution_horizon,
        "timestamp_ms": timestamp_ms,
        "actions": actions,
    }


def validate_packet(
    packet: dict[str, object],
    schema: ActionSchema = MOBILE_BASE_SCHEMA,
    now_ms: int = 1000,
) -> tuple[str, ...]:
    issues = []
    if packet.get("source") not in EXECUTABLE_SOURCES:
        issues.append("non_executable_source")
    if packet.get("schema_id") != schema.schema_id:
        issues.append("schema_mismatch")
    if packet.get("frame_id") != schema.frame_id:
        issues.append("frame_mismatch")
    expected_units = tuple(field.unit for field in schema.fields)
    if packet.get("units") != expected_units:
        issues.append("unit_mismatch")
    timestamp = packet.get("timestamp_ms")
    if (
        isinstance(timestamp, bool)
        or not isinstance(timestamp, int)
        or timestamp > now_ms
        or now_ms - timestamp > schema.max_age_ms
    ):
        issues.append("stale_or_future_timestamp")
    if packet.get("control_hz") != schema.control_hz:
        issues.append("control_rate_mismatch")

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

    for action in actions:
        if not isinstance(action, tuple) or len(action) != len(schema.fields):
            issues.append("action_dimension_mismatch")
            continue
        for value, field in zip(action, schema.fields):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
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
    }
    valid_issues = {name: validate_packet(packet) for name, packet in valid_packets.items()}
    malformed_issues = {name: validate_packet(packet) for name, packet in malformed_packets.items()}
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
    }
