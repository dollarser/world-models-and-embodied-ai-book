from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from deployment_gate import (  # noqa: E402
    ActionPacket,
    GateConfig,
    LATENCIES_MS,
    evaluate,
    gate,
    latency_summary,
    nearest_rank,
)


class DeploymentGateTests(unittest.TestCase):
    def test_mean_can_pass_while_tail_misses_deadline(self):
        result = latency_summary(LATENCIES_MS, 50.0)
        self.assertEqual(result["mean_ms"], 45.0)
        self.assertEqual(result["p95_ms"], 150.0)
        self.assertTrue(result["mean_passes_deadline"])
        self.assertFalse(result["all_cycles_meet_deadline"])

    def test_healthy_packet_is_allowed(self):
        decision = gate(ActionPacket(20.0, 25.0, (0.2, -0.1), 2, 5), GateConfig())
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["selected_mode"], "policy_action")

    def test_stale_late_and_expired_packets_are_rejected(self):
        config = GateConfig()
        fixtures = (
            (ActionPacket(120.0, 25.0, (0.2,), 2, 5), "stale_observation"),
            (ActionPacket(20.0, 80.0, (0.2,), 2, 5), "deadline_miss"),
            (ActionPacket(20.0, 25.0, (0.2,), 5, 5), "action_chunk_expired"),
        )
        for packet, reason in fixtures:
            with self.subTest(reason=reason):
                self.assertIn(reason, gate(packet, config)["reasons"])

    def test_invalid_and_out_of_bounds_actions_are_rejected(self):
        config = GateConfig()
        invalid = gate(ActionPacket(20.0, 25.0, (float("nan"),), 2, 5), config)
        bounded = gate(ActionPacket(20.0, 25.0, (1.2,), 2, 5), config)
        self.assertIn("invalid_action", invalid["reasons"])
        self.assertIn("action_out_of_bounds", bounded["reasons"])

    def test_fallback_is_not_hard_coded(self):
        packet = ActionPacket(120.0, 25.0, (0.2,), 2, 5)
        decision = gate(packet, GateConfig(fallback="request_minimum_risk_maneuver"))
        self.assertEqual(decision["selected_mode"], "request_minimum_risk_maneuver")

    def test_invalid_config_and_latency_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            GateConfig(deadline_ms=True)
        with self.assertRaises(ValueError):
            latency_summary((20.0, float("inf")), 50.0)
        with self.assertRaises(ValueError):
            nearest_rank((20.0,), 0.0)

    def test_evaluation_exposes_each_expected_failure(self):
        result = evaluate()
        self.assertEqual(result["allowed_count"], 1)
        self.assertEqual(result["fallback_count"], 5)
        self.assertTrue(all(count == 1 for count in result["reason_counts"].values()))


if __name__ == "__main__":
    unittest.main()
