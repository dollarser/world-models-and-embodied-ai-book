#!/usr/bin/env python3
"""Run EXP-21-01 without a model, device, network, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from deployment_gate import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if not metrics["latency"]["mean_passes_deadline"]:
        raise AssertionError("the fixture mean must pass the deadline")
    if metrics["latency"]["all_cycles_meet_deadline"]:
        raise AssertionError("the fixture tail must include a deadline miss")
    if metrics["allowed_count"] != 1 or metrics["fallback_count"] != 6:
        raise AssertionError("the deployment gate fixture changed")
    selective = metrics["selective_evaluation"]
    if selective["threshold_0_5"]["coverage"] >= selective["threshold_0_7"]["coverage"]:
        raise AssertionError("the permissive threshold must increase fixture coverage")
    if selective["threshold_0_5"]["accepted_failure_rate"] >= selective["threshold_0_7"]["accepted_failure_rate"]:
        raise AssertionError("the permissive threshold must expose the fixture risk tradeoff")
    report = {
        "experiment_id": "EXP-21-01",
        "status": "smoke",
        "scope": "deadline and action-gate fixture; not real-time, safety, or deployment certification",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
