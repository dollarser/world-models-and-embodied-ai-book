#!/usr/bin/env python3
"""Run EXP-10-01 without model weights, downloads, frameworks, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from probing_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    appearance = metrics["appearance"]
    predictive = metrics["task_predictive"]
    if appearance["reconstruction_mse"] >= predictive["reconstruction_mse"]:
        raise AssertionError("appearance representation must win reconstruction")
    if appearance["shifted_probe_accuracy"] >= predictive["shifted_probe_accuracy"]:
        raise AssertionError("task-predictive representation must win shifted probing")

    report = {
        "experiment_id": "EXP-10-01",
        "status": "smoke",
        "scope": "hand-designed representation ranking reversal; not V-JEPA inference",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
