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
    blind, conditioned = metrics["action_blind"], metrics["action_conditioned"]
    if blind["action_sensitivity"] >= conditioned["action_sensitivity"]:
        raise AssertionError("action-conditioned model must distinguish counterfactual actions")
    if blind["mean_unseen_sequence_endpoint_error"] <= conditioned["mean_unseen_sequence_endpoint_error"]:
        raise AssertionError("action-conditioned model must improve held-out sequence rollout")

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
