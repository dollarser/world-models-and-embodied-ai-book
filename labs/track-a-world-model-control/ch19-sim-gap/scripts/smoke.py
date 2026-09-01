#!/usr/bin/env python3
"""Run EXP-19-01 without a simulator install, dataset, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from sim_gap import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["nominal_held_out_gap"]["state_mae"] <= 0.0:
        raise AssertionError("nominal parameters must expose a held-out simulator gap")
    if metrics["observation_only_calibration"]["identifiable"]:
        raise AssertionError("observation-only gain and scale must remain structurally confounded")
    if metrics["observation_only_calibration"]["minimizer_count"] != 2:
        raise AssertionError("the fixed observation-only grid must expose two equivalent minimizers")
    if metrics["observation_only_alternative"]["held_out_gap"]["observation_mae"] != 0.0:
        raise AssertionError("the alternative must remain observation-equivalent on held-out actions")
    if metrics["observation_only_alternative"]["held_out_gap"]["state_mae"] <= 0.0:
        raise AssertionError("the observation-equivalent alternative must expose a hidden state gap")
    if not metrics["state_observation_calibration"]["identifiable"]:
        raise AssertionError("the state anchor must identify one grid candidate")
    if any(metrics["calibrated_held_out_gap"].values()):
        raise AssertionError("the state-anchored grid fixture must recover the target parameters")
    if metrics["narrow_randomization_covers_target"]:
        raise AssertionError("the narrow range must miss the target")
    if not metrics["broad_randomization_covers_target"]:
        raise AssertionError("the broad range must cover the target")
    condition_metrics = metrics["operating_condition_calibration"]
    if condition_metrics["single_load"]["minimizer_count"] != 3:
        raise AssertionError("one load must expose three force/load-equivalent grid points")
    if condition_metrics["repeated_same_load"]["minimizer_count"] != 3:
        raise AssertionError("repeating one load must not resolve the structural ambiguity")
    if condition_metrics["repeated_same_load"]["unique_condition_count"] != 1:
        raise AssertionError("duplicate measurements must remain one unique condition")
    if condition_metrics["two_distinct_loads"]["minimizer_count"] != 1:
        raise AssertionError("two distinct known loads must identify one fixed-grid candidate")
    if condition_metrics["single_load_alternative_payload_one_mae"] <= 0.0:
        raise AssertionError("the single-load alternative must fail at the second load")

    report = {
        "experiment_id": "EXP-19-01",
        "status": "smoke",
        "scope": "scalar calibration and bias-attribution fixture; not a physics simulator or sim-to-real result",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
