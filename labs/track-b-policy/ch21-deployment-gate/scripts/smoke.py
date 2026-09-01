#!/usr/bin/env python3
"""Run EXP-21-01 without a model, device, network, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from deployment_gate import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if not metrics["latency"]["mean_passes_deadline"]:
        raise AssertionError("the fixture mean must pass the deadline")
    if metrics["latency"]["all_cycles_meet_deadline"]:
        raise AssertionError("the fixture tail must include a deadline miss")
    burst = metrics["deadline_burst_comparison"]
    if burst["bursted"]["deadline_miss_rate"] != burst["scattered"]["deadline_miss_rate"]:
        raise AssertionError("burst comparison must preserve the aggregate miss rate")
    if burst["bursted"]["maximum_consecutive_deadline_misses"] <= burst["scattered"]["maximum_consecutive_deadline_misses"]:
        raise AssertionError("burst length must expose information hidden by miss rate")
    if metrics["async_schedule"]["reason_counts"] != {"queue_underflow": 1, "stale_chunk": 1}:
        raise AssertionError("async fixture must expose one underflow and one stale chunk")
    fallback_audit = metrics["fallback_reactivation_audit"]
    health_only = fallback_audit["health_only_negative_control"]["trace"]
    authorization_aware = fallback_audit["authorization_aware"]["trace"]
    if health_only[5]["mode"] != "policy_action":
        raise AssertionError("health-only negative control must reactivate after two healthy packets")
    if authorization_aware[5]["mode"] != "request_operator":
        raise AssertionError("healthy packets must not bypass explicit reactivation authorization")
    if authorization_aware[6]["mode"] != "policy_action":
        raise AssertionError("authorized recovery must reactivate after the healthy window")
    lifecycle = metrics["fallback_lifecycle_audit"]
    success = lifecycle["success_then_authorize"]["trace"]
    timeout = lifecycle["premature_authorization_then_timeout"]["trace"]
    late_success = lifecycle["timeout_then_late_success"]
    failed = lifecycle["reported_failure"]
    if success[2]["reactivation_allowed"] or not success[3]["reactivation_allowed"]:
        raise AssertionError("fallback completion and reactivation authorization must remain separate")
    if timeout[3]["failure_reason"] != "fallback_timeout" or timeout[3]["reactivation_allowed"]:
        raise AssertionError("fallback timeout must fail closed")
    if late_success["trace"][3]["effective_state"] != "failed" or late_success["reactivation_count"]:
        raise AssertionError("late success must not clear a latched fallback timeout")
    if failed["reactivation_count"] != 0:
        raise AssertionError("reported fallback failure must never reactivate policy")
    receipt_audit = metrics["reactivation_receipt_audit"]
    if receipt_audit["allowed_count"] != 1 or receipt_audit["rejected_count"] != 8:
        raise AssertionError("only the fresh, correctly bound receipt may pass")
    replay_reasons = receipt_audit["cases"]["replayed"]
    if replay_reasons != (
        "replay_or_out_of_order_receipt",
        "receipt_already_consumed",
    ):
        raise AssertionError("a consumed receipt must be rejected by identity and sequence")
    if metrics["allowed_count"] != 1 or metrics["fallback_count"] != 6:
        raise AssertionError("the deployment gate fixture changed")
    selective = metrics["selective_evaluation"]
    if selective["threshold_0_5"]["coverage"] >= selective["threshold_0_7"]["coverage"]:
        raise AssertionError("the permissive threshold must increase fixture coverage")
    if selective["threshold_0_5"]["accepted_failure_rate"] >= selective["threshold_0_7"]["accepted_failure_rate"]:
        raise AssertionError("the permissive threshold must expose the fixture risk tradeoff")
    severity_audit = metrics["severity_stratified_selective_audit"]
    reject_high = severity_audit["reject_high_consequence_failure"]
    reject_low = severity_audit["reject_low_consequence_failure"]
    aggregate_metrics = ("coverage", "accepted_failure_rate", "failure_recall_by_rejection")
    if any(reject_high[name] != reject_low[name] for name in aggregate_metrics):
        raise AssertionError("severity comparison must preserve aggregate selective metrics")
    if reject_high["accepted_failure_authored_weight"] >= reject_low["accepted_failure_authored_weight"]:
        raise AssertionError("accepted authored consequence must expose the hidden severity difference")
    transition = metrics["action_transition_audit"]
    if not transition["smooth_transition"]["allowed"]:
        raise AssertionError("the bounded smooth transition must pass the authored transition gate")
    if transition["legal_endpoint_jump"]["allowed"]:
        raise AssertionError("static endpoint bounds must not bypass the authored transition limit")
    if transition["legal_endpoint_jump"]["reasons"] != ["action_delta_exceeded"]:
        raise AssertionError("the legal-endpoint jump must retain its distinct reason code")
    if transition["missing_history"]["reasons"] != ["missing_previous_applied_action"]:
        raise AssertionError("an enabled transition limit must fail closed without applied history")
    report = {
        "experiment_id": "EXP-21-01",
        "status": "smoke",
        "scope": "deadline and action-gate fixture; not real-time, safety, or deployment certification",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
