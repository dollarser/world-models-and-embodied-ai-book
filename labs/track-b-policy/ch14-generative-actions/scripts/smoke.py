#!/usr/bin/env python3
"""Run EXP-14-01 without ML frameworks, downloads, simulator, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from generative_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["mse_mean"]["invalid_action_rate"] != 1.0:
        raise AssertionError("conditional mean must remain outside both valid modes")
    if metrics["mode_refinement_4_steps"]["covered_mode_count"] != 2:
        raise AssertionError("refinement fixture must retain both modes")
    if metrics["oracle_straight_flow_1_step"]["mean_nearest_mode_distance"] > 1e-12:
        raise AssertionError("oracle straight paths must end at assigned modes")
    frequency = metrics["mode_frequency_calibration"]
    if frequency["balanced_5_to_5"]["covered_mode_count"] != frequency["imbalanced_9_to_1"]["covered_mode_count"]:
        raise AssertionError("the frequency negative control must hold mode coverage fixed")
    if frequency["balanced_5_to_5"]["empirical_total_variation_to_target"] != 0.0:
        raise AssertionError("the balanced sample must match the equal target frequencies")
    if frequency["imbalanced_9_to_1"]["empirical_total_variation_to_target"] != 0.4:
        raise AssertionError("the imbalanced sample must expose frequency miscalibration")
    budget = metrics["control_budget"]
    if budget["sequential_10_candidates_4_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("sequential candidates must include candidate count in the forward budget")
    if not budget["single_batch_10_candidates_4_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("the abstract batched four-step fixture must fit eight forward passes")
    if budget["single_batch_10_candidates_16_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("sixteen solver steps must exceed the eight-forward abstract budget")
    availability = metrics["candidate_availability"]
    if availability[-1]["iid_any_accepted_probability"] != 0.971852502329:
        raise AssertionError("the iid endpoint must use the registered best-of-N formula")
    if availability[-1]["sample_model_evaluation_count"] != 64 or availability[-1]["forward_pass_count"] != 8:
        raise AssertionError("the availability panel must carry its candidate-generation budget")
    if {row["perfectly_correlated_any_accepted_probability"] for row in availability} != {0.2}:
        raise AssertionError("perfect correlation must preserve the single-candidate availability")
    if metrics["safety_screen"]["mixed_modes"]["safety_accepted_count"] != 5:
        raise AssertionError("the independent gate must reject the five blocked-mode candidates")
    if not metrics["safety_screen"]["all_candidates_blocked"]["fallback_used"]:
        raise AssertionError("no accepted candidate must trigger the deterministic fallback")

    report = {
        "experiment_id": "EXP-14-01",
        "status": "smoke",
        "scope": "analytic bimodal action, candidate-dependence, batching-budget, and gate fixture; not trained diffusion or flow policy",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
