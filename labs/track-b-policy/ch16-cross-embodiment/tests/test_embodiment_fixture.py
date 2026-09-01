from pathlib import Path
import math
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from embodiment_fixture import (  # noqa: E402
    ADAPTERS,
    EmbodimentAdapter,
    canonicalize,
    evaluate,
    mean_action,
    maximum_round_trip_error,
    mixture_exposure_report,
    naive_raw_pooling_error,
    schema_aware_pooling_error,
    window_exposure_report,
)


class EmbodimentAdapterTests(unittest.TestCase):
    def test_arm_a_uses_controller_delta_and_positive_gripper(self):
        self.assertEqual(ADAPTERS["arm_a"].to_canonical((0.2, 1.0)), (0.020000000000000004, 1.0))

    def test_arm_b_uses_centimeters_and_reversed_gripper(self):
        self.assertEqual(ADAPTERS["arm_b"].to_canonical((2.0, -1.0)), (0.02, 1.0))

    def test_each_adapter_round_trips_its_own_convention(self):
        self.assertAlmostEqual(maximum_round_trip_error(), 0.0)

    def test_naive_raw_pooling_changes_semantics(self):
        self.assertAlmostEqual(naive_raw_pooling_error(), 0.28375)

    def test_schema_aware_pooling_aligns_targets(self):
        self.assertAlmostEqual(schema_aware_pooling_error(), 0.0)

    def test_missing_embodiment_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            canonicalize({"episode_id": "x", "task": "forward_open", "raw_action": (0.2, 1.0)})

    def test_missing_or_stale_adapter_fingerprint_is_rejected(self):
        for fingerprint in (None, "sha256:" + "0" * 64):
            record = {
                "episode_id": "x",
                "task": "forward_open",
                "embodiment_id": "arm_a",
                "raw_action": (0.2, 1.0),
            }
            if fingerprint is not None:
                record["adapter_schema_fingerprint"] = fingerprint
            with self.subTest(fingerprint=fingerprint), self.assertRaises(ValueError):
                canonicalize(record)

    def test_semantic_adapter_change_changes_fingerprint(self):
        changed_scale = EmbodimentAdapter("arm_a", "controller_delta", 0.01, 1)
        changed_fields = EmbodimentAdapter(
            "arm_a", "controller_delta", 0.1, 1, raw_action_fields=("gripper", "delta_x")
        )
        self.assertNotEqual(changed_scale.schema_fingerprint, ADAPTERS["arm_a"].schema_fingerprint)
        self.assertNotEqual(changed_fields.schema_fingerprint, ADAPTERS["arm_a"].schema_fingerprint)

    def test_non_dictionary_record_is_rejected(self):
        with self.assertRaises(ValueError):
            canonicalize(("arm_a", (0.2, 1.0)))

    def test_gripper_ranges_are_validated(self):
        with self.assertRaises(ValueError):
            ADAPTERS["arm_a"].to_canonical((0.0, 2.0))
        with self.assertRaises(ValueError):
            ADAPTERS["arm_a"].from_canonical((0.0, -0.1))

    def test_non_finite_boolean_and_malformed_actions_are_rejected(self):
        invalid_actions = ((True, 0.0), (math.nan, 0.0), (math.inf, 0.0), (0.0,))
        for action in invalid_actions:
            with self.subTest(action=action), self.assertRaises(ValueError):
                ADAPTERS["arm_a"].to_canonical(action)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            mean_action(())

    def test_invalid_adapter_metadata_is_rejected(self):
        invalid_configs = (
            {"embodiment_id": "", "delta_x_unit": "m", "delta_x_scale_to_m": 1.0, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": 0.0, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": math.inf, "gripper_polarity": 1},
            {"embodiment_id": "x", "delta_x_unit": "m", "delta_x_scale_to_m": 1.0, "gripper_polarity": True},
            {
                "embodiment_id": "x",
                "delta_x_unit": "m",
                "delta_x_scale_to_m": 1.0,
                "gripper_polarity": 1,
                "raw_action_fields": ("action", "action"),
            },
        )
        for config in invalid_configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                EmbodimentAdapter(**config)  # type: ignore[arg-type]

    def test_sampling_unit_changes_dataset_exposure(self):
        report = mixture_exposure_report({"short_dataset": (2,), "long_dataset": (4, 4, 4)})
        self.assertEqual(report["dataset_uniform_exposure"], {"long_dataset": 0.5, "short_dataset": 0.5})
        self.assertEqual(report["episode_uniform_exposure"], {"long_dataset": 0.75, "short_dataset": 0.25})
        self.assertEqual(
            report["transition_uniform_exposure"],
            {"long_dataset": 0.857142857143, "short_dataset": 0.142857142857},
        )

    def test_mixture_report_keeps_all_three_denominators_explicit(self):
        report = mixture_exposure_report({"short_dataset": (2,), "long_dataset": (4, 4, 4)})
        self.assertEqual(report["dataset_count"], 2)
        self.assertEqual(report["episode_count"], 4)
        self.assertEqual(report["transition_count"], 14)
        self.assertEqual(report["episode_counts_by_dataset"], {"long_dataset": 3, "short_dataset": 1})
        self.assertEqual(report["transition_counts_by_dataset"], {"long_dataset": 12, "short_dataset": 2})

    def test_invalid_mixture_lengths_are_rejected(self):
        invalid_mixtures = ({}, {"": (1,)}, {"a": ()}, {"a": (True,)}, {"a": (0,)})
        for mixture in invalid_mixtures:
            with self.subTest(mixture=mixture), self.assertRaises(ValueError):
                mixture_exposure_report(mixture)

    def test_action_horizon_changes_realized_source_exposure(self):
        report = window_exposure_report(
            {"short_dataset": (2,), "long_dataset": (4, 4, 4)}, action_horizon=3
        )
        self.assertEqual(report["eligible_window_count"], 6)
        self.assertEqual(
            report["eligible_window_counts_by_dataset"],
            {"long_dataset": 6, "short_dataset": 0},
        )
        self.assertEqual(
            report["window_uniform_exposure"],
            {"long_dataset": 1.0, "short_dataset": 0.0},
        )

    def test_too_short_dataset_remains_visible_in_window_audit(self):
        report = window_exposure_report(
            {"short_dataset": (2,), "long_dataset": (4, 4, 4)}, action_horizon=3
        )
        self.assertEqual(report["datasets_without_eligible_windows"], ("short_dataset",))

    def test_invalid_or_unusable_action_horizons_are_rejected(self):
        for horizon in (True, 0, -1):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                window_exposure_report({"dataset": (2,)}, action_horizon=horizon)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            window_exposure_report({"dataset": (2,)}, action_horizon=3)

    def test_evaluate_registers_action_window_exposure_shift(self):
        metrics = evaluate()
        report = metrics["action_window_exposure"]
        self.assertEqual(report["action_horizon"], 3)
        self.assertEqual(report["window_uniform_exposure"]["long_dataset"], 1.0)


if __name__ == "__main__":
    unittest.main()
