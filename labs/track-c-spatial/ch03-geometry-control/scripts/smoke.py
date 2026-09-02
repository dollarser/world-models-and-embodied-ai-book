#!/usr/bin/env python3
"""Run EXP-03-01 with Python standard library only."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from bridge_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    geometry, control = metrics["geometry"], metrics["control"]
    if geometry["max_reprojection_error_px"] > 1e-12:
        raise AssertionError("projection round trip must close for the exact fixture")
    if geometry["depth_unit_fault_scale_ratio"] != 1000.0:
        raise AssertionError("millimetre/metre fault must be visible")
    if geometry["temporal_alignment"]["translation_only"]["spatial_error_m"] != 0.2:
        raise AssertionError("2 m/s and 100 ms offset must produce the fixed 0.2 m translation error")
    if geometry["temporal_alignment"]["timestamp_matched"]["spatial_error_m"] != 0.0:
        raise AssertionError("timestamp-matched transform must close exactly")
    if geometry["pose_interpolation"]["shortest_arc_interpolation_error_m"] != 0.0:
        raise AssertionError("registered shortest-arc interpolation must match the authored midpoint")
    if geometry["pose_interpolation"]["naive_angle_interpolation_error_m"] != 20.0:
        raise AssertionError("naive wrapped-angle averaging must expose the fixed 20 m point error")
    if control["feedback_endpoint_error_m"] >= control["open_loop_endpoint_error_m"]:
        raise AssertionError("feedback must reduce the injected actuator-bias error")

    report = {
        "experiment_id": "EXP-03-01",
        "status": "smoke",
        "scope": "exact RGB-D, temporal-transform/interpolation, and planar feedback fixtures; not calibrated hardware",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
