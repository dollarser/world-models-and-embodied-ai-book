#!/usr/bin/env python3
"""Run EXP-17-01 without datasets, ML frameworks, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from policy_utility import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["transition_agreement"]["matching_count"] != 8:
        raise AssertionError("the learned fixture must match eight of nine tested transitions")
    if metrics["policy_ranking_matches"]:
        raise AssertionError("the critical shortcut error must reverse policy ranking")
    if metrics["selected_policy_true_terminal"] != "collision":
        raise AssertionError("model-selected shortcut must fail in the true simulator")
    if metrics["model_selected_first_transition_matches"]:
        raise AssertionError("the model-selected first transition must expose the optimistic error")
    gate_audit = metrics["support_gate_audit"]
    if gate_audit["out_of_support_error"]["selected_policy"] != "safe_route":
        raise AssertionError("support gate must reject the unsupported shortcut")
    if gate_audit["out_of_support_error"]["model_exploitation_regret"] != 0.0:
        raise AssertionError("support-gated selection must remove exploitation regret in this fixture")
    if gate_audit["in_support_model_error"]["selected_policy_true_terminal"] != "collision":
        raise AssertionError("support membership must not hide the in-support model error")
    if gate_audit["in_support_model_error"]["model_exploitation_regret"] != metrics["model_exploitation_regret"]:
        raise AssertionError("the in-support error must preserve the ungated exploitation regret")

    report = {
        "experiment_id": "EXP-17-01",
        "status": "smoke",
        "scope": "deterministic model-gap and policy-exploitation fixture; not learned-world-model performance",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
