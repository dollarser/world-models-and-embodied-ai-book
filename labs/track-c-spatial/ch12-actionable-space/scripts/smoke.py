#!/usr/bin/env python3
"""Run EXP-12-01 without 3D frameworks, downloads, simulators, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from occupancy_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if not metrics["occluded_cell_is_unknown"]:
        raise AssertionError("cell behind a depth return must stay unknown")
    if metrics["dynamic_path_safe_tristate_before_update"]:
        raise AssertionError("conservative tri-state map must reject an unknown path")
    if not metrics["dynamic_path_safe_binary_unknown_as_free"]:
        raise AssertionError("binary absent-is-free baseline must expose false safety")
    if metrics["dynamic_path_safe_after_update"]:
        raise AssertionError("updated dynamic occupancy must reject the collision path")
    if metrics["dynamic_old_cell_without_clearing_evidence"] != "unknown":
        raise AssertionError("a departed return must not make its old cell free without clearing evidence")
    if metrics["dynamic_old_cell_with_clearing_evidence"] != "free":
        raise AssertionError("explicit clearing evidence must be able to mark the old cell free")
    if not metrics["centerline_point_path_safe"] or metrics["centerline_radius_one_footprint_report"]["safe"]:
        raise AssertionError("the fixture must expose point-centerline versus footprint safety")
    if not metrics["fresh_free_path_safe"] or metrics["stale_free_path_safe"]:
        raise AssertionError("expired free-space evidence must conservatively block the path")
    if not metrics["sparse_waypoint_only_report"]["safe"] or metrics["sparse_segment_report"]["safe"]:
        raise AssertionError("segment rasterization must expose the obstacle between sparse waypoints")

    report = {
        "experiment_id": "EXP-12-01",
        "status": "smoke",
        "scope": "tri-state ray grid, rasterized path, and actionability fixture; not continuous collision checking or learned 3D perception",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
