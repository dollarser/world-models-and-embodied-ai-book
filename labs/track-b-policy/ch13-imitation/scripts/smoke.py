#!/usr/bin/env python3
"""Run EXP-13-01 without frameworks, downloads, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imitation_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    compounding = metrics["compounding_error"]
    chunks = metrics["chunk_tradeoff"]
    if compounding["closed_loop_final_state_error"] <= compounding["open_loop_action_rmse"]:
        raise AssertionError("fixture must expose integrated closed-loop error")
    if not chunks[0]["policy_queries"] > chunks[-1]["policy_queries"]:
        raise AssertionError("larger execution horizons must reduce policy queries")
    if not chunks[0]["mean_reaction_delay_steps"] < chunks[-1]["mean_reaction_delay_steps"]:
        raise AssertionError("larger chunks must increase stale-action delay")
    if {row["prediction_horizon_steps"] for row in chunks} != {8}:
        raise AssertionError("the execution-policy comparison must hold prediction horizon fixed")
    ensemble = metrics["temporal_ensemble"]
    if ensemble["stationary_ensemble_absolute_error"] >= ensemble["stationary_latest_absolute_error"]:
        raise AssertionError("the fixed stationary case must expose jitter reduction")
    if ensemble["changed_ensemble_absolute_error"] <= ensemble["changed_latest_absolute_error"]:
        raise AssertionError("the fixed regime change must expose temporal-ensemble lag")

    report = {
        "experiment_id": "EXP-13-01",
        "status": "smoke",
        "scope": "deterministic protocol fixture; not a learned policy comparison",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
