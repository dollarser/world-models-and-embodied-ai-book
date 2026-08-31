#!/usr/bin/env python3
"""Run EXP-02-01 without third-party dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from system_cards import load_fixture, summarize, validate_fixture  # noqa: E402


def main() -> int:
    fixture = load_fixture(LAB_ROOT / "fixtures/system-cards.json")
    errors = validate_fixture(fixture)
    if errors:
        raise AssertionError("; ".join(errors))
    report = {
        "experiment_id": "EXP-02-01",
        "status": "smoke",
        "scope": fixture["scope"],
        "metrics": summarize(fixture),
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
