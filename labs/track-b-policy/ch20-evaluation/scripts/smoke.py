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
    easy_safe = metrics["easy_safety_aware"]
    full_goal = metrics["full_goal_only"]
    full = metrics["full_safety_aware"]
    if easy["success_rate"] <= full["success_rate"]:
        raise AssertionError("fixture must expose a protocol-dependent score gap")
    if len(metrics["comparability_warnings"]) != 3:
        raise AssertionError("all three comparability dimensions must be detected")
    if easy["success_wilson_95"]["lower"] >= easy["success_rate"]:
        raise AssertionError("a perfect four-episode point estimate must not imply certainty")
    if full["truncated_episode_count"] != 1 or full["episode_count"] != 8:
        raise AssertionError("the valid timeout must remain visible in the complete denominator")
    if full["invalid_episode_count"] != 0:
        raise AssertionError("the fixed reference table must not contain invalid technical runs")
    if easy_safe["success_rate"] != 1.0 or full_goal["success_rate"] != 0.875:
        raise AssertionError("all four factorial protocol cells must remain visible")
    effects = metrics["factorial_protocol_effects"]
    if effects["interaction"] != -0.25:
        raise AssertionError("the fixture must expose a population-by-success-rule interaction")
    clustered = metrics["paired_cluster_comparison"]
    if clustered["micro_paired_difference"] != 0.3 or clustered["macro_cluster_difference"] != 0.0:
        raise AssertionError("unequal route replication must separate episode-micro and cluster-macro estimands")
    if clustered["cluster_bootstrap_95"] != {"lower": -0.75, "upper": 0.75}:
        raise AssertionError("the exact route-level bootstrap interval must remain deterministic")

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
