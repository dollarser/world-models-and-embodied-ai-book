from pathlib import Path
import copy
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from project_audit import (  # noqa: E402
    INVALID_DRIVING_PACKAGE,
    VALID_DRIVING_PACKAGE,
    audit_project,
    evaluate,
)


class ProjectAuditTests(unittest.TestCase):
    def test_valid_project_is_accepted(self):
        self.assertEqual(audit_project(VALID_DRIVING_PACKAGE), [])
        self.assertTrue(evaluate()["valid_package"]["accepted"])

    def test_invalid_project_exposes_all_fixed_issues(self):
        result = evaluate()["invalid_package"]
        self.assertFalse(result["accepted"])
        self.assertEqual(result["issue_count"], 15)

    def test_group_overlap_is_rejected(self):
        self.assertIn("train_eval_group_overlap", audit_project(INVALID_DRIVING_PACKAGE))

    def test_missing_required_artifacts_are_named(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("missing_result", issues)
        self.assertIn("missing_failure_record", issues)
        self.assertIn("missing_reproduction_command", issues)

    def test_private_data_and_resource_excess_are_rejected(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("private_data_without_authorization", issues)
        self.assertIn("resource_limit_exceeded", issues)
        self.assertIn("gpu_result_unverified", issues)

    def test_driving_requires_metrics_and_safety_gateway(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("driving_metrics_incomplete", issues)
        self.assertIn("missing_safety_gateway", issues)

    def test_single_gpu_over_24gb_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["resources"] = {"tier": "L1", "gpu_count": 1, "vram_gb_each": 25, "gpu_verified": False}
        self.assertIn("resource_limit_exceeded", audit_project(package))

    def test_non_object_and_invalid_resource_types_are_rejected(self):
        self.assertEqual(audit_project([]), ["package_not_object"])
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["resources"] = {"tier": "S", "gpu_count": True, "vram_gb_each": 0, "gpu_verified": False}
        self.assertIn("invalid_resource_record", audit_project(package))


if __name__ == "__main__":
    unittest.main()
