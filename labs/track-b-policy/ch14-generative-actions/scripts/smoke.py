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
    budget = metrics["control_budget"]
    if budget["sequential_10_candidates_4_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("sequential candidates must include candidate count in the forward budget")
    if not budget["single_batch_10_candidates_4_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("the abstract batched four-step fixture must fit eight forward passes")
    if budget["single_batch_10_candidates_16_steps"]["fits_abstract_forward_budget"]:
        raise AssertionError("sixteen solver steps must exceed the eight-forward abstract budget")
    if metrics["safety_screen"]["mixed_modes"]["safety_accepted_count"] != 5:
        raise AssertionError("the independent gate must reject the five blocked-mode candidates")
    if not metrics["safety_screen"]["all_candidates_blocked"]["fallback_used"]:
        raise AssertionError("no accepted candidate must trigger the deterministic fallback")

    report = {
        "experiment_id": "EXP-14-01",
        "status": "smoke",
        "scope": "analytic bimodal action, batching budget, and candidate-gate fixture; not trained diffusion or flow policy",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
