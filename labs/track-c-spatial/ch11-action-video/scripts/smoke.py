#!/usr/bin/env python3
"""Run EXP-11-01 without video models, downloads, frameworks, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from action_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    blind = metrics["action_blind"]
    swapped = metrics["left_right_swapped"]
    conditioned = metrics["action_conditioned"]
    if blind["action_sensitivity"] >= conditioned["action_sensitivity"]:
        raise AssertionError("action-conditioned model must distinguish counterfactual actions")
    if blind["mean_unseen_sequence_endpoint_error"] <= conditioned["mean_unseen_sequence_endpoint_error"]:
        raise AssertionError("action-conditioned model must improve held-out sequence rollout")
    if swapped["action_sensitivity"] != conditioned["action_sensitivity"]:
        raise AssertionError("swapped control labels must preserve action sensitivity in this diagnostic")
    if swapped["left_to_right_signed_separation"] >= 0.0:
        raise AssertionError("swapped control labels must reverse the signed left-to-right effect")
    if swapped["counterfactual_vector_rmse"] <= conditioned["counterfactual_vector_rmse"]:
        raise AssertionError("direction-aware counterfactual error must detect swapped actions")
    if swapped["endpoint_cancellation_sequence_count"] != 1:
        raise AssertionError("one swapped-action sequence must return to the correct endpoint")
    if swapped["endpoint_cancellation_sequence_ids"] != ["left→forward→right"]:
        raise AssertionError("endpoint cancellation must stay bound to the preregistered sequence")
    if swapped["maximum_hidden_intermediate_error"] != 2.0:
        raise AssertionError("endpoint cancellation must retain its authored intermediate error")
    if conditioned["endpoint_cancellation_sequence_count"] != 0:
        raise AssertionError("exact rollouts must not be labeled as endpoint cancellation")

    report = {
        "experiment_id": "EXP-11-01",
        "status": "smoke",
        "scope": "learned transition-table and ASCII-frame fixture; not a video world model",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
