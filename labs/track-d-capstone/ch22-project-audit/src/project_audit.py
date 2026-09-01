"""Project-package audit fixture for Chapter 22."""

from __future__ import annotations

from hashlib import sha256
from math import isfinite
import re


REQUIRED_ARTIFACTS = (
    "experiment_card",
    "result",
    "failure_record",
    "reproduction_command",
    "model_card",
)
REQUIRED_ARTIFACT_PRODUCERS = {
    "experiment_card": "evidence_package",
    "result": "independent_evaluation",
    "failure_record": "deployment_or_safety_gate",
    "reproduction_command": "evidence_package",
    "model_card": "method_contract",
}
DRIVING_METRICS = {"route_completion", "collision_rate", "intervention_rate"}
ALLOWED_TIERS = {"S", "M", "L1", "L2"}
SPLIT_IDENTITY_FIELDS = {
    "group_ids": "group",
    "source_asset_ids": "source_asset",
    "content_fingerprints": "content_fingerprint",
    "similarity_cluster_ids": "similarity_cluster",
}
SPLIT_PAIRS = (("train", "eval"), ("selection", "eval"), ("train", "selection"))
CLAIM_ID_PATTERN = re.compile(r"^CLAIM-[0-9]{2}-[0-9]{2}$")
TRACE_ARTIFACT_PATTERN = re.compile(r"^(?:EXP|BENCH)-([0-9]{2})-[0-9]{2}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
TRACE_STAGE_RULES = {
    "input_contract": {"chapters": {4}, "depends_on": set()},
    "method_contract": {"chapters": set(range(5, 19)), "depends_on": {"input_contract"}},
    "independent_evaluation": {
        "chapters": {9, 19, 20},
        "depends_on": {"input_contract", "method_contract"},
    },
    "deployment_or_safety_gate": {
        "chapters": {20, 21},
        "depends_on": {"input_contract", "method_contract"},
    },
    "evidence_package": {
        "chapters": {22},
        "depends_on": {
            "input_contract",
            "method_contract",
            "independent_evaluation",
            "deployment_or_safety_gate",
        },
    },
}


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _string_set(value: object) -> set[str]:
    if not isinstance(value, (list, tuple)):
        return set()
    return {item for item in value if isinstance(item, str) and item}


def _strict_string_set(value: object) -> set[str] | None:
    if not isinstance(value, (list, tuple)) or not value:
        return None
    if any(not isinstance(item, str) or not item for item in value):
        return None
    items = set(value)
    return items if len(items) == len(value) else None


def _artifact_binding(
    uri: str, payload: str, producer_stage: str, claim_id: str
) -> dict[str, object]:
    return {
        "uri": uri,
        "sha256": sha256(payload.encode("utf-8")).hexdigest(),
        "producer_stage": producer_stage,
        "claim_ids": [claim_id],
    }


def audit_project(package: object) -> list[str]:
    if not isinstance(package, dict):
        return ["package_not_object"]
    issues = []
    if not isinstance(package.get("research_question"), str) or not package["research_question"].strip():
        issues.append("missing_research_question")
    if not isinstance(package.get("claim_id"), str) or not CLAIM_ID_PATTERN.fullmatch(package["claim_id"]):
        issues.append("missing_claim_id")
    claim_id = package.get("claim_id") if isinstance(package.get("claim_id"), str) else ""

    data = _dict(package.get("data"))
    if not isinstance(data.get("license"), str) or not data["license"].strip():
        issues.append("missing_data_license")
    if data.get("classification") == "private" and data.get("authorized") is not True:
        issues.append("private_data_without_authorization")

    split = _dict(package.get("split"))
    split_identities: dict[str, dict[str, set[str]]] = {}
    for split_name in ("train", "selection", "eval"):
        partition = _dict(split.get(split_name))
        split_identities[split_name] = {}
        for field in SPLIT_IDENTITY_FIELDS:
            values = _strict_string_set(partition.get(field))
            if values is None:
                issues.append(f"missing_split_identity:{split_name}:{field}")
            else:
                split_identities[split_name][field] = values

    for left_split, right_split in SPLIT_PAIRS:
        for field, issue_label in SPLIT_IDENTITY_FIELDS.items():
            left_values = split_identities[left_split].get(field)
            right_values = split_identities[right_split].get(field)
            if left_values is not None and right_values is not None and left_values & right_values:
                issues.append(f"{left_split}_{right_split}_{issue_label}_overlap")

    artifacts = _dict(package.get("artifacts"))
    artifact_payloads = _dict(package.get("artifact_payloads"))
    for artifact in REQUIRED_ARTIFACTS:
        binding = _dict(artifacts.get(artifact))
        if not binding:
            issues.append(f"missing_{artifact}")
            continue
        uri = binding.get("uri")
        digest = binding.get("sha256")
        producer_stage = binding.get("producer_stage")
        artifact_claims = _strict_string_set(binding.get("claim_ids"))
        if (
            not isinstance(uri, str)
            or not uri
            or not isinstance(digest, str)
            or not SHA256_PATTERN.fullmatch(digest)
            or producer_stage != REQUIRED_ARTIFACT_PRODUCERS[artifact]
            or artifact_claims is None
            or any(not CLAIM_ID_PATTERN.fullmatch(item) for item in artifact_claims)
            or claim_id not in artifact_claims
        ):
            issues.append(f"invalid_artifact_binding:{artifact}")
            continue
        payload = artifact_payloads.get(uri)
        if not isinstance(payload, str):
            issues.append(f"artifact_payload_missing:{artifact}")
        elif sha256(payload.encode("utf-8")).hexdigest() != digest:
            issues.append(f"artifact_digest_mismatch:{artifact}")

    failure_injections = package.get("failure_injections")
    if not isinstance(failure_injections, (list, tuple)) or not failure_injections:
        issues.append("missing_failure_injection")
    elif any(
        not isinstance(injection, dict)
        or not isinstance(injection.get("name"), str)
        or not injection["name"]
        or not isinstance(injection.get("expected_issue"), str)
        or injection.get("observed_issue") != injection.get("expected_issue")
        or injection.get("trace_artifact") != "failure_record"
        for injection in failure_injections
    ):
        issues.append("unverified_failure_injection")
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
    elif (
        (tier in {"S", "M"} and gpu_count != 0)
        or (tier == "L1" and (gpu_count > 1 or vram_gb_each > 24))
        or (tier == "L2" and (gpu_count > 2 or vram_gb_each > 80))
    ):
        issues.append("resource_tier_mismatch")
    if package.get("claims_gpu_result") is True and resources.get("gpu_verified") is not True:
        issues.append("gpu_result_unverified")

    traceability = _dict(package.get("traceability"))
    required_trace_stages = set(TRACE_STAGE_RULES)
    if not required_trace_stages <= set(traceability):
        issues.append("traceability_incomplete")
    else:
        if set(traceability) - required_trace_stages:
            issues.append("traceability_unknown_stage")
        for stage_name, rule in TRACE_STAGE_RULES.items():
            stage = _dict(traceability.get(stage_name))
            chapter = stage.get("chapter")
            artifact = stage.get("artifact")
            revision = stage.get("revision")
            decision = stage.get("decision")
            dependencies = _string_set(stage.get("depends_on"))
            artifact_match = (
                TRACE_ARTIFACT_PATTERN.fullmatch(artifact) if isinstance(artifact, str) else None
            )
            if (
                isinstance(chapter, bool)
                or not isinstance(chapter, int)
                or chapter not in rule["chapters"]
                or artifact_match is None
                or int(artifact_match.group(1)) != chapter
                or not isinstance(revision, str)
                or not revision.strip()
                or not isinstance(decision, str)
                or not decision.strip()
                or dependencies != rule["depends_on"]
            ):
                issues.append(f"invalid_trace_stage:{stage_name}")

    evaluation = _dict(package.get("evaluation"))
    if evaluation.get("independent_from_training") is not True:
        issues.append("evaluation_not_independent")
    if evaluation.get("protocol_frozen_before_evaluation") is not True:
        issues.append("evaluation_protocol_not_frozen")
    independent_trace = _dict(traceability.get("independent_evaluation"))
    if evaluation.get("evaluator_artifact") != independent_trace.get("artifact"):
        issues.append("evaluation_trace_mismatch")
    metrics = _string_set(evaluation.get("metrics"))
    if not metrics:
        issues.append("missing_evaluation_metrics")
    if package.get("domain") == "automatic_driving":
        if not DRIVING_METRICS <= metrics:
            issues.append("driving_metrics_incomplete")
        gateway = _dict(package.get("safety_gateway"))
        deployment_trace = _dict(traceability.get("deployment_or_safety_gate"))
        if (
            gateway.get("enabled") is not True
            or gateway.get("trace_artifact") != deployment_trace.get("artifact")
            or gateway.get("failure_record") != "failure_record"
            or not _strict_string_set(gateway.get("fallback_modes"))
        ):
            issues.append("missing_safety_gateway")
    return issues


VALID_ARTIFACT_PAYLOADS = {
    "experiment-card.json": "fixture experiment card v4",
    "results.json": "fixture structured result v4",
    "failures.md": "stale_observation -> stale_observation\nfixed_disturbance -> route_failure",
    "commands/reproduce.txt": "make ch22-smoke",
    "model-card.md": "fixture model card: no model, no vehicle",
}


VALID_DRIVING_PACKAGE = {
    "research_question": "Does replanning reduce fixed-disturbance route failure under a frozen protocol?",
    "claim_id": "CLAIM-22-02",
    "domain": "automatic_driving",
    "data": {"classification": "fixture", "license": "MIT", "authorized": True},
    "split": {
        "train": {
            "group_ids": ["route-a", "route-b"],
            "source_asset_ids": ["raw-log-a", "raw-log-b"],
            "content_fingerprints": [
                "sha256:1ff0f379169d12474fb99e11470ed7357024591663a8b9a2d9531ee2d9949239",
                "sha256:1b394a54e6887abaf7ecc7ba24ea7e36882897b800e75c1525df1d36cfdd36be",
            ],
            "similarity_cluster_ids": ["cluster-a", "cluster-b"],
        },
        "selection": {
            "group_ids": ["route-selection"],
            "source_asset_ids": ["raw-log-selection"],
            "content_fingerprints": ["sha256:7c9ce945996e3f31d5da5dc5b0f737a41f045f506464d92dbc3228fdf1fca02c"],
            "similarity_cluster_ids": ["cluster-selection"],
        },
        "eval": {
            "group_ids": ["route-c"],
            "source_asset_ids": ["raw-log-c"],
            "content_fingerprints": ["sha256:c93aa394c014604f31954bee646795c9feec39c6cf0a73d1836aef3e0a66b822"],
            "similarity_cluster_ids": ["cluster-c"],
        },
    },
    "artifacts": {
        "experiment_card": _artifact_binding(
            "experiment-card.json", VALID_ARTIFACT_PAYLOADS["experiment-card.json"], "evidence_package", "CLAIM-22-02"
        ),
        "result": _artifact_binding(
            "results.json", VALID_ARTIFACT_PAYLOADS["results.json"], "independent_evaluation", "CLAIM-22-02"
        ),
        "failure_record": _artifact_binding(
            "failures.md", VALID_ARTIFACT_PAYLOADS["failures.md"], "deployment_or_safety_gate", "CLAIM-22-02"
        ),
        "reproduction_command": _artifact_binding(
            "commands/reproduce.txt", VALID_ARTIFACT_PAYLOADS["commands/reproduce.txt"], "evidence_package", "CLAIM-22-02"
        ),
        "model_card": _artifact_binding(
            "model-card.md", VALID_ARTIFACT_PAYLOADS["model-card.md"], "method_contract", "CLAIM-22-02"
        ),
    },
    "artifact_payloads": VALID_ARTIFACT_PAYLOADS,
    "failure_injections": [
        {
            "name": "stale_observation",
            "expected_issue": "stale_observation",
            "observed_issue": "stale_observation",
            "trace_artifact": "failure_record",
        },
        {
            "name": "fixed_disturbance",
            "expected_issue": "route_failure",
            "observed_issue": "route_failure",
            "trace_artifact": "failure_record",
        },
    ],
    "known_limitations": ["scalar fixture", "no vehicle"],
    "resources": {"tier": "S", "gpu_count": 0, "vram_gb_each": 0, "gpu_verified": False},
    "claims_gpu_result": False,
    "traceability": {
        "input_contract": {
            "chapter": 4,
            "artifact": "EXP-04-01",
            "revision": "fixture-v4",
            "decision": "validate episode boundaries, timestamps, masks, and four-dimensional split identity before targets",
            "depends_on": [],
        },
        "method_contract": {
            "chapter": 8,
            "artifact": "EXP-08-01",
            "revision": "fixture-v3",
            "decision": "construct continuation-aware value targets without collapsing truncation into terminal",
            "depends_on": ["input_contract"],
        },
        "independent_evaluation": {
            "chapter": 20,
            "artifact": "BENCH-20-01",
            "revision": "fixture-v7",
            "decision": "freeze route population, safety-aware success, timeout policy, valid denominator, and independent-unit plus zero-event estimand assumptions",
            "depends_on": ["input_contract", "method_contract"],
        },
        "deployment_or_safety_gate": {
            "chapter": 21,
            "artifact": "EXP-21-01",
            "revision": "fixture-v7",
            "decision": "reject stale, late, uncertain, or out-of-bounds actions and retain severity-stratified fallback consequences",
            "depends_on": ["input_contract", "method_contract"],
        },
        "evidence_package": {
            "chapter": 22,
            "artifact": "EXP-22-01",
            "revision": "fixture-v4",
            "decision": "bind question, artifacts, failures, resources, evaluation, and limitations into one audit",
            "depends_on": [
                "input_contract",
                "method_contract",
                "independent_evaluation",
                "deployment_or_safety_gate",
            ],
        },
    },
    "evaluation": {
        "independent_from_training": True,
        "protocol_frozen_before_evaluation": True,
        "evaluator_artifact": "BENCH-20-01",
        "metrics": ["route_completion", "collision_rate", "intervention_rate", "deadline_miss_rate"],
    },
    "safety_gateway": {
        "enabled": True,
        "trace_artifact": "EXP-21-01",
        "failure_record": "failure_record",
        "fallback_modes": ["controlled_stop", "request_operator"],
    },
}


INVALID_ARTIFACT_PAYLOADS = {
    "experiment-card.json": "invalid fixture experiment card",
    "model-card.md": "invalid fixture model card",
}


INVALID_DRIVING_PACKAGE = {
    "research_question": "",
    "claim_id": "claim-22",
    "domain": "automatic_driving",
    "data": {"classification": "private", "license": "", "authorized": False},
    "split": {
        "train": {
            "group_ids": ["same-route"],
            "source_asset_ids": ["same-raw-log"],
            "content_fingerprints": ["sha256:1150ac400725ba2c47d6e45c1f26d4769d0b77165833e812a7f0832c800885aa"],
            "similarity_cluster_ids": ["same-cluster"],
        },
        "selection": {
            "group_ids": ["selection-route"],
            "source_asset_ids": ["selection-raw-log"],
            "content_fingerprints": ["sha256:d993043cc1b9417c84f6b5130fa6b58f192d1bc8d30d33ed34a15ff2a1099e4f"],
            "similarity_cluster_ids": ["selection-cluster"],
        },
        "eval": {
            "group_ids": ["same-route"],
            "source_asset_ids": ["same-raw-log"],
            "content_fingerprints": ["sha256:1150ac400725ba2c47d6e45c1f26d4769d0b77165833e812a7f0832c800885aa"],
            "similarity_cluster_ids": ["same-cluster"],
        },
    },
    "artifacts": {
        "experiment_card": _artifact_binding(
            "experiment-card.json", INVALID_ARTIFACT_PAYLOADS["experiment-card.json"], "evidence_package", "claim-22"
        ),
        "model_card": _artifact_binding(
            "model-card.md", INVALID_ARTIFACT_PAYLOADS["model-card.md"], "method_contract", "claim-22"
        ),
    },
    "artifact_payloads": INVALID_ARTIFACT_PAYLOADS,
    "failure_injections": [],
    "known_limitations": [],
    "resources": {"tier": "L2", "gpu_count": 3, "vram_gb_each": 80, "gpu_verified": False},
    "claims_gpu_result": True,
    "evaluation": {
        "independent_from_training": False,
        "protocol_frozen_before_evaluation": False,
        "evaluator_artifact": "unbound-evaluator",
        "metrics": ["success_rate"],
    },
    "safety_gateway": {"enabled": False},
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
        "required_trace_stage_count": len(TRACE_STAGE_RULES),
        "split_identity_dimension_count": len(SPLIT_IDENTITY_FIELDS),
        "verified_artifact_binding_count": len(REQUIRED_ARTIFACTS),
        "verified_failure_injection_count": len(VALID_DRIVING_PACKAGE["failure_injections"]),
    }
