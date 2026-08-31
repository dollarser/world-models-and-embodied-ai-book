#!/usr/bin/env python3
"""Run EXP-04-01 without third-party dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from data_audit import audit, load_fixture, summarize  # noqa: E402


EXPECTED_INJECTED_CODES = {
    "normalization_scope",
    "noncontiguous_frame_index",
    "timestamp_cadence",
    "action_out_of_range",
    "group_split_overlap",
}


def main() -> int:
    valid_issues = audit(load_fixture(LAB_ROOT / "fixtures/valid-dataset.json"))
    injected_issues = audit(load_fixture(LAB_ROOT / "fixtures/injected-failures.json"))
    injected_codes = {issue.code for issue in injected_issues}
    if valid_issues:
        raise AssertionError(f"valid fixture produced issues: {valid_issues}")
    if injected_codes != EXPECTED_INJECTED_CODES:
        raise AssertionError(f"expected {sorted(EXPECTED_INJECTED_CODES)}, got {sorted(injected_codes)}")

    report = {
        "experiment_id": "EXP-04-01",
        "status": "smoke",
        "scope": "metadata audit smoke; not validation of a real dataset",
        "metrics": {
            "valid_fixture": summarize(valid_issues),
            "injected_failures": summarize(injected_issues),
            "injected_issue_types_detected": len(injected_codes),
        },
        "detected_codes": sorted(injected_codes),
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
