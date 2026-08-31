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

    report = {
        "experiment_id": "EXP-12-01",
        "status": "smoke",
        "scope": "tri-state ray grid and actionability fixture; not learned 3D perception",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
