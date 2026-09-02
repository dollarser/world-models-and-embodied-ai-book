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
    if not perceptual["action_sensitivity"] < functional["action_sensitivity"]:
        raise AssertionError("action intervention must expose the action-blind predictor")
    missingness = metrics["horizon_missingness"]
    if missingness["available_case_terminal_winner"] == missingness["fixed_denominator_terminal_winner"]:
        raise AssertionError("missing-rollout policy must reverse the terminal ranking")
    probability = metrics["probability_metric_diagnostic"]
    if not probability["one_bin_ece_tie"]:
        raise AssertionError("coarse one-bin ECE must hide the forecast-quality difference")
    if not probability["informative"]["brier_loss"] < probability["uniform_base_rate"]["brier_loss"]:
        raise AssertionError("the informative forecast must win the authored Brier comparison")
    if not probability["informative"]["two_bin_ece"] > probability["informative"]["one_bin_ece"]:
        raise AssertionError("the registered binning must expose ECE sensitivity")
    concentration = metrics["probability_error_concentration"]
    if concentration["mean_brier_gap"] != 0.0:
        raise AssertionError("the probability pair must retain equal mean Brier loss")
    if concentration["diffuse_error"]["threshold_accuracy_at_0_5"] != 1.0:
        raise AssertionError("the diffuse-error forecast must keep four correct threshold decisions")
    if concentration["concentrated_error"]["threshold_accuracy_at_0_5"] != 0.75:
        raise AssertionError("the concentrated-error forecast must expose one threshold error")
    if not (
        concentration["concentrated_error"]["maximum_log_loss"]
        > concentration["diffuse_error"]["maximum_log_loss"]
    ):
        raise AssertionError("equal mean Brier must not hide the larger worst log loss")

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
