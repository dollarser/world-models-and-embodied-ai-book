#!/usr/bin/env python3
"""Run EXP-15-01 without a VLA, checkpoint, simulator, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from action_contract import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["valid_packet_count"] != 3:
        raise AssertionError("all three executable action-head packets must pass")
    if metrics["malformed_rejection_rate"] != 1.0:
        raise AssertionError("every malformed packet must be rejected")
    if metrics["high_level_text_directly_executable"]:
        raise AssertionError("high-level text must not bypass action grounding")
    if not metrics["next_ordered_command_accepted"]:
        raise AssertionError("a fresh command after the accepted sequence must pass")
    if not metrics["replay_command_rejected"] or not metrics["out_of_order_command_rejected"]:
        raise AssertionError("replayed and out-of-order commands must be rejected")
    if not metrics["execution_horizon_bypass_rejected"]:
        raise AssertionError("packet metadata must not expand the schema execution horizon")
    if not metrics["fresh_but_stale_observation_rejected"]:
        raise AssertionError("a fresh packet timestamp must not hide a stale observation timestep")
    if not metrics["wrong_action_timestep_rejected"]:
        raise AssertionError("the first action timestep must match the execution slot")
    if not metrics["duplicate_action_timestep_rejected"] or not metrics["skipped_action_timestep_rejected"]:
        raise AssertionError("every predicted action must bind to one contiguous execution slot")
    if metrics["flow_chunk_action_timesteps"] != (42, 43, 44):
        raise AssertionError("the valid three-step chunk must expose its complete timetable")

    report = {
        "experiment_id": "EXP-15-01",
        "status": "smoke",
        "scope": "action-schema decoding and gateway fixture; not VLA inference or policy quality",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
