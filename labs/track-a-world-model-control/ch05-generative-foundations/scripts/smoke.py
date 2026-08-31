#!/usr/bin/env python3
"""Run EXP-05-01 without training, data downloads, or a GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from generative_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["point_mean_distance_to_nearest_supported_future"] != 1.0:
        raise AssertionError("the point mean must remain outside the fork support")
    if metrics["fork_sample_support_coverage"] != 1.0:
        raise AssertionError("the deterministic categorical samples must cover both modes")
    if metrics["conditional_dataset_nll"] >= metrics["unconditional_dataset_nll"]:
        raise AssertionError("conditioning must improve this fixture's likelihood")
    report = {
        "experiment_id": "EXP-05-01",
        "status": "smoke",
        "scope": "analytic multimodal and probability-path fixture; not a trained generative model",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
