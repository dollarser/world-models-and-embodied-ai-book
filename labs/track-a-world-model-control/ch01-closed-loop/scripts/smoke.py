#!/usr/bin/env python3
"""Run EXP-01-01 without models, datasets, simulators, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from closed_loop_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["offline_mae_gap"] != 0.0:
        raise AssertionError("the two fixed sequences must have equal offline MAE")
    if not metrics["persistent_residual"]["bound_violated"]:
        raise AssertionError("persistent residual must cross the fixed bound")
    if metrics["alternating_residual"]["bound_violated"]:
        raise AssertionError("alternating residual must remain inside the fixed bound")
    feedback = metrics["feedback_comparison"]
    if feedback["timely_feedback"]["bound_violated"]:
        raise AssertionError("the fixed timely-feedback case must remain inside the bound")
    if not feedback["delayed_feedback"]["bound_violated"]:
        raise AssertionError("the fixed delayed-feedback case must cross the bound")
    if feedback["authority_limited_feedback"]["saturation_count"] != 11:
        raise AssertionError("the fixed authority-limited case must expose eleven saturated steps")
    report = {
        "experiment_id": "EXP-01-01",
        "status": "smoke",
        "scope": "scalar feedback-mechanics fixture; not learned perception or physical controller, robot, or vehicle performance",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
