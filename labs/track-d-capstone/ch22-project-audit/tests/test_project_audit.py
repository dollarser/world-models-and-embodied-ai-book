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
        binding = VALID_DRIVING_PACKAGE["artifacts"]["reproduction_command"]
        self.assertEqual(binding["uri"], "commands/reproduce.txt")
        self.assertEqual(
            VALID_DRIVING_PACKAGE["artifact_payloads"][binding["uri"]],
            "make ch22-smoke",
        )

    def test_invalid_project_exposes_all_fixed_issues(self):
        result = evaluate()["invalid_package"]
        self.assertFalse(result["accepted"])
        self.assertEqual(result["issue_count"], 20)

    def test_valid_project_has_five_stage_traceability(self):
        self.assertEqual(evaluate()["required_trace_stage_count"], 5)
        self.assertEqual(
            set(VALID_DRIVING_PACKAGE["traceability"]),
            {
                "input_contract",
                "method_contract",
                "independent_evaluation",
                "deployment_or_safety_gate",
                "evidence_package",
            },
        )

    def test_missing_traceability_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        del package["traceability"]["independent_evaluation"]
        self.assertIn("traceability_incomplete", audit_project(package))

    def test_malformed_trace_stage_or_dependency_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["traceability"]["method_contract"]["chapter"] = 20
        package["traceability"]["method_contract"]["depends_on"] = []
        self.assertIn("invalid_trace_stage:method_contract", audit_project(package))

    def test_trace_artifact_chapter_and_revision_are_bound(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["traceability"]["independent_evaluation"]["artifact"] = "BENCH-19-01"
        package["traceability"]["input_contract"]["revision"] = ""
        issues = audit_project(package)
        self.assertIn("invalid_trace_stage:independent_evaluation", issues)
        self.assertIn("invalid_trace_stage:input_contract", issues)

    def test_group_overlap_is_rejected(self):
        self.assertIn("train_eval_group_overlap", audit_project(INVALID_DRIVING_PACKAGE))

    def test_selection_eval_overlap_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["split"]["selection_groups"] = ["route-c"]
        self.assertIn("selection_eval_group_overlap", audit_project(package))

    def test_missing_required_artifacts_are_named(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("missing_result", issues)
        self.assertIn("missing_failure_record", issues)
        self.assertIn("missing_reproduction_command", issues)

    def test_private_data_and_resource_excess_are_rejected(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("private_data_without_authorization", issues)
        self.assertIn("resource_tier_mismatch", issues)
        self.assertIn("gpu_result_unverified", issues)

    def test_driving_requires_metrics_and_safety_gateway(self):
        issues = audit_project(INVALID_DRIVING_PACKAGE)
        self.assertIn("driving_metrics_incomplete", issues)
        self.assertIn("missing_safety_gateway", issues)

    def test_single_gpu_over_24gb_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["resources"] = {"tier": "L1", "gpu_count": 1, "vram_gb_each": 25, "gpu_verified": False}
        self.assertIn("resource_tier_mismatch", audit_project(package))

    def test_resource_tiers_enforce_the_declared_hardware_envelope(self):
        for resources, expected_issue in (
            ({"tier": "L2", "gpu_count": 1, "vram_gb_each": 80, "gpu_verified": False}, None),
            ({"tier": "L2", "gpu_count": 2, "vram_gb_each": 80, "gpu_verified": False}, None),
            ({"tier": "S", "gpu_count": 1, "vram_gb_each": 24, "gpu_verified": False}, "resource_tier_mismatch"),
        ):
            package = copy.deepcopy(VALID_DRIVING_PACKAGE)
            package["resources"] = resources
            issues = audit_project(package)
            with self.subTest(resources=resources):
                if expected_issue is None:
                    self.assertNotIn("resource_tier_mismatch", issues)
                else:
                    self.assertIn(expected_issue, issues)

    def test_non_object_and_invalid_resource_types_are_rejected(self):
        self.assertEqual(audit_project([]), ["package_not_object"])
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["resources"] = {"tier": "S", "gpu_count": True, "vram_gb_each": 0, "gpu_verified": False}
        self.assertIn("invalid_resource_record", audit_project(package))

    def test_non_finite_and_inconsistent_gpu_records_are_rejected(self):
        for resources in (
            {"tier": "S", "gpu_count": 0, "vram_gb_each": float("nan"), "gpu_verified": False},
            {"tier": "S", "gpu_count": 0, "vram_gb_each": 24, "gpu_verified": False},
            {"tier": "L1", "gpu_count": 1, "vram_gb_each": 0, "gpu_verified": False},
        ):
            package = copy.deepcopy(VALID_DRIVING_PACKAGE)
            package["resources"] = resources
            with self.subTest(resources=resources):
                self.assertIn("invalid_resource_record", audit_project(package))

    def test_artifact_payload_tampering_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["artifact_payloads"]["results.json"] = "tampered result"
        self.assertIn("artifact_digest_mismatch:result", audit_project(package))

    def test_artifact_binding_requires_exact_claim_and_producer(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["artifacts"]["model_card"]["producer_stage"] = "evidence_package"
        package["artifacts"]["model_card"]["claim_ids"] = ["claim-22"]
        self.assertIn("invalid_artifact_binding:model_card", audit_project(package))

    def test_evaluation_protocol_and_trace_must_be_frozen_and_bound(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["evaluation"]["protocol_frozen_before_evaluation"] = False
        package["evaluation"]["evaluator_artifact"] = "BENCH-19-01"
        issues = audit_project(package)
        self.assertIn("evaluation_protocol_not_frozen", issues)
        self.assertIn("evaluation_trace_mismatch", issues)

    def test_boolean_or_unbound_safety_gateway_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["safety_gateway"] = True
        self.assertIn("missing_safety_gateway", audit_project(package))

        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["safety_gateway"]["trace_artifact"] = "EXP-20-01"
        self.assertIn("missing_safety_gateway", audit_project(package))

    def test_unobserved_failure_injection_is_rejected(self):
        package = copy.deepcopy(VALID_DRIVING_PACKAGE)
        package["failure_injections"][0]["observed_issue"] = "no_issue"
        self.assertIn("unverified_failure_injection", audit_project(package))


if __name__ == "__main__":
    unittest.main()
