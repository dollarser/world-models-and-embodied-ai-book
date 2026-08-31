#!/usr/bin/env python3
"""Validate the essential experiment-card contract without dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


REQUIRED = {
    "schema_version",
    "id",
    "chapter",
    "status",
    "claim_scope",
    "code",
    "data",
    "resources",
    "commands",
    "metrics",
    "limitations",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_experiment_card.py CARD.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    card = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - card.keys())
    if missing:
        print(f"missing fields: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not re.fullmatch(r"EXP-\d{2}-\d{2}", card["id"]):
        print("invalid experiment id", file=sys.stderr)
        return 1
    if card["schema_version"] != 2:
        print("unsupported experiment-card schema version", file=sys.stderr)
        return 1
    if card["status"] not in {"planned", "smoke", "experimented", "reviewed", "reproducible"}:
        print("invalid status", file=sys.stderr)
        return 1
    if card["resources"]["gpu_verified"] and card["resources"].get("peak_vram_bytes") is None:
        print("GPU-verified cards require peak_vram_bytes", file=sys.stderr)
        return 1
    if card["data"].get("classification") not in {
        "fixture", "downloadable", "application_required", "restricted", "private"
    }:
        print("invalid data classification", file=sys.stderr)
        return 1
    print(f"experiment card valid: {card['id']} ({card['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
