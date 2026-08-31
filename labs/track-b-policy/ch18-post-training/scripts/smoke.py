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
    if metrics["support_gate"]["out_of_support_proposal_accepted"]:
        raise AssertionError("the fixed out-of-support proposal must be rejected")
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
