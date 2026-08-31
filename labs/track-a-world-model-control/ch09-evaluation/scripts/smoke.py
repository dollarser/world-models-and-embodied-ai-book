#!/usr/bin/env python3
"""Run EXP-09-01 without frameworks, downloads, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from evaluation_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    perceptual = metrics["action_blind"]
    functional = metrics["action_faithful_biased"]
    if not perceptual["one_step_rmse"] < functional["one_step_rmse"]:
        raise AssertionError("fixture must make the action-blind model win one-step RMSE")
    if not perceptual["closed_loop_success_rate"] < functional["closed_loop_success_rate"]:
        raise AssertionError("fixture must reverse the ranking under closed-loop utility")

    report = {
        "experiment_id": "EXP-09-01",
        "status": "smoke",
        "scope": "metric-ranking fixture; not learned world-model evaluation",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
