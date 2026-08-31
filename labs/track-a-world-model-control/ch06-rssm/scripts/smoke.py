#!/usr/bin/env python3
"""Run EXP-06-01 without third-party dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from toy_rssm import ToyRSSM, evaluate, generate_trajectory  # noqa: E402


def main() -> int:
    trajectory = generate_trajectory(steps=32, seed=7)
    metrics = evaluate(ToyRSSM(), trajectory)

    if not metrics["open_loop_rmse"] > metrics["filtering_rmse"]:
        raise AssertionError("open-loop RMSE should exceed filtering RMSE in the fixture")

    report = {
        "experiment_id": "EXP-06-01",
        "status": "smoke",
        "scope": "data-flow and metric smoke; not neural training",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
