#!/usr/bin/env python3
"""Run EXP-07-01 without an RL library, model training, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from planning_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["horizon_1"]["actions"] == metrics["horizon_3"]["actions"][:1]:
        raise AssertionError("the fixture must expose horizon-dependent first actions")
    protocol = metrics["disturbance_protocol_audit"]
    legacy = protocol["legacy_unequal_budget"]
    if legacy["open_loop"]["post_disturbance_action_budget"] == legacy["replanning"]["post_disturbance_action_budget"]:
        raise AssertionError("the legacy fixture must expose its unequal action budgets")
    reward_only = protocol["fixed_budget_reward_only"]
    if reward_only["open_loop"]["post_disturbance_action_budget"] != reward_only["replanning"]["post_disturbance_action_budget"]:
        raise AssertionError("the controlled comparison must hold the action budget fixed")
    if reward_only["replanning"]["environment_return"] <= reward_only["open_loop"]["environment_return"]:
        raise AssertionError("replanning must improve reward in the fixed-budget fixture")
    terminal_objective = protocol["fixed_budget_with_terminal_value"]["replanning"]
    if terminal_objective["return"] == terminal_objective["environment_return"]:
        raise AssertionError("terminal value must remain separate from observed environment return")
    if metrics["value_equivalence_fixture"]["max_bellman_backup_gap"] != 0.0:
        raise AssertionError("the surrogate labels must preserve the fixed Bellman backups")
    if metrics["risk_objective_fixture"]["mean_selected_action"] == metrics["risk_objective_fixture"]["worst_20_percent_selected_action"]:
        raise AssertionError("the fixture must expose mean-return and lower-tail ranking disagreement")
    report = {
        "experiment_id": "EXP-07-01",
        "status": "smoke",
        "scope": "enumerated delayed-reward, controlled replanning-protocol, and five-scenario risk fixtures; not learned-model, probability, safety, or CEM performance",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
