"""Project-package audit fixture for Chapter 22."""

from __future__ import annotations

from math import isfinite


REQUIRED_ARTIFACTS = (
    "experiment_card",
    "result",
    "failure_record",
    "reproduction_command",
    "model_card",
)
DRIVING_METRICS = {"route_completion", "collision_rate", "intervention_rate"}
ALLOWED_TIERS = {"S", "M", "L1", "L2"}


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _string_set(value: object) -> set[str]:
    if not isinstance(value, (list, tuple)):
        return set()
    return {item for item in value if isinstance(item, str) and item}


def audit_project(package: object) -> list[str]:
    if not isinstance(package, dict):
        return ["package_not_object"]
    issues = []
    if not isinstance(package.get("research_question"), str) or not package["research_question"].strip():
        issues.append("missing_research_question")
    if not isinstance(package.get("claim_id"), str) or not package["claim_id"].startswith("CLAIM-"):
        issues.append("missing_claim_id")

    data = _dict(package.get("data"))
    if not isinstance(data.get("license"), str) or not data["license"].strip():
        issues.append("missing_data_license")
    if data.get("classification") == "private" and data.get("authorized") is not True:
        issues.append("private_data_without_authorization")

    split = _dict(package.get("split"))
    train_groups = _string_set(split.get("train_groups"))
    eval_groups = _string_set(split.get("eval_groups"))
    if not train_groups or not eval_groups:
        issues.append("missing_group_split")
    elif train_groups & eval_groups:
        issues.append("train_eval_group_overlap")

    artifacts = _dict(package.get("artifacts"))
    for artifact in REQUIRED_ARTIFACTS:
        if not isinstance(artifacts.get(artifact), str) or not artifacts[artifact].strip():
            issues.append(f"missing_{artifact}")

    failure_injections = _string_set(package.get("failure_injections"))
    if not failure_injections:
        issues.append("missing_failure_injection")
    limitations = _string_set(package.get("known_limitations"))
    if not limitations:
        issues.append("missing_known_limitations")

    resources = _dict(package.get("resources"))
    tier = resources.get("tier")
    gpu_count = resources.get("gpu_count")
    vram_gb_each = resources.get("vram_gb_each")
    if tier not in ALLOWED_TIERS:
        issues.append("invalid_resource_tier")
    if (
        isinstance(gpu_count, bool)
        or not isinstance(gpu_count, int)
        or gpu_count < 0
        or isinstance(vram_gb_each, bool)
        or not isinstance(vram_gb_each, (int, float))
        or not isfinite(vram_gb_each)
        or vram_gb_each < 0
        or (gpu_count == 0 and vram_gb_each != 0)
        or (gpu_count > 0 and vram_gb_each == 0)
    ):
        issues.append("invalid_resource_record")
    elif gpu_count > 2 or (gpu_count == 1 and vram_gb_each > 24) or (gpu_count == 2 and vram_gb_each > 80):
        issues.append("resource_limit_exceeded")
    if package.get("claims_gpu_result") is True and resources.get("gpu_verified") is not True:
        issues.append("gpu_result_unverified")

    evaluation = _dict(package.get("evaluation"))
    if evaluation.get("independent_from_training") is not True:
        issues.append("evaluation_not_independent")
    metrics = _string_set(evaluation.get("metrics"))
    if not metrics:
        issues.append("missing_evaluation_metrics")
    if package.get("domain") == "automatic_driving":
        if not DRIVING_METRICS <= metrics:
            issues.append("driving_metrics_incomplete")
        if package.get("safety_gateway") is not True:
            issues.append("missing_safety_gateway")
    return issues


VALID_DRIVING_PACKAGE = {
    "research_question": "Does replanning reduce fixed-disturbance route failure under a frozen protocol?",
    "claim_id": "CLAIM-22-02",
    "domain": "automatic_driving",
    "data": {"classification": "fixture", "license": "MIT", "authorized": True},
    "split": {"train_groups": ["route-a", "route-b"], "eval_groups": ["route-c"]},
    "artifacts": {
        "experiment_card": "experiment-card.json",
        "result": "results.json",
        "failure_record": "failures.md",
        "reproduction_command": "make capstone-smoke",
        "model_card": "model-card.md",
    },
    "failure_injections": ["stale_observation", "fixed_disturbance"],
    "known_limitations": ["scalar fixture", "no vehicle"],
    "resources": {"tier": "S", "gpu_count": 0, "vram_gb_each": 0, "gpu_verified": False},
    "claims_gpu_result": False,
    "evaluation": {
        "independent_from_training": True,
        "metrics": ["route_completion", "collision_rate", "intervention_rate", "deadline_miss_rate"],
    },
    "safety_gateway": True,
}


INVALID_DRIVING_PACKAGE = {
    "research_question": "",
    "claim_id": "claim-22",
    "domain": "automatic_driving",
    "data": {"classification": "private", "license": "", "authorized": False},
    "split": {"train_groups": ["same-route"], "eval_groups": ["same-route"]},
    "artifacts": {"experiment_card": "experiment-card.json", "model_card": "model-card.md"},
    "failure_injections": [],
    "known_limitations": [],
    "resources": {"tier": "L2", "gpu_count": 3, "vram_gb_each": 80, "gpu_verified": False},
    "claims_gpu_result": True,
    "evaluation": {"independent_from_training": False, "metrics": ["success_rate"]},
    "safety_gateway": False,
}


def evaluate() -> dict[str, object]:
    valid_issues = audit_project(VALID_DRIVING_PACKAGE)
    invalid_issues = audit_project(INVALID_DRIVING_PACKAGE)
    return {
        "valid_package": {"issue_count": len(valid_issues), "issues": valid_issues, "accepted": not valid_issues},
        "invalid_package": {
            "issue_count": len(invalid_issues),
            "issues": invalid_issues,
            "accepted": not invalid_issues,
        },
        "required_artifact_count": len(REQUIRED_ARTIFACTS),
        "driving_metric_count": len(DRIVING_METRICS),
    }
