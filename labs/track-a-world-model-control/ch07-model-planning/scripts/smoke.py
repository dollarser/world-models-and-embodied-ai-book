#!/usr/bin/env python3
"""Run EXP-07-01 without an RL library, model training, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from planning_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["horizon_1"]["actions"] == metrics["horizon_3"]["actions"][:1]:
        raise AssertionError("the fixture must expose horizon-dependent first actions")
    if metrics["receding_horizon_after_disturbance"]["return"] <= metrics["open_loop_after_disturbance"]["return"]:
        raise AssertionError("replanning must recover in the fixed disturbance fixture")
    if metrics["value_equivalence_fixture"]["max_bellman_backup_gap"] != 0.0:
        raise AssertionError("the surrogate labels must preserve the fixed Bellman backups")
    if metrics["risk_objective_fixture"]["mean_selected_action"] == metrics["risk_objective_fixture"]["worst_20_percent_selected_action"]:
        raise AssertionError("the fixture must expose mean-return and lower-tail ranking disagreement")
    report = {
        "experiment_id": "EXP-07-01",
        "status": "smoke",
        "scope": "enumerated delayed-reward and five-scenario risk fixtures; not learned-model, probability, safety, or CEM performance",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
