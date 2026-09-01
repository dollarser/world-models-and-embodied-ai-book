"""Deterministic deadline and deployment-safety gate for Chapter 21."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from math import ceil, isfinite
from pathlib import Path
import sys


SHARED_ROOT = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(SHARED_ROOT))

from action_schema import ActionSchema, MOBILE_BASE_SCHEMA  # noqa: E402


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)


@dataclass(frozen=True)
class GateConfig:
    deadline_ms: float = 50.0
    max_sensor_age_ms: float = 100.0
    action_schema: ActionSchema = MOBILE_BASE_SCHEMA
    enforce_action_transition: bool = False
    max_uncertainty_score: float = 0.7
    uncertainty_revision: str = "fixture-v1"
    fallback: str = "hold_position"

    def __post_init__(self) -> None:
        for name, value in (
            ("deadline_ms", self.deadline_ms),
            ("max_sensor_age_ms", self.max_sensor_age_ms),
        ):
            if not _finite_number(value) or value <= 0.0:
                raise ValueError(f"{name} must be a finite positive number")
        if not isinstance(self.action_schema, ActionSchema):
            raise ValueError("action_schema must be an ActionSchema")
        if not isinstance(self.enforce_action_transition, bool):
            raise ValueError("enforce_action_transition must be boolean")
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
    command_id: int = 8
    command_session_id: str = "policy-session-003"
    executor_boot_id: str = "executor-boot-012"
    schema_id: str = MOBILE_BASE_SCHEMA.schema_id
    frame_id: str = MOBILE_BASE_SCHEMA.frame_id
    field_names: tuple[str, ...] = tuple(field.name for field in MOBILE_BASE_SCHEMA.fields)
    units: tuple[str, ...] = tuple(field.unit for field in MOBILE_BASE_SCHEMA.fields)
    control_hz: float = MOBILE_BASE_SCHEMA.control_hz
    clock_id: str = MOBILE_BASE_SCHEMA.clock_id


@dataclass(frozen=True)
class AppliedAction:
    """An authored prior-command record; a real system must bind this to actuator acknowledgement."""

    action: tuple[float, ...]
    applied_step: int
    command_id: int = 7
    acknowledged_command_id: int = 7
    command_session_id: str = "policy-session-003"
    executor_boot_id: str = "executor-boot-012"
    schema_id: str = MOBILE_BASE_SCHEMA.schema_id
    frame_id: str = MOBILE_BASE_SCHEMA.frame_id
    field_names: tuple[str, ...] = tuple(field.name for field in MOBILE_BASE_SCHEMA.fields)
    units: tuple[str, ...] = tuple(field.unit for field in MOBILE_BASE_SCHEMA.fields)
    control_hz: float = MOBILE_BASE_SCHEMA.control_hz
    clock_id: str = MOBILE_BASE_SCHEMA.clock_id


@dataclass(frozen=True)
class CommandReceipt:
    """Executor-local receipt; it is not an authenticated or durable device acknowledgement."""

    command_session_id: str
    executor_boot_id: str
    command_id: int
    action: tuple[float, ...]
    applied_step: int
    payload_digest: str


@dataclass(frozen=True)
class ExecutorLedger:
    """Immutable teaching state for one negotiated producer session and executor boot."""

    command_session_id: str
    executor_boot_id: str
    highest_command_id: int = -1
    receipts: tuple[CommandReceipt, ...] = ()


def command_payload_digest(packet: ActionPacket) -> str:
    """Digest the action envelope deterministically; this is not authentication or a signature."""

    payload = {
        "action": packet.action,
        "current_step": packet.current_step,
        "valid_until_step": packet.valid_until_step,
        "schema_id": packet.schema_id,
        "frame_id": packet.frame_id,
        "field_names": packet.field_names,
        "units": packet.units,
        "control_hz": packet.control_hz,
        "clock_id": packet.clock_id,
    }
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("command payload must be finite and JSON-serializable") from exc
    return sha256(encoded).hexdigest()


def apply_command_once(
    packet: ActionPacket,
    ledger: ExecutorLedger,
) -> tuple[ExecutorLedger, dict[str, object]]:
    """Model executor-side deduplication after gating, without claiming crash atomicity."""

    if not isinstance(packet, ActionPacket) or not isinstance(ledger, ExecutorLedger):
        raise ValueError("packet and ledger must use the declared command contract")
    if not ledger.command_session_id or not ledger.executor_boot_id:
        raise ValueError("ledger session and boot identities must be explicit")
    if (
        isinstance(ledger.highest_command_id, bool)
        or not isinstance(ledger.highest_command_id, int)
        or ledger.highest_command_id < -1
    ):
        raise ValueError("highest_command_id must be an integer greater than or equal to -1")
    if not isinstance(ledger.receipts, tuple) or any(
        not isinstance(receipt, CommandReceipt)
        or receipt.command_session_id != ledger.command_session_id
        or receipt.executor_boot_id != ledger.executor_boot_id
        or receipt.command_id > ledger.highest_command_id
        for receipt in ledger.receipts
    ):
        raise ValueError("ledger receipts must belong to its session, boot, and sequence range")
    receipt_ids = tuple(receipt.command_id for receipt in ledger.receipts)
    if len(receipt_ids) != len(set(receipt_ids)):
        raise ValueError("ledger receipt command IDs must be unique")
    if packet.command_session_id != ledger.command_session_id:
        return ledger, {"applied_new": False, "status": "command_session_mismatch"}
    if packet.executor_boot_id != ledger.executor_boot_id:
        return ledger, {"applied_new": False, "status": "executor_boot_mismatch"}
    if isinstance(packet.command_id, bool) or not isinstance(packet.command_id, int) or packet.command_id < 0:
        return ledger, {"applied_new": False, "status": "invalid_command_id"}

    payload_digest = command_payload_digest(packet)
    existing = next(
        (receipt for receipt in ledger.receipts if receipt.command_id == packet.command_id),
        None,
    )
    if existing is not None:
        if existing.payload_digest == payload_digest:
            return ledger, {
                "applied_new": False,
                "status": "duplicate_returned_cached_receipt",
                "receipt": asdict(existing),
            }
        return ledger, {"applied_new": False, "status": "command_identity_conflict"}
    if packet.command_id <= ledger.highest_command_id:
        return ledger, {"applied_new": False, "status": "stale_or_out_of_order_command"}

    receipt = CommandReceipt(
        command_session_id=packet.command_session_id,
        executor_boot_id=packet.executor_boot_id,
        command_id=packet.command_id,
        action=packet.action,
        applied_step=packet.current_step,
        payload_digest=payload_digest,
    )
    updated = replace(
        ledger,
        highest_command_id=packet.command_id,
        receipts=ledger.receipts + (receipt,),
    )
    return updated, {"applied_new": True, "status": "applied_once", "receipt": asdict(receipt)}


@dataclass(frozen=True)
class ActionChunk:
    """A chunk schedule in control-step coordinates; valid_until_step is exclusive."""

    chunk_id: str
    observed_step: int
    arrival_step: int
    start_step: int
    valid_until_step: int


@dataclass(frozen=True)
class ReactivationReceipt:
    """Authored approval record; identity strings are not authenticated principals."""

    receipt_id: str
    approver_id: str
    fallback_run_id: str
    target_mode: str
    issued_step: int
    valid_until_step: int
    sequence: int
    decision: str


def validate_reactivation_receipt(
    receipt: ReactivationReceipt,
    *,
    now_step: int,
    expected_fallback_run_id: str,
    expected_target_mode: str,
    authorized_approver_ids: frozenset[str],
    last_accepted_sequence: int | None = None,
    consumed_receipt_ids: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    """Validate binding, freshness and single-use semantics without authenticating a sender."""

    if not isinstance(receipt, ReactivationReceipt):
        return ("invalid_reactivation_receipt",)
    if isinstance(now_step, bool) or not isinstance(now_step, int) or now_step < 0:
        raise ValueError("now_step must be a non-negative integer")
    if not isinstance(expected_fallback_run_id, str) or not expected_fallback_run_id:
        raise ValueError("expected_fallback_run_id must be explicit")
    if not isinstance(expected_target_mode, str) or not expected_target_mode:
        raise ValueError("expected_target_mode must be explicit")
    if (
        not isinstance(authorized_approver_ids, frozenset)
        or not authorized_approver_ids
        or any(not isinstance(value, str) or not value for value in authorized_approver_ids)
    ):
        raise ValueError("authorized_approver_ids must be a non-empty frozenset of strings")
    if last_accepted_sequence is not None and (
        isinstance(last_accepted_sequence, bool)
        or not isinstance(last_accepted_sequence, int)
        or last_accepted_sequence < 0
    ):
        raise ValueError("last_accepted_sequence must be a non-negative integer or None")
    if not isinstance(consumed_receipt_ids, frozenset) or any(
        not isinstance(value, str) or not value for value in consumed_receipt_ids
    ):
        raise ValueError("consumed_receipt_ids must be a frozenset of non-empty strings")

    issues = []
    for name, value in (
        ("receipt_id", receipt.receipt_id),
        ("approver_id", receipt.approver_id),
        ("fallback_run_id", receipt.fallback_run_id),
        ("target_mode", receipt.target_mode),
        ("decision", receipt.decision),
    ):
        if not isinstance(value, str) or not value:
            issues.append(f"invalid_{name}")

    step_fields_valid = all(
        not isinstance(value, bool) and isinstance(value, int) and value >= 0
        for value in (receipt.issued_step, receipt.valid_until_step)
    )
    if not step_fields_valid or receipt.issued_step >= receipt.valid_until_step:
        issues.append("invalid_receipt_validity_interval")
    elif not receipt.issued_step <= now_step < receipt.valid_until_step:
        issues.append("stale_or_future_receipt_time")

    if (
        isinstance(receipt.sequence, bool)
        or not isinstance(receipt.sequence, int)
        or receipt.sequence < 0
    ):
        issues.append("invalid_receipt_sequence")
    elif last_accepted_sequence is not None and receipt.sequence <= last_accepted_sequence:
        issues.append("replay_or_out_of_order_receipt")

    if receipt.fallback_run_id != expected_fallback_run_id:
        issues.append("fallback_run_mismatch")
    if receipt.target_mode != expected_target_mode:
        issues.append("target_mode_mismatch")
    if receipt.approver_id not in authorized_approver_ids:
        issues.append("unauthorized_approver")
    if receipt.decision != "approved":
        issues.append("reactivation_not_approved")
    if receipt.receipt_id in consumed_receipt_ids:
        issues.append("receipt_already_consumed")
    return tuple(dict.fromkeys(issues))


def reactivation_receipt_audit() -> dict[str, object]:
    """Run fixed negative controls for an authored, single-use reactivation receipt."""

    receipt = ReactivationReceipt(
        receipt_id="receipt-042",
        approver_id="operator-alpha",
        fallback_run_id="fallback-run-007",
        target_mode="policy_action",
        issued_step=100,
        valid_until_step=105,
        sequence=42,
        decision="approved",
    )
    common = {
        "now_step": 102,
        "expected_fallback_run_id": "fallback-run-007",
        "expected_target_mode": "policy_action",
        "authorized_approver_ids": frozenset({"operator-alpha"}),
    }
    valid_issues = validate_reactivation_receipt(receipt, **common)
    if valid_issues:
        raise AssertionError("the authored valid receipt must pass before consumption")

    cases = {
        "valid": valid_issues,
        "replayed": validate_reactivation_receipt(
            receipt,
            last_accepted_sequence=receipt.sequence,
            consumed_receipt_ids=frozenset({receipt.receipt_id}),
            **common,
        ),
        "expired": validate_reactivation_receipt(
            replace(
                receipt,
                receipt_id="receipt-expired",
                issued_step=90,
                valid_until_step=100,
            ),
            **common,
        ),
        "future": validate_reactivation_receipt(
            replace(
                receipt,
                receipt_id="receipt-future",
                issued_step=103,
                valid_until_step=108,
            ),
            **common,
        ),
        "wrong_run": validate_reactivation_receipt(
            replace(receipt, receipt_id="receipt-run", fallback_run_id="fallback-run-old"),
            **common,
        ),
        "wrong_target": validate_reactivation_receipt(
            replace(receipt, receipt_id="receipt-target", target_mode="diagnostic_mode"),
            **common,
        ),
        "unauthorized_approver": validate_reactivation_receipt(
            replace(receipt, receipt_id="receipt-approver", approver_id="operator-unknown"),
            **common,
        ),
        "denied": validate_reactivation_receipt(
            replace(receipt, receipt_id="receipt-denied", decision="denied"),
            **common,
        ),
        "out_of_order": validate_reactivation_receipt(
            replace(receipt, receipt_id="receipt-old-sequence", sequence=41),
            last_accepted_sequence=42,
            **common,
        ),
    }
    return {
        "case_count": len(cases),
        "allowed_count": sum(not issues for issues in cases.values()),
        "rejected_count": sum(bool(issues) for issues in cases.values()),
        "cases": cases,
        "scope": (
            "hand-authored receipt fields and in-memory single-session state; "
            "not authentication, integrity, cryptography, reboot persistence, or safety evidence"
        ),
    }


def nearest_rank(values: tuple[float, ...], percentile: float) -> float:
    if not values or not 0.0 < percentile <= 1.0:
        raise ValueError("values must be non-empty and percentile in (0, 1]")
    if any(not _finite_number(value) or value < 0.0 for value in values):
        raise ValueError("latencies must be finite non-negative numbers")
    ordered = sorted(float(value) for value in values)
    return ordered[ceil(percentile * len(ordered)) - 1]


def latency_summary(
    latencies_ms: tuple[float, ...], deadline_ms: float
) -> dict[str, float | int | bool]:
    if not _finite_number(deadline_ms) or deadline_ms <= 0.0:
        raise ValueError("deadline must be a finite positive number")
    if not latencies_ms:
        raise ValueError("at least one latency sample is required")
    if any(not _finite_number(value) or value < 0.0 for value in latencies_ms):
        raise ValueError("latencies must be finite non-negative numbers")
    mean = sum(latencies_ms) / len(latencies_ms)
    misses = sum(value > deadline_ms for value in latencies_ms)
    longest_miss_burst = 0
    current_miss_burst = 0
    for value in latencies_ms:
        if value > deadline_ms:
            current_miss_burst += 1
            longest_miss_burst = max(longest_miss_burst, current_miss_burst)
        else:
            current_miss_burst = 0
    return {
        "mean_ms": round(mean, 6),
        "p95_ms": round(nearest_rank(latencies_ms, 0.95), 6),
        "p99_ms": round(nearest_rank(latencies_ms, 0.99), 6),
        "max_ms": round(max(latencies_ms), 6),
        "deadline_miss_count": misses,
        "deadline_miss_rate": round(misses / len(latencies_ms), 6),
        "maximum_consecutive_deadline_misses": longest_miss_burst,
        "mean_passes_deadline": mean <= deadline_ms,
        "all_cycles_meet_deadline": misses == 0,
    }


def audit_async_schedule(
    chunks: tuple[ActionChunk, ...],
    total_steps: int,
    max_observation_lag_steps: int,
) -> dict[str, object]:
    """Audit whether an async chunk schedule supplies fresh actions at every tick."""
    if isinstance(total_steps, bool) or not isinstance(total_steps, int) or total_steps <= 0:
        raise ValueError("total_steps must be a positive integer")
    if (
        isinstance(max_observation_lag_steps, bool)
        or not isinstance(max_observation_lag_steps, int)
        or max_observation_lag_steps < 0
    ):
        raise ValueError("max_observation_lag_steps must be a non-negative integer")
    if not chunks:
        raise ValueError("at least one action chunk is required")

    seen_ids = set()
    for chunk in chunks:
        if not isinstance(chunk, ActionChunk):
            raise TypeError("chunks must contain ActionChunk values")
        if not isinstance(chunk.chunk_id, str) or not chunk.chunk_id or chunk.chunk_id in seen_ids:
            raise ValueError("chunk ids must be non-empty and unique")
        seen_ids.add(chunk.chunk_id)
        fields = (chunk.observed_step, chunk.arrival_step, chunk.start_step, chunk.valid_until_step)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in fields):
            raise ValueError("chunk step fields must be non-negative integers")
        if chunk.observed_step > chunk.arrival_step:
            raise ValueError("a chunk cannot arrive before its source observation")
        if chunk.start_step >= chunk.valid_until_step:
            raise ValueError("chunk validity interval must be non-empty")

    trace = []
    reason_counts = {"queue_underflow": 0, "stale_chunk": 0}
    for step in range(total_steps):
        candidates = tuple(
            chunk
            for chunk in chunks
            if chunk.arrival_step <= step and chunk.start_step <= step < chunk.valid_until_step
        )
        if not candidates:
            reason = "queue_underflow"
            selected = None
            observation_lag = None
        else:
            selected_chunk = max(
                candidates,
                key=lambda chunk: (chunk.observed_step, chunk.arrival_step, chunk.chunk_id),
            )
            selected = selected_chunk.chunk_id
            observation_lag = step - selected_chunk.observed_step
            reason = "stale_chunk" if observation_lag > max_observation_lag_steps else None
        if reason:
            reason_counts[reason] += 1
        trace.append(
            {
                "step": step,
                "selected_chunk": selected,
                "observation_lag_steps": observation_lag,
                "mode": "fallback" if reason else "policy_action",
                "reason": reason,
            }
        )

    fallback_count = sum(item["mode"] == "fallback" for item in trace)
    return {
        "total_steps": total_steps,
        "policy_action_count": total_steps - fallback_count,
        "fallback_count": fallback_count,
        "late_arrival_count": sum(chunk.arrival_step > chunk.start_step for chunk in chunks),
        "reason_counts": reason_counts,
        "trace": trace,
    }


def fallback_state_machine(
    allowed_sequence: tuple[bool, ...],
    *,
    initial_mode: str,
    escalated_mode: str,
    failures_to_escalate: int = 3,
    successes_to_recover: int = 2,
    reactivation_authorized_sequence: tuple[bool, ...] | None = None,
) -> dict[str, object]:
    """Exercise a generic escalation/recovery contract, not an actuator controller."""
    if not allowed_sequence or any(not isinstance(value, bool) for value in allowed_sequence):
        raise ValueError("allowed_sequence must be a non-empty boolean tuple")
    if not initial_mode or not escalated_mode or initial_mode == escalated_mode:
        raise ValueError("fallback modes must be distinct and explicit")
    for name, value in (
        ("failures_to_escalate", failures_to_escalate),
        ("successes_to_recover", successes_to_recover),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    authorization_required = reactivation_authorized_sequence is not None
    if authorization_required and (
        len(reactivation_authorized_sequence) != len(allowed_sequence)
        or any(not isinstance(value, bool) for value in reactivation_authorized_sequence)
    ):
        raise ValueError("reactivation authorization must be a same-length boolean tuple")

    failure_streak = 0
    recovery_streak = 0
    escalated = False
    trace = []
    for step, allowed in enumerate(allowed_sequence):
        reactivation_authorized = (
            reactivation_authorized_sequence[step]
            if reactivation_authorized_sequence is not None
            else None
        )
        recovery_blocked_reason = None
        if allowed:
            failure_streak = 0
            if escalated:
                recovery_streak += 1
                if recovery_streak >= successes_to_recover:
                    if not authorization_required or reactivation_authorized:
                        escalated = False
                        recovery_streak = 0
                    else:
                        recovery_blocked_reason = "reactivation_not_authorized"
            mode = escalated_mode if escalated else "policy_action"
        else:
            recovery_streak = 0
            failure_streak += 1
            escalated = escalated or failure_streak >= failures_to_escalate
            mode = escalated_mode if escalated else initial_mode
        trace.append(
            {
                "step": step,
                "allowed": allowed,
                "mode": mode,
                "failure_streak": failure_streak,
                "recovery_streak": recovery_streak,
                "reactivation_authorized": reactivation_authorized,
                "recovery_blocked_reason": recovery_blocked_reason,
            }
        )
    return {
        "failures_to_escalate": failures_to_escalate,
        "successes_to_recover": successes_to_recover,
        "reactivation_authorization_required": authorization_required,
        "trace": trace,
    }


def fallback_reactivation_audit() -> dict[str, object]:
    """Separate healthy input hysteresis from explicit policy reactivation."""

    allowed = (True, False, False, False, True, True, True)
    authorization = (False, False, False, False, False, False, True)
    common = {
        "initial_mode": "controlled_stop",
        "escalated_mode": "request_operator",
    }
    return {
        "health_only_negative_control": fallback_state_machine(allowed, **common),
        "authorization_aware": fallback_state_machine(
            allowed,
            reactivation_authorized_sequence=authorization,
            **common,
        ),
        "scope": "hand-authored gate-health and reactivation-authorization sequences; not fallback completion",
    }


FALLBACK_LIFECYCLE_TRANSITIONS = {
    "requested": frozenset({"requested", "operating", "failed"}),
    "operating": frozenset({"operating", "succeeded", "failed"}),
    "succeeded": frozenset({"succeeded"}),
    "failed": frozenset({"failed"}),
}


def audit_fallback_lifecycle(
    reported_states: tuple[str, ...],
    reactivation_authorized_sequence: tuple[bool, ...],
    *,
    max_operating_steps: int,
) -> dict[str, object]:
    """Audit lifecycle reports and fail closed on timeout; not an MRM controller."""

    if not reported_states or any(
        not isinstance(state, str) or state not in FALLBACK_LIFECYCLE_TRANSITIONS
        for state in reported_states
    ):
        raise ValueError("reported fallback states must use the explicit lifecycle vocabulary")
    if reported_states[0] != "requested":
        raise ValueError("fallback lifecycle must begin with requested")
    if (
        len(reactivation_authorized_sequence) != len(reported_states)
        or any(not isinstance(value, bool) for value in reactivation_authorized_sequence)
    ):
        raise ValueError("reactivation authorization must be a same-length boolean tuple")
    if (
        isinstance(max_operating_steps, bool)
        or not isinstance(max_operating_steps, int)
        or max_operating_steps <= 0
    ):
        raise ValueError("max_operating_steps must be a positive integer")

    for previous, current in zip(reported_states, reported_states[1:]):
        if current not in FALLBACK_LIFECYCLE_TRANSITIONS[previous]:
            raise ValueError(f"illegal fallback lifecycle transition: {previous}->{current}")

    operating_steps = 0
    failure_latched = False
    trace = []
    for step, (reported_state, reactivation_authorized) in enumerate(
        zip(reported_states, reactivation_authorized_sequence)
    ):
        failure_reason = None
        if failure_latched:
            effective_state = "failed"
        elif reported_state == "operating":
            operating_steps += 1
            if operating_steps > max_operating_steps:
                effective_state = "failed"
                failure_latched = True
                failure_reason = "fallback_timeout"
            else:
                effective_state = reported_state
        elif reported_state == "failed":
            effective_state = "failed"
            failure_latched = True
            failure_reason = "fallback_reported_failed"
        else:
            effective_state = reported_state

        reactivation_allowed = effective_state == "succeeded" and reactivation_authorized
        if reactivation_allowed:
            blocked_reason = None
        elif effective_state == "failed" and reactivation_authorized:
            blocked_reason = "fallback_failed"
        elif reactivation_authorized:
            blocked_reason = "fallback_not_succeeded"
        elif effective_state == "succeeded":
            blocked_reason = "reactivation_not_authorized"
        else:
            blocked_reason = None
        trace.append(
            {
                "step": step,
                "reported_state": reported_state,
                "effective_state": effective_state,
                "operating_steps": operating_steps,
                "reactivation_authorized": reactivation_authorized,
                "reactivation_allowed": reactivation_allowed,
                "blocked_reason": blocked_reason,
                "failure_reason": failure_reason,
            }
        )

    return {
        "max_operating_steps": max_operating_steps,
        "reactivation_count": sum(item["reactivation_allowed"] for item in trace),
        "trace": trace,
    }


def fallback_lifecycle_audit() -> dict[str, object]:
    """Compare successful, timed-out, and explicitly failed authored lifecycles."""

    return {
        "success_then_authorize": audit_fallback_lifecycle(
            ("requested", "operating", "succeeded", "succeeded"),
            (False, False, False, True),
            max_operating_steps=2,
        ),
        "premature_authorization_then_timeout": audit_fallback_lifecycle(
            ("requested", "operating", "operating", "operating"),
            (False, True, True, True),
            max_operating_steps=2,
        ),
        "timeout_then_late_success": audit_fallback_lifecycle(
            ("requested", "operating", "operating", "succeeded"),
            (False, False, False, True),
            max_operating_steps=1,
        ),
        "reported_failure": audit_fallback_lifecycle(
            ("requested", "operating", "failed", "failed"),
            (False, False, True, True),
            max_operating_steps=2,
        ),
        "scope": "hand-authored lifecycle reports and authorization; not fallback execution or safety evidence",
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


def selective_consequence_metrics(
    cases: tuple[tuple[str, bool, float], ...], accepted_case_ids: tuple[str, ...]
) -> dict[str, object]:
    """Audit authored failure-consequence weights without interpreting them as real risk."""
    if not cases:
        raise ValueError("at least one consequence-audit case is required")
    case_ids = tuple(case_id for case_id, _, _ in cases)
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ValueError("case IDs must be non-empty strings")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("case IDs must be unique")
    if any(
        not isinstance(failed, bool) or not _finite_number(weight) or weight <= 0.0
        for _, failed, weight in cases
    ):
        raise ValueError("cases require boolean failures and finite positive authored weights")
    if (
        not accepted_case_ids
        or any(not isinstance(case_id, str) or not case_id for case_id in accepted_case_ids)
        or len(set(accepted_case_ids)) != len(accepted_case_ids)
        or not set(accepted_case_ids).issubset(case_ids)
    ):
        raise ValueError("accepted case IDs must be a non-empty unique subset of cases")

    accepted_ids = set(accepted_case_ids)
    accepted = tuple(case for case in cases if case[0] in accepted_ids)
    failure_cases = tuple(case for case in cases if case[1])
    accepted_failures = tuple(case for case in accepted if case[1])
    rejected_failures = tuple(case for case in failure_cases if case[0] not in accepted_ids)
    total_failure_weight = sum(weight for _, _, weight in failure_cases)
    accepted_failure_weight = sum(weight for _, _, weight in accepted_failures)
    rejected_failure_weight = sum(weight for _, _, weight in rejected_failures)
    return {
        "coverage": round(len(accepted) / len(cases), 6),
        "accepted_failure_rate": round(len(accepted_failures) / len(accepted), 6),
        "failure_recall_by_rejection": (
            round(len(rejected_failures) / len(failure_cases), 6) if failure_cases else None
        ),
        "accepted_failure_authored_weight": round(accepted_failure_weight, 6),
        "total_failure_authored_weight": round(total_failure_weight, 6),
        "authored_weight_recall_by_rejection": (
            round(rejected_failure_weight / total_failure_weight, 6)
            if total_failure_weight
            else None
        ),
        "accepted_failure_ids": tuple(case_id for case_id, _, _ in accepted_failures),
    }


def severity_stratified_selective_audit() -> dict[str, object]:
    """Hold aggregate counts fixed while swapping which authored failure is accepted."""
    cases = (
        ("safe-a", False, 1.0),
        ("safe-b", False, 1.0),
        ("safe-c", False, 1.0),
        ("safe-d", False, 1.0),
        ("low-consequence-failure", True, 1.0),
        ("high-consequence-failure", True, 10.0),
    )
    shared_safe = ("safe-a", "safe-b", "safe-c")
    return {
        "reject_high_consequence_failure": selective_consequence_metrics(
            cases, shared_safe + ("low-consequence-failure",)
        ),
        "reject_low_consequence_failure": selective_consequence_metrics(
            cases, shared_safe + ("high-consequence-failure",)
        ),
        "weight_semantics": (
            "hand-authored sensitivity-analysis proxy weight; not probability, injury, monetary loss, "
            "or validated real-world risk"
        ),
    }


def gate(
    packet: ActionPacket,
    config: GateConfig,
    *,
    previous_applied_action: AppliedAction | None = None,
) -> dict[str, object]:
    reasons = []
    schema = config.action_schema
    if not _finite_number(packet.sensor_age_ms) or packet.sensor_age_ms < 0.0:
        reasons.append("invalid_sensor_age")
    elif packet.sensor_age_ms > config.max_sensor_age_ms:
        reasons.append("stale_observation")

    if not _finite_number(packet.pipeline_latency_ms) or packet.pipeline_latency_ms < 0.0:
        reasons.append("invalid_latency")
    elif packet.pipeline_latency_ms > config.deadline_ms:
        reasons.append("deadline_miss")

    expected_field_names = tuple(field.name for field in schema.fields)
    expected_units = tuple(field.unit for field in schema.fields)
    if packet.schema_id != schema.schema_id:
        reasons.append("schema_mismatch")
    if packet.frame_id != schema.frame_id:
        reasons.append("frame_mismatch")
    if packet.field_names != expected_field_names:
        reasons.append("field_order_mismatch")
    if packet.units != expected_units:
        reasons.append("unit_mismatch")
    if packet.control_hz != schema.control_hz:
        reasons.append("control_rate_mismatch")
    if packet.clock_id != schema.clock_id:
        reasons.append("clock_mismatch")
    if not isinstance(packet.command_session_id, str) or not packet.command_session_id:
        reasons.append("invalid_command_session_id")
    if not isinstance(packet.executor_boot_id, str) or not packet.executor_boot_id:
        reasons.append("invalid_executor_boot_id")
    if isinstance(packet.command_id, bool) or not isinstance(packet.command_id, int) or packet.command_id < 0:
        reasons.append("invalid_command_id")

    if not packet.action or any(not _finite_number(value) for value in packet.action):
        reasons.append("invalid_action")
    elif len(packet.action) != len(schema.fields):
        reasons.append("action_dimension_mismatch")
    else:
        for value, field in zip(packet.action, schema.fields):
            if not field.minimum <= value <= field.maximum:
                reasons.append(f"action_out_of_bounds:{field.name}")

    if config.enforce_action_transition:
        if previous_applied_action is None:
            reasons.append("missing_previous_applied_action")
        elif not isinstance(previous_applied_action, AppliedAction):
            reasons.append("invalid_previous_applied_action")
        else:
            if previous_applied_action.schema_id != schema.schema_id:
                reasons.append("previous_schema_mismatch")
            if previous_applied_action.frame_id != schema.frame_id:
                reasons.append("previous_frame_mismatch")
            if previous_applied_action.field_names != expected_field_names:
                reasons.append("previous_field_order_mismatch")
            if previous_applied_action.units != expected_units:
                reasons.append("previous_unit_mismatch")
            if previous_applied_action.control_hz != schema.control_hz:
                reasons.append("previous_control_rate_mismatch")
            if previous_applied_action.clock_id != schema.clock_id:
                reasons.append("previous_clock_mismatch")
            if previous_applied_action.command_session_id != packet.command_session_id:
                reasons.append("previous_command_session_mismatch")
            if previous_applied_action.executor_boot_id != packet.executor_boot_id:
                reasons.append("previous_executor_boot_mismatch")
            if (
                isinstance(previous_applied_action.command_id, bool)
                or not isinstance(previous_applied_action.command_id, int)
                or previous_applied_action.command_id < 0
                or previous_applied_action.acknowledged_command_id
                != previous_applied_action.command_id
            ):
                reasons.append("invalid_applied_action_ack")
            elif (
                not isinstance(packet.command_id, bool)
                and isinstance(packet.command_id, int)
                and previous_applied_action.command_id >= packet.command_id
            ):
                reasons.append("previous_command_not_before_current")
            previous_action_valid = bool(previous_applied_action.action) and all(
                _finite_number(value) for value in previous_applied_action.action
            )
            if not previous_action_valid:
                reasons.append("invalid_previous_applied_action")
            elif len(previous_applied_action.action) != len(packet.action):
                reasons.append("action_shape_mismatch")
            else:
                for current, previous, field in zip(
                    packet.action, previous_applied_action.action, schema.fields
                ):
                    if abs(current - previous) > field.maximum_delta_per_step:
                        reasons.append(f"action_delta_exceeded:{field.name}")

            if (
                isinstance(previous_applied_action.applied_step, bool)
                or not isinstance(previous_applied_action.applied_step, int)
                or previous_applied_action.applied_step < 0
                or isinstance(packet.current_step, bool)
                or not isinstance(packet.current_step, int)
                or previous_applied_action.applied_step + 1 != packet.current_step
            ):
                reasons.append("previous_applied_step_mismatch")

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


def action_transition_audit() -> dict[str, object]:
    """Show why legal action endpoints do not establish a legal one-step transition."""

    config = GateConfig(enforce_action_transition=True)
    previous = AppliedAction((0.0, 0.0), applied_step=1)
    common = {
        "sensor_age_ms": 20.0,
        "pipeline_latency_ms": 25.0,
        "current_step": 2,
        "valid_until_step": 5,
        "uncertainty_score": 0.2,
        "uncertainty_revision": "fixture-v1",
    }
    smooth_packet = ActionPacket(action=(0.2, -0.1), **common)
    jump_packet = ActionPacket(action=(0.4, -0.1), **common)
    smooth = gate(smooth_packet, config, previous_applied_action=previous)
    jump = gate(jump_packet, config, previous_applied_action=previous)
    missing_history = gate(jump_packet, config)
    identity_negative_controls = {
        "current_schema": gate(
            replace(smooth_packet, schema_id="mobile-base-v0"),
            config,
            previous_applied_action=previous,
        ),
        "previous_units": gate(
            smooth_packet,
            config,
            previous_applied_action=replace(previous, units=("km/h", "deg/s")),
        ),
        "previous_control_rate": gate(
            smooth_packet,
            config,
            previous_applied_action=replace(previous, control_hz=20.0),
        ),
        "previous_ack": gate(
            smooth_packet,
            config,
            previous_applied_action=replace(previous, acknowledged_command_id=6),
        ),
        "previous_session": gate(
            smooth_packet,
            config,
            previous_applied_action=replace(previous, command_session_id="policy-session-002"),
        ),
        "previous_boot": gate(
            smooth_packet,
            config,
            previous_applied_action=replace(previous, executor_boot_id="executor-boot-011"),
        ),
    }

    def transition_record(packet: ActionPacket, decision: dict[str, object]) -> dict[str, object]:
        return {
            "action": packet.action,
            "static_endpoint_within_bounds": all(
                field.minimum <= value <= field.maximum
                for value, field in zip(packet.action, config.action_schema.fields)
            ),
            "absolute_delta_by_field": {
                field.name: round(abs(current - prior), 6)
                for current, prior, field in zip(
                    packet.action, previous.action, config.action_schema.fields
                )
            },
            **decision,
        }

    return {
        "schema_id": config.action_schema.schema_id,
        "field_contracts": {
            field.name: {
                "unit": field.unit,
                "minimum": field.minimum,
                "maximum": field.maximum,
                "maximum_delta_per_step": field.maximum_delta_per_step,
            }
            for field in config.action_schema.fields
        },
        "previous_applied_action": previous.action,
        "previous_command_id": previous.command_id,
        "acknowledged_command_id": previous.acknowledged_command_id,
        "command_session_id": previous.command_session_id,
        "executor_boot_id": previous.executor_boot_id,
        "smooth_transition": transition_record(smooth_packet, smooth),
        "legal_endpoint_jump": transition_record(jump_packet, jump),
        "missing_history": missing_history,
        "identity_negative_controls": identity_negative_controls,
        "scope": (
            "hand-authored physical-unit action vectors, identity fields, command acknowledgement, and "
            "step IDs; not authenticated acknowledgement, dynamics, acceleration, jerk, tracking, "
            "feasibility, or safety evidence"
        ),
    }


def command_idempotency_audit() -> dict[str, object]:
    """Exercise duplicate, conflict, ordering, session, and boot controls in one epoch."""

    ledger = ExecutorLedger("policy-session-003", "executor-boot-012", highest_command_id=7)
    packet = ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5, 0.2, "fixture-v1")
    updated, first = apply_command_once(packet, ledger)
    after_duplicate, duplicate = apply_command_once(packet, updated)
    _, conflict = apply_command_once(replace(packet, action=(0.3, -0.1)), updated)
    _, contract_conflict = apply_command_once(replace(packet, valid_until_step=6), updated)
    _, out_of_order = apply_command_once(replace(packet, command_id=6), updated)
    _, wrong_session = apply_command_once(
        replace(packet, command_id=9, command_session_id="policy-session-004"), updated
    )
    _, wrong_boot = apply_command_once(
        replace(packet, command_id=9, executor_boot_id="executor-boot-013"), updated
    )
    restarted = ExecutorLedger("policy-session-004", "executor-boot-013")
    restarted_packet = replace(
        packet,
        command_id=0,
        command_session_id="policy-session-004",
        executor_boot_id="executor-boot-013",
    )
    restarted_updated, explicit_restart = apply_command_once(restarted_packet, restarted)
    return {
        "first": first,
        "duplicate": duplicate,
        "conflict": conflict,
        "contract_conflict": contract_conflict,
        "out_of_order": out_of_order,
        "wrong_session": wrong_session,
        "wrong_boot": wrong_boot,
        "explicit_restart": explicit_restart,
        "receipt_count_after_duplicate": len(after_duplicate.receipts),
        "receipt_count_after_explicit_restart": len(restarted_updated.receipts),
        "scope": (
            "immutable in-memory state transition after gating; not a database transaction, "
            "authenticated actuator acknowledgement, crash-recovery proof, or exactly-once physical effect"
        ),
    }


LATENCIES_MS = (20.0, 22.0, 24.0, 26.0, 28.0, 150.0)
BURSTED_LATENCIES_MS = (20.0, 80.0, 80.0, 20.0, 20.0, 20.0)
SCATTERED_LATENCIES_MS = (20.0, 80.0, 20.0, 80.0, 20.0, 20.0)


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
            "action_out_of_bounds:linear_velocity",
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
    async_schedule = (
        ActionChunk("chunk-a", 0, 0, 0, 3),
        ActionChunk("chunk-b", 1, 3, 3, 5),
        ActionChunk("chunk-c", 5, 6, 5, 8),
    )
    return {
        "latency": latency_summary(LATENCIES_MS, config.deadline_ms),
        "deadline_burst_comparison": {
            "bursted": latency_summary(BURSTED_LATENCIES_MS, config.deadline_ms),
            "scattered": latency_summary(SCATTERED_LATENCIES_MS, config.deadline_ms),
        },
        "async_schedule": audit_async_schedule(async_schedule, 8, 2),
        "fallback_reactivation_audit": fallback_reactivation_audit(),
        "fallback_lifecycle_audit": fallback_lifecycle_audit(),
        "reactivation_receipt_audit": reactivation_receipt_audit(),
        "decisions": decisions,
        "allowed_count": sum(decision["allowed"] for decision in decisions.values()),
        "fallback_count": sum(not decision["allowed"] for decision in decisions.values()),
        "reason_counts": reason_counts,
        "selective_evaluation": {
            "threshold_0_5": selective_metrics(selective_cases, 0.5),
            "threshold_0_7": selective_metrics(selective_cases, 0.7),
        },
        "severity_stratified_selective_audit": severity_stratified_selective_audit(),
        "action_transition_audit": action_transition_audit(),
        "command_idempotency_audit": command_idempotency_audit(),
        "fallback_is_profile_specific": {
            "manipulator": GateConfig(fallback="hold_position").fallback,
            "mobile_robot": GateConfig(fallback="controlled_stop").fallback,
            "vehicle": GateConfig(fallback="request_minimum_risk_maneuver").fallback,
        },
    }
