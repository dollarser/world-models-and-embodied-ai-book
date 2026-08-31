from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from data_audit import audit, load_fixture  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
