#!/usr/bin/env python3
"""Run EXP-16-01 without datasets, ML frameworks, or GPU."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from embodiment_fixture import evaluate  # noqa: E402


def main() -> int:
    metrics = evaluate()
    if metrics["schema_aware_pooling_semantic_mae"] != 0.0:
        raise AssertionError("canonical adapters must align both embodiment fixtures")
    if metrics["naive_raw_pooling_semantic_mae"] <= 0.0:
        raise AssertionError("naive raw pooling must expose a semantic mismatch")
    if metrics["contract_rejection_rate"] != 1.0:
        raise AssertionError("missing or stale adapter contracts must be rejected")
    if not metrics["semantic_change_changes_fingerprint"]:
        raise AssertionError("action semantic changes must change the adapter fingerprint")

    report = {
        "experiment_id": "EXP-16-01",
        "status": "smoke",
        "scope": "cross-embodiment action-schema fixture; not learned transfer or policy performance",
        "metrics": metrics,
        "gpu_verified": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
