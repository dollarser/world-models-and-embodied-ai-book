from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from data_audit import audit, bootstrap_allowed, describe_fixture, load_fixture  # noqa: E402


class DataAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = load_fixture(LAB_ROOT / "fixtures/valid-dataset.json")

    def test_valid_fixture_has_no_issues(self) -> None:
        self.assertEqual(audit(self.valid), [])

    def test_group_leakage_is_detected(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][1]["group_id"] = changed["episodes"][0]["group_id"]
        self.assertIn("group_split_overlap", {issue.code for issue in audit(changed)})

    def test_action_alignment_requires_nonfinal_action(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][0]["frames"][0]["action"] = None
        self.assertIn("missing_transition_action", {issue.code for issue in audit(changed)})

    def test_test_statistics_are_rejected(self) -> None:
        changed = deepcopy(self.valid)
        changed["dataset"]["normalization_scope"] = "all"
        self.assertIn("normalization_scope", {issue.code for issue in audit(changed)})

    def test_non_numeric_action_is_reported_instead_of_crashing(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][0]["frames"][0]["action"] = "left"
        self.assertIn("invalid_action_type", {issue.code for issue in audit(changed)})

    def test_termination_and_truncation_have_distinct_bootstrap_semantics(self) -> None:
        terminated_final = self.valid["episodes"][0]["frames"][-1]
        truncated_final = self.valid["episodes"][1]["frames"][-1]
        self.assertFalse(bootstrap_allowed(terminated_final))
        self.assertTrue(bootstrap_allowed(truncated_final))

    def test_final_frame_requires_at_least_one_end_flag(self) -> None:
        missing = deepcopy(self.valid)
        missing_final = missing["episodes"][0]["frames"][-1]
        missing_final["terminated"] = False
        missing_final["truncated"] = False
        self.assertIn("missing_episode_end", {issue.code for issue in audit(missing)})

    def test_simultaneous_terminal_and_time_limit_is_valid_and_terminal_dominates_bootstrap(self) -> None:
        changed = deepcopy(self.valid)
        final = changed["episodes"][0]["frames"][-1]
        final["terminated"] = True
        final["truncated"] = True
        self.assertEqual(audit(changed), [])
        self.assertFalse(bootstrap_allowed(final))

    def test_nonfinal_end_flag_is_rejected(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][0]["frames"][0]["truncated"] = True
        self.assertIn("early_episode_end", {issue.code for issue in audit(changed)})

    def test_explicit_missing_sensor_mask_is_valid(self) -> None:
        codes = {issue.code for issue in audit(self.valid)}
        self.assertNotIn("missing_sensor_record", codes)
        self.assertEqual(describe_fixture(self.valid)["masked_sensor_sample_count"], 1)

    def test_missing_sensor_record_requires_explicit_mask(self) -> None:
        changed = deepcopy(self.valid)
        del changed["episodes"][0]["frames"][1]["sensors"]["wrist_camera"]
        self.assertIn("missing_sensor_record", {issue.code for issue in audit(changed)})

    def test_sensor_skew_exceeding_contract_is_rejected(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][0]["frames"][1]["sensors"]["front_camera"]["timestamp"] = 0.15
        self.assertIn("sensor_sync_skew", {issue.code for issue in audit(changed)})

    def test_sensor_timestamp_must_be_monotonic(self) -> None:
        changed = deepcopy(self.valid)
        changed["episodes"][0]["frames"][1]["sensors"]["wrist_camera"]["timestamp"] = 0.0
        self.assertIn("nonmonotonic_sensor_timestamp", {issue.code for issue in audit(changed)})

    def test_nonfinite_action_and_sensor_timestamp_are_rejected(self) -> None:
        action_changed = deepcopy(self.valid)
        action_changed["episodes"][0]["frames"][0]["action"] = float("nan")
        self.assertIn("nonfinite_action", {issue.code for issue in audit(action_changed)})

        sensor_changed = deepcopy(self.valid)
        sensor_changed["episodes"][0]["frames"][0]["sensors"]["front_camera"]["timestamp"] = float("inf")
        self.assertIn("invalid_sensor_timestamp", {issue.code for issue in audit(sensor_changed)})


if __name__ == "__main__":
    unittest.main()
