from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from deployment_gate import (  # noqa: E402
    ActionChunk,
    ActionPacket,
    BURSTED_LATENCIES_MS,
    GateConfig,
    LATENCIES_MS,
    ReactivationReceipt,
    SCATTERED_LATENCIES_MS,
    audit_async_schedule,
    audit_fallback_lifecycle,
    evaluate,
    fallback_lifecycle_audit,
    fallback_reactivation_audit,
    fallback_state_machine,
    gate,
    latency_summary,
    nearest_rank,
    reactivation_receipt_audit,
    selective_metrics,
    validate_reactivation_receipt,
)


class DeploymentGateTests(unittest.TestCase):
    def test_mean_can_pass_while_tail_misses_deadline(self):
        result = latency_summary(LATENCIES_MS, 50.0)
        self.assertEqual(result["mean_ms"], 45.0)
        self.assertEqual(result["p95_ms"], 150.0)
        self.assertTrue(result["mean_passes_deadline"])
        self.assertFalse(result["all_cycles_meet_deadline"])
        self.assertEqual(result["p99_ms"], 150.0)
        self.assertEqual(result["maximum_consecutive_deadline_misses"], 1)

    def test_equal_miss_rates_can_hide_different_burst_lengths(self):
        bursted = latency_summary(BURSTED_LATENCIES_MS, 50.0)
        scattered = latency_summary(SCATTERED_LATENCIES_MS, 50.0)
        self.assertEqual(bursted["deadline_miss_rate"], scattered["deadline_miss_rate"])
        self.assertEqual(bursted["maximum_consecutive_deadline_misses"], 2)
        self.assertEqual(scattered["maximum_consecutive_deadline_misses"], 1)

    def test_async_schedule_exposes_underflow_and_stale_actions(self):
        chunks = (
            ActionChunk("a", 0, 0, 0, 3),
            ActionChunk("b", 1, 3, 3, 5),
            ActionChunk("c", 5, 6, 5, 8),
        )
        audit = audit_async_schedule(chunks, 8, 2)
        self.assertEqual(audit["policy_action_count"], 6)
        self.assertEqual(audit["fallback_count"], 2)
        self.assertEqual(audit["reason_counts"], {"queue_underflow": 1, "stale_chunk": 1})

    def test_async_schedule_rejects_impossible_chunk_contracts(self):
        with self.assertRaises(ValueError):
            audit_async_schedule((ActionChunk("a", 2, 1, 1, 3),), 3, 1)
        with self.assertRaises(ValueError):
            audit_async_schedule((ActionChunk("a", 0, 0, 2, 2),), 3, 1)

    def test_fallback_escalation_requires_sustained_recovery(self):
        result = fallback_state_machine(
            (True, False, False, False, True, True),
            initial_mode="controlled_stop",
            escalated_mode="request_operator",
        )
        modes = [item["mode"] for item in result["trace"]]
        self.assertEqual(
            modes,
            ["policy_action", "controlled_stop", "controlled_stop", "request_operator", "request_operator", "policy_action"],
        )

    def test_fallback_state_machine_rejects_ambiguous_configuration(self):
        with self.assertRaises(ValueError):
            fallback_state_machine(
                (False,),
                initial_mode="stop",
                escalated_mode="stop",
            )
        with self.assertRaises(ValueError):
            fallback_state_machine(
                (False, True),
                initial_mode="stop",
                escalated_mode="operator",
                reactivation_authorized_sequence=(True,),
            )
        with self.assertRaises(ValueError):
            fallback_state_machine(
                (False,),
                initial_mode="stop",
                escalated_mode="operator",
                reactivation_authorized_sequence=(1,),  # type: ignore[arg-type]
            )

    def test_gate_health_does_not_authorize_policy_reactivation(self):
        audit = fallback_reactivation_audit()
        health_only = audit["health_only_negative_control"]["trace"]
        authorization_aware = audit["authorization_aware"]["trace"]
        self.assertEqual(health_only[5]["mode"], "policy_action")
        self.assertEqual(authorization_aware[5]["mode"], "request_operator")
        self.assertEqual(
            authorization_aware[5]["recovery_blocked_reason"],
            "reactivation_not_authorized",
        )
        self.assertEqual(authorization_aware[6]["mode"], "policy_action")

    def test_fallback_completion_does_not_authorize_reactivation(self):
        success = fallback_lifecycle_audit()["success_then_authorize"]["trace"]
        self.assertEqual(success[2]["effective_state"], "succeeded")
        self.assertFalse(success[2]["reactivation_allowed"])
        self.assertEqual(success[2]["blocked_reason"], "reactivation_not_authorized")
        self.assertTrue(success[3]["reactivation_allowed"])

    def test_premature_authorization_and_timeout_fail_closed(self):
        timeout = fallback_lifecycle_audit()["premature_authorization_then_timeout"]["trace"]
        self.assertEqual(timeout[1]["blocked_reason"], "fallback_not_succeeded")
        self.assertEqual(timeout[2]["blocked_reason"], "fallback_not_succeeded")
        self.assertEqual(timeout[3]["effective_state"], "failed")
        self.assertEqual(timeout[3]["failure_reason"], "fallback_timeout")
        self.assertEqual(timeout[3]["blocked_reason"], "fallback_failed")
        self.assertFalse(timeout[3]["reactivation_allowed"])
        late = fallback_lifecycle_audit()["timeout_then_late_success"]
        self.assertEqual(late["trace"][2]["failure_reason"], "fallback_timeout")
        self.assertEqual(late["trace"][3]["reported_state"], "succeeded")
        self.assertEqual(late["trace"][3]["effective_state"], "failed")
        self.assertEqual(late["trace"][3]["blocked_reason"], "fallback_failed")
        self.assertEqual(late["reactivation_count"], 0)

    def test_reported_fallback_failure_cannot_reactivate(self):
        failed = fallback_lifecycle_audit()["reported_failure"]
        self.assertEqual(failed["reactivation_count"], 0)
        self.assertEqual(failed["trace"][2]["failure_reason"], "fallback_reported_failed")
        self.assertEqual(failed["trace"][3]["blocked_reason"], "fallback_failed")

    def test_fallback_lifecycle_rejects_ambiguous_contracts(self):
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(("operating",), (False,), max_operating_steps=1)
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(
                ("requested", "succeeded"),
                (False, True),
                max_operating_steps=1,
            )
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(("requested",), (), max_operating_steps=1)
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(("requested",), (False,), max_operating_steps=True)
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(
                ("requested", "unknown"),
                (False, False),
                max_operating_steps=1,
            )
        with self.assertRaises(ValueError):
            audit_fallback_lifecycle(
                ("requested",),
                (1,),  # type: ignore[arg-type]
                max_operating_steps=1,
            )

    def test_valid_reactivation_receipt_is_single_use(self):
        audit = reactivation_receipt_audit()
        self.assertEqual(audit["allowed_count"], 1)
        self.assertEqual(audit["rejected_count"], 8)
        self.assertEqual(audit["cases"]["valid"], ())
        self.assertEqual(
            audit["cases"]["replayed"],
            ("replay_or_out_of_order_receipt", "receipt_already_consumed"),
        )

    def test_reactivation_receipt_binds_run_target_and_declared_approver(self):
        cases = reactivation_receipt_audit()["cases"]
        self.assertEqual(cases["wrong_run"], ("fallback_run_mismatch",))
        self.assertEqual(cases["wrong_target"], ("target_mode_mismatch",))
        self.assertEqual(cases["unauthorized_approver"], ("unauthorized_approver",))

    def test_reactivation_receipt_rejects_time_decision_and_order_failures(self):
        cases = reactivation_receipt_audit()["cases"]
        self.assertEqual(cases["expired"], ("stale_or_future_receipt_time",))
        self.assertEqual(cases["future"], ("stale_or_future_receipt_time",))
        self.assertEqual(cases["denied"], ("reactivation_not_approved",))
        self.assertEqual(cases["out_of_order"], ("replay_or_out_of_order_receipt",))

    def test_reactivation_receipt_rejects_ambiguous_contracts(self):
        receipt = ReactivationReceipt("r", "a", "run", "policy_action", 0, 2, 1, "approved")
        common = {
            "now_step": 1,
            "expected_fallback_run_id": "run",
            "expected_target_mode": "policy_action",
            "authorized_approver_ids": frozenset({"a"}),
        }
        self.assertEqual(
            validate_reactivation_receipt("not-a-receipt", **common),  # type: ignore[arg-type]
            ("invalid_reactivation_receipt",),
        )
        malformed = ReactivationReceipt("", "", "", "", True, 0, True, "")
        issues = validate_reactivation_receipt(malformed, **common)
        self.assertIn("invalid_receipt_id", issues)
        self.assertIn("invalid_receipt_validity_interval", issues)
        self.assertIn("invalid_receipt_sequence", issues)
        with self.assertRaises(ValueError):
            validate_reactivation_receipt(receipt, **{**common, "now_step": True})
        with self.assertRaises(ValueError):
            validate_reactivation_receipt(
                receipt,
                **{**common, "authorized_approver_ids": frozenset()},
            )

    def test_healthy_packet_is_allowed(self):
        packet = ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5, 0.2, "fixture-v1")
        decision = gate(packet, GateConfig())
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["selected_mode"], "policy_action")

    def test_stale_late_and_expired_packets_are_rejected(self):
        config = GateConfig()
        fixtures = (
            (ActionPacket(120.0, 25.0, (0.2,), 2, 5, 0.2, "fixture-v1"), "stale_observation"),
            (ActionPacket(20.0, 80.0, (0.2,), 2, 5, 0.2, "fixture-v1"), "deadline_miss"),
            (ActionPacket(20.0, 25.0, (0.2,), 5, 5, 0.2, "fixture-v1"), "action_chunk_expired"),
        )
        for packet, reason in fixtures:
            with self.subTest(reason=reason):
                self.assertIn(reason, gate(packet, config)["reasons"])

    def test_invalid_and_out_of_bounds_actions_are_rejected(self):
        config = GateConfig()
        invalid = gate(ActionPacket(20.0, 25.0, (float("nan"),), 2, 5, 0.2, "fixture-v1"), config)
        bounded = gate(ActionPacket(20.0, 25.0, (1.2,), 2, 5, 0.2, "fixture-v1"), config)
        self.assertIn("invalid_action", invalid["reasons"])
        self.assertIn("action_out_of_bounds", bounded["reasons"])

    def test_fallback_is_not_hard_coded(self):
        packet = ActionPacket(120.0, 25.0, (0.2,), 2, 5, 0.2, "fixture-v1")
        decision = gate(packet, GateConfig(fallback="request_minimum_risk_maneuver"))
        self.assertEqual(decision["selected_mode"], "request_minimum_risk_maneuver")

    def test_invalid_config_and_latency_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            GateConfig(deadline_ms=True)
        with self.assertRaises(ValueError):
            latency_summary((20.0, float("inf")), 50.0)
        with self.assertRaises(ValueError):
            nearest_rank((20.0,), 0.0)
        with self.assertRaises(ValueError):
            GateConfig(uncertainty_revision="")

    def test_uncertainty_score_has_distinct_gate_reasons(self):
        uncertain = gate(
            ActionPacket(20.0, 25.0, (0.2,), 2, 5, 0.9, "fixture-v1"), GateConfig()
        )
        invalid = gate(
            ActionPacket(20.0, 25.0, (0.2,), 2, 5, float("nan"), "fixture-v1"), GateConfig()
        )
        mismatch = gate(
            ActionPacket(20.0, 25.0, (0.2,), 2, 5, 0.2, "old-v0"), GateConfig()
        )
        self.assertEqual(uncertain["reasons"], ["uncertainty_exceeds_limit"])
        self.assertEqual(invalid["reasons"], ["invalid_uncertainty_score"])
        self.assertEqual(mismatch["reasons"], ["uncertainty_revision_mismatch"])

    def test_selective_metrics_expose_risk_coverage_tradeoff(self):
        cases = ((0.1, False), (0.2, False), (0.3, False), (0.6, True), (0.8, True), (0.9, True))
        strict = selective_metrics(cases, 0.5)
        permissive = selective_metrics(cases, 0.7)
        self.assertEqual(strict["coverage"], 0.5)
        self.assertEqual(strict["accepted_failure_rate"], 0.0)
        self.assertEqual(permissive["coverage"], 0.666667)
        self.assertEqual(permissive["accepted_failure_rate"], 0.25)
        self.assertIsNone(selective_metrics(((0.1, False),), 0.0)["accepted_failure_rate"])
        with self.assertRaises(ValueError):
            selective_metrics(((float("nan"), False),), 0.5)

    def test_evaluation_exposes_each_expected_failure(self):
        result = evaluate()
        self.assertEqual(result["allowed_count"], 1)
        self.assertEqual(result["fallback_count"], 6)
        self.assertTrue(all(count == 1 for count in result["reason_counts"].values()))


if __name__ == "__main__":
    unittest.main()
