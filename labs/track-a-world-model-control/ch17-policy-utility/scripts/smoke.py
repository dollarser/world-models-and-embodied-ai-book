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
