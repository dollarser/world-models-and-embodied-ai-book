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
    if appearance["in_distribution_probe_accuracy"] != 1.0:
        raise AssertionError("appearance shortcut must look successful in distribution")
    action_metrics = metrics["action_interface"]
    if action_metrics["action_blind"]["current_state_probe_rmse"] != 0.0:
        raise AssertionError("action-blind interface must retain an exact current-state readout")
    if action_metrics["action_blind"]["counterfactual_transition_rmse"] <= action_metrics["action_conditioned"]["counterfactual_transition_rmse"]:
        raise AssertionError("action-conditioned interface must win counterfactual transition prediction")
    temporal_metrics = metrics["temporal_interface"]
    if temporal_metrics["middle_frame"]["current_state_probe_rmse"] != 0.0:
        raise AssertionError("middle-frame interface must retain the authored current state")
    if temporal_metrics["middle_frame"]["temporal_direction_accuracy"] != 0.5:
        raise AssertionError("direction-blind interface must remain at balanced-fixture chance")
    if temporal_metrics["ordered_delta"]["temporal_direction_accuracy"] != 1.0:
        raise AssertionError("ordered temporal delta must recover every authored direction")
    if temporal_metrics["middle_frame"]["reversal_sensitivity"] != 0.0:
        raise AssertionError("middle-frame interface must be invariant to reversal")
    if temporal_metrics["ordered_delta"]["reversal_sensitivity"] != 4.0:
        raise AssertionError("ordered temporal delta must change under reversal")

    report = {
        "experiment_id": "EXP-10-01",
        "status": "smoke",
        "scope": "hand-designed representation shift, action-interface, and temporal-order diagnostics; not V-JEPA inference",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
