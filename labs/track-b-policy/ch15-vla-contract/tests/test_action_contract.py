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

    def test_token_round_trip_has_explicit_quantization(self):
        tokens = encode_tokens((0.6, -0.4), bins=5)
        self.assertEqual(tokens, (3, 1))
        self.assertEqual(decode_tokens(tokens, bins=5), (0.5, -0.5))

    def test_token_decoder_rejects_invalid_vocabulary_item(self):
        with self.assertRaises(ValueError):
            decode_tokens((5,), bins=5)

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
        self.assertIn("frame_mismatch", validate_packet({**base, "frame_id": "camera"}))
        self.assertIn("unit_mismatch", validate_packet({**base, "units": ("km/h", "deg/s")}))
        self.assertIn("out_of_bounds:linear_velocity", validate_packet(make_packet("continuous", ((0.8, 0.0),))))


if __name__ == "__main__":
    unittest.main()
