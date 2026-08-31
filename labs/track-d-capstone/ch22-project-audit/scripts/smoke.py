#!/usr/bin/env python3
"""Run EXP-22-01 without models, datasets, simulators, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from project_audit import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if not metrics["valid_package"]["accepted"]:
        raise AssertionError("the complete fixed package must be accepted")
    if metrics["invalid_package"]["accepted"]:
        raise AssertionError("the incomplete fixed package must be rejected")
    if metrics["invalid_package"]["issue_count"] != 15:
        raise AssertionError("the fixed audit issue set changed")
    report = {
        "experiment_id": "EXP-22-01",
        "status": "smoke",
        "scope": "project-metadata contract audit; not end-to-end model or deployment validation",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
