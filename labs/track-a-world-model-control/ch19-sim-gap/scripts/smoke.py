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
    if any(metrics["calibrated_held_out_gap"].values()):
        raise AssertionError("the grid fixture must recover the target parameters")
    if metrics["narrow_randomization_covers_target"]:
        raise AssertionError("the narrow range must miss the target")
    if not metrics["broad_randomization_covers_target"]:
        raise AssertionError("the broad range must cover the target")

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
