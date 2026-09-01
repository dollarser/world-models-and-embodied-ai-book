#!/usr/bin/env python3
"""Run EXP-22-01 without models, datasets, simulators, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from project_audit import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if not metrics["valid_package"]["accepted"]:
        raise AssertionError("the complete fixed package must be accepted")
    if metrics["invalid_package"]["accepted"]:
        raise AssertionError("the incomplete fixed package must be rejected")
    if metrics["invalid_package"]["issue_count"] != 23:
        raise AssertionError("the fixed audit issue set changed")
    if metrics["required_trace_stage_count"] != 5:
        raise AssertionError("the complete package must expose the five-stage evidence trace")
    if metrics["split_identity_dimension_count"] != 4:
        raise AssertionError("all three partitions must expose four split-identity dimensions")
    if metrics["verified_artifact_binding_count"] != 5:
        raise AssertionError("all required artifacts must have verified digest bindings")
    if metrics["verified_failure_injection_count"] != 2:
        raise AssertionError("both fixed failure injections must reproduce their expected issue")
    report = {
        "experiment_id": "EXP-22-01",
        "status": "smoke",
        "scope": "in-memory project-package contract audit; not filesystem reproduction, model, or deployment validation",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
