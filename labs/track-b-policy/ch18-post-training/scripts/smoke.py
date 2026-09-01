#!/usr/bin/env python3
"""Run EXP-18-01 without policy training, simulator, model weights, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from reweighting_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["reward_weighted"]["reference_mae"] >= metrics["uniform"]["reference_mae"]:
        raise AssertionError("fixed reward weighting must move the target toward the successful reference")
    if metrics["reward_weighted"]["effective_sample_size"] >= metrics["uniform"]["effective_sample_size"]:
        raise AssertionError("fixed reward weighting must expose sample concentration")
    if not metrics["support_gate"]["unseen_hybrid"]["marginal_range_accepted"]:
        raise AssertionError("the unseen hybrid must expose the weakness of marginal ranges")
    if metrics["support_gate"]["unseen_hybrid"]["joint_support_accepted"]:
        raise AssertionError("the joint trajectory gate must reject the unseen hybrid")
    if metrics["leave_one_out_advantage"]["all_success"]["has_nonzero_learning_signal"]:
        raise AssertionError("an all-success group must have zero leave-one-out advantage")
    if metrics["leave_one_out_advantage"]["all_failure"]["has_nonzero_learning_signal"]:
        raise AssertionError("an all-failure group must have zero leave-one-out advantage")
    if not metrics["leave_one_out_advantage"]["mixed"]["has_nonzero_learning_signal"]:
        raise AssertionError("a mixed-outcome group must retain relative advantage signal")
    if metrics["dynamic_rejection"]["attempted_difficulty_distribution"]["medium"] != 0.5:
        raise AssertionError("the attempted fixture must contain easy, medium, and hard contexts")
    if metrics["dynamic_rejection"]["used_difficulty_distribution"]["medium"] != 1.0:
        raise AssertionError("zero-advantage rejection must expose the changed used-context distribution")
    if metrics["dynamic_rejection"]["rejected_rollout_count"] != 6:
        raise AssertionError("rejected rollout count must remain explicit rather than inferred")
    report = {
        "experiment_id": "EXP-18-01",
        "status": "smoke",
        "scope": "offline scalar trajectory reweighting; not VLA/RL training or policy improvement",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
