from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from action_contract import (  # noqa: E402
    MOBILE_BASE_SCHEMA,
    decode_tokens,
    encode_tokens,
    make_packet,
    unnormalize_action,
    validate_packet,
)


class ActionContractTests(unittest.TestCase):
    def test_continuous_action_uses_schema_limits(self):
        decoded = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        self.assertAlmostEqual(decoded[0], 0.3)
        self.assertAlmostEqual(decoded[1], -0.4)

    def test_continuous_action_rejects_wrong_dimension_and_range(self):
        with self.assertRaises(ValueError):
            unnormalize_action((0.0,), MOBILE_BASE_SCHEMA)
        with self.assertRaises(ValueError):
            unnormalize_action((1.2, 0.0), MOBILE_BASE_SCHEMA)
        with self.assertRaises(ValueError):
            unnormalize_action((True, 0.0), MOBILE_BASE_SCHEMA)
        with self.assertRaises(ValueError):
            unnormalize_action((float("nan"), 0.0), MOBILE_BASE_SCHEMA)

    def test_token_round_trip_has_explicit_quantization(self):
        tokens = encode_tokens((0.6, -0.4), bins=5)
        self.assertEqual(tokens, (3, 1))
        self.assertEqual(decode_tokens(tokens, bins=5), (0.5, -0.5))

    def test_token_decoder_rejects_invalid_vocabulary_item(self):
        with self.assertRaises(ValueError):
            decode_tokens((5,), bins=5)
        with self.assertRaises(ValueError):
            decode_tokens((True,), bins=5)
        with self.assertRaises(ValueError):
            decode_tokens((1.5,), bins=5)

    def test_token_encoder_rejects_boolean_action(self):
        with self.assertRaises(ValueError):
            encode_tokens((True,), bins=5)
        with self.assertRaises(ValueError):
            encode_tokens((0.0,), bins=True)

    def test_valid_chunk_passes_and_preserves_receding_horizon(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("flow_chunk", (action, action, action))
        self.assertEqual(validate_packet(packet), tuple())
        self.assertEqual(packet["prediction_horizon"], 3)
        self.assertEqual(packet["execution_horizon"], 1)

    def test_high_level_text_is_not_directly_executable(self):
        issues = validate_packet(make_packet("high_level_text", tuple()))
        self.assertIn("non_executable_source", issues)
        self.assertIn("missing_action_values", issues)

    def test_gateway_rejects_stale_frame_unit_and_bounds_errors(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        base = make_packet("continuous", (action,))
        self.assertIn("stale_or_future_timestamp", validate_packet({**base, "timestamp_ms": 800}))
        self.assertIn("stale_or_future_timestamp", validate_packet({**base, "timestamp_ms": True}, now_ms=1))
        self.assertIn("frame_mismatch", validate_packet({**base, "frame_id": "camera"}))
        self.assertIn("unit_mismatch", validate_packet({**base, "units": ("km/h", "deg/s")}))
        self.assertIn("out_of_bounds:linear_velocity", validate_packet(make_packet("continuous", ((0.8, 0.0),))))
        self.assertIn("invalid_execution_horizon", validate_packet({**base, "execution_horizon": True}))

    def test_gateway_rejects_boolean_and_forged_horizon(self):
        boolean_action = make_packet("continuous", ((True, 0.0),))
        self.assertIn("out_of_bounds:linear_velocity", validate_packet(boolean_action))

        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        forged_horizon = {**make_packet("continuous", (action,)), "prediction_horizon": 3}
        self.assertIn("prediction_horizon_mismatch", validate_packet(forged_horizon))

    def test_packet_factory_includes_execution_identity(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,), command_id=11)
        self.assertEqual(packet["command_id"], 11)
        self.assertEqual(packet["clock_id"], "control_monotonic_ms")
        self.assertEqual(packet["field_names"], ("linear_velocity", "yaw_rate"))

    def test_packet_factory_binds_observation_and_action_timesteps(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,), observation_timestep=42, first_action_timestep=42)
        self.assertEqual(packet["observation_timestep"], 42)
        self.assertEqual(packet["first_action_timestep"], 42)

    def test_fresh_timestamp_does_not_hide_stale_observation_timestep(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,), timestamp_ms=990, observation_timestep=40)
        issues = validate_packet(packet, now_ms=1000, expected_observation_timestep=42)
        self.assertNotIn("stale_or_future_timestamp", issues)
        self.assertIn("observation_timestep_mismatch", issues)

    def test_gateway_rejects_wrong_first_action_timestep(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,), timestamp_ms=990, first_action_timestep=43)
        issues = validate_packet(packet, now_ms=1000, expected_first_action_timestep=42)
        self.assertNotIn("stale_or_future_timestamp", issues)
        self.assertIn("action_timestep_mismatch", issues)

    def test_gateway_prevents_execution_horizon_bypass(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("flow_chunk", (action, action, action))
        self.assertIn("execution_horizon_exceeded", validate_packet({**packet, "execution_horizon": 3}))

    def test_gateway_rejects_replay_and_out_of_order_commands(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        replay = make_packet("continuous", (action,), command_id=7)
        old = make_packet("continuous", (action,), command_id=6)
        new = make_packet("continuous", (action,), command_id=8)
        self.assertIn("replay_or_out_of_order_command", validate_packet(replay, last_accepted_command_id=7))
        self.assertIn("replay_or_out_of_order_command", validate_packet(old, last_accepted_command_id=7))
        self.assertEqual(validate_packet(new, last_accepted_command_id=7), tuple())

    def test_gateway_rejects_clock_and_field_order_mismatch(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,))
        self.assertIn("clock_mismatch", validate_packet({**packet, "clock_id": "wall_clock_ms"}))
        swapped = {**packet, "field_names": ("yaw_rate", "linear_velocity")}
        self.assertIn("field_order_mismatch", validate_packet(swapped))

    def test_gateway_rejects_non_mapping_packet_without_crashing(self):
        self.assertEqual(validate_packet(None), ("invalid_packet",))  # type: ignore[arg-type]

    def test_gateway_context_requires_monotonic_nonnegative_integers(self):
        action = unnormalize_action((0.6, -0.4), MOBILE_BASE_SCHEMA)
        packet = make_packet("continuous", (action,))
        with self.assertRaises(ValueError):
            validate_packet(packet, now_ms=True)
        with self.assertRaises(ValueError):
            validate_packet(packet, last_accepted_command_id=-1)
        with self.assertRaises(ValueError):
            validate_packet(packet, expected_observation_timestep=True)
        with self.assertRaises(ValueError):
            validate_packet(packet, expected_first_action_timestep=-1)


if __name__ == "__main__":
    unittest.main()
