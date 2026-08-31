#!/usr/bin/env python3
"""Verify every fixed smoke output exactly matches its registered JSON artifact."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    checked = 0
    for card_path in sorted(ROOT.glob("labs/**/experiment-card.json")):
        card = json.loads(card_path.read_text(encoding="utf-8"))
        smoke_path = card_path.parent / "scripts/smoke.py"
        json_artifacts = [ROOT / item for item in card.get("artifacts", []) if item.endswith(".json")]
        label = card.get("id", str(card_path.relative_to(ROOT)))
        if not smoke_path.is_file():
            errors.append(f"{label}: missing smoke script: {smoke_path.relative_to(ROOT)}")
            continue
        if len(json_artifacts) != 1:
            errors.append(f"{label}: expected exactly one JSON result artifact, found {len(json_artifacts)}")
            continue
        try:
            completed = subprocess.run(
                [sys.executable, str(smoke_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            actual = json.loads(completed.stdout)
            expected = json.loads(json_artifacts[0].read_text(encoding="utf-8"))
        except (subprocess.CalledProcessError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: could not compare smoke and result: {exc}")
            continue
        if actual != expected:
            errors.append(f"{label}: smoke output differs from {json_artifacts[0].relative_to(ROOT)}")
            continue
        checked += 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"result checks passed: {checked} smoke output(s) exactly match registered JSON artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
