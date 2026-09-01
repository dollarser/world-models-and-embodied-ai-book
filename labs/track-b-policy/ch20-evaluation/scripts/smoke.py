#!/usr/bin/env python3
"""Run EXP-20-01 without simulators, downloads, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from protocol_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    easy = metrics["easy_goal_only"]
    full = metrics["full_safety_aware"]
    if easy["success_rate"] <= full["success_rate"]:
        raise AssertionError("fixture must expose a protocol-dependent score gap")
    if len(metrics["comparability_warnings"]) != 3:
        raise AssertionError("all three comparability dimensions must be detected")
    if easy["success_wilson_95"]["lower"] >= easy["success_rate"]:
        raise AssertionError("a perfect four-episode point estimate must not imply certainty")

    report = {
        "experiment_id": "EXP-20-01",
        "status": "smoke",
        "scope": "fixed episode-table protocol audit; not simulator evaluation",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
