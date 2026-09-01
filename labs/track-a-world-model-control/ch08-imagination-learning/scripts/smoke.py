#!/usr/bin/env python3
"""Run EXP-08-01 without RL training, model weights, data downloads, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from imagination_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["lambda_targets"]["lambda_0_5"] != (0.65, 0.9, 1.0):
        raise AssertionError("the fixed lambda-return reference changed")
    if metrics["reward_model_bias"]["start_target_gap"] != 1.0:
        raise AssertionError("the fixed imagined reward bias must reach the start target")
    if metrics["continuation_mask"]["leakage_gap"] != 10.0:
        raise AssertionError("the fixture must expose post-terminal reward leakage")
    if metrics["episode_end_semantics"]["truncation_bootstrap_loss"] != 4.0:
        raise AssertionError("collapsing truncation into done must expose lost bootstrap value")
    if metrics["truncation_trace_boundary"]["cross_episode_start_target_leakage"] != 96.0:
        raise AssertionError("a truncation must bootstrap without consuming the next episode's return")
    if metrics["imagined_loss_weighting"]["post_terminal_loss_leakage"] != 100.0:
        raise AssertionError("the continuation mask must remove post-terminal loss contribution")
    report = {
        "experiment_id": "EXP-08-01",
        "status": "smoke",
        "scope": "analytic lambda-return, continuation, and imagined-loss weighting fixture; not Dreamer training or policy improvement",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
