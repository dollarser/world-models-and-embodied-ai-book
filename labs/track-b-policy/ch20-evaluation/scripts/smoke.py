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
    paired_margins = metrics["paired_margin_diagnostic"]
    if not paired_margins["marginal_rates_equal_across_tables"]:
        raise AssertionError("the pairing negative control must hold both marginal rates fixed")
    if paired_margins["high_concordance"]["exact_conditional_two_sided_p"] != 0.125:
        raise AssertionError("the four-discordant-pair exact diagnostic must remain fixed")
    if paired_margins["more_discordant"]["exact_conditional_two_sided_p"] != 0.387695:
        raise AssertionError("the twelve-discordant-pair exact diagnostic must remain fixed")
    expected_effect_interval = {
        "sample_count": 20,
        "mean": 0.2,
        "radius": 0.607361,
        "lower": -0.407361,
        "upper": 0.807361,
    }
    for report in (
        paired_margins["high_concordance"],
        paired_margins["more_discordant"],
    ):
        if report["paired_difference_hoeffding_95"] != expected_effect_interval:
            raise AssertionError("the fixed paired-difference Hoeffding interval must remain exact")
        if report["interval_within_practical_equivalence_band"]:
            raise AssertionError("the conservative interval must not establish practical equivalence")
    if metrics["zero_event_upper_bounds_95"] != {
        "20_trials": 0.139108,
        "100_trials": 0.029513,
        "1000_trials": 0.002991,
    }:
        raise AssertionError("zero observed events must retain a positive deterministic risk upper bound")
    pseudoreplication = metrics["zero_event_pseudoreplication_audit"]
    if pseudoreplication["episode_iid_upper_if_independent"] != 0.029513:
        raise AssertionError("the nominal 100-episode iid bound must remain explicit")
    if pseudoreplication["cluster_incidence_upper_if_clusters_independent"] != 0.258866:
        raise AssertionError("ten independent clusters must retain their distinct cluster-incidence bound")
    if not pseudoreplication["estimands_are_different"]:
        raise AssertionError("episode and cluster event probabilities must not be treated as one estimand")
    selection = metrics["checkpoint_selection_audit"]
    if selection["selection_split_selected_checkpoint"] != "checkpoint-a":
        raise AssertionError("checkpoint selection must be frozen on the selection split")
    if selection["test_reuse_selected_checkpoint"] != "checkpoint-d":
        raise AssertionError("the negative control must expose final-set-driven checkpoint selection")
    if selection["test_reuse_authored_optimism_gap"] != 0.25:
        raise AssertionError("the untouched confirmation score must expose the authored reuse gap")
    retry = metrics["adaptive_retry_audit"]
    if retry["task_count"] != 4 or retry["attempt_count"] != 6:
        raise AssertionError("the adaptive retry ledger must preserve task and attempt denominators")
    if retry["per_attempt_success_rate"] != 0.5:
        raise AssertionError("the per-attempt success estimand must remain fixed")
    if retry["task_success_rate_with_up_to_two_attempts"] != 0.75:
        raise AssertionError("the retry-policy task success estimand must remain fixed")
    if retry["mean_attempts_per_task"] != 1.5 or retry["recovered_task_count"] != 1:
        raise AssertionError("retry cost and recovered-task accounting must remain explicit")

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
