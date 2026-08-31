"""Standard-library data-contract audit for Chapter 4 fixtures."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


REQUIRED_FEATURES = {"observation.state", "action", "timestamp"}


@dataclass(frozen=True)
class Issue:
    code: str
    location: str
    detail: str


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(fixture: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    dataset = fixture.get("dataset", {})
    episodes = fixture.get("episodes", [])
    features = dataset.get("features", {})
    missing_features = REQUIRED_FEATURES - set(features)
    if missing_features:
        issues.append(Issue("missing_feature", "dataset.features", str(sorted(missing_features))))

    if dataset.get("normalization_scope") != "train":
        issues.append(Issue("normalization_scope", "dataset.normalization_scope", "statistics must use train only"))

    fps = dataset.get("fps")
    expected_delta = 1.0 / fps if isinstance(fps, (int, float)) and fps > 0 else None
    action_range = dataset.get("action_range", [None, None])
    lower, upper = action_range if isinstance(action_range, list) and len(action_range) == 2 else (None, None)

    groups_by_split: dict[str, set[str]] = {}
    episode_ids: set[str] = set()
    for episode in episodes:
        episode_id = episode.get("episode_id", "<missing>")
        if episode_id in episode_ids:
            issues.append(Issue("duplicate_episode_id", episode_id, "episode id is not unique"))
        episode_ids.add(episode_id)
        split = episode.get("split", "<missing>")
        groups_by_split.setdefault(split, set()).add(episode.get("group_id", "<missing>"))

        frames = episode.get("frames", [])
        indices = [frame.get("frame_index") for frame in frames]
        if indices != list(range(len(frames))):
            issues.append(Issue("noncontiguous_frame_index", episode_id, f"found {indices}"))
        timestamps = [frame.get("timestamp") for frame in frames]
        if any(not isinstance(value, (int, float)) for value in timestamps):
            issues.append(Issue("invalid_timestamp", episode_id, "timestamps must be numeric"))
        elif expected_delta is not None:
            for previous, current in zip(timestamps, timestamps[1:]):
                if current <= previous:
                    issues.append(Issue("nonmonotonic_timestamp", episode_id, f"{previous} -> {current}"))
                    break
                if abs((current - previous) - expected_delta) > 1e-6:
                    issues.append(Issue("timestamp_cadence", episode_id, f"expected {expected_delta}, found {current - previous}"))
                    break

        for frame_position, frame in enumerate(frames):
            action = frame.get("action")
            is_final = frame_position == len(frames) - 1
            if not is_final and action is None:
                issues.append(Issue("missing_transition_action", f"{episode_id}:{frame_position}", "non-final frame needs action"))
            if action is not None:
                if isinstance(action, bool) or not isinstance(action, (int, float)):
                    issues.append(Issue("invalid_action_type", f"{episode_id}:{frame_position}", f"found {type(action).__name__}"))
                elif isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
                    if not lower <= action <= upper:
                        issues.append(Issue("action_out_of_range", f"{episode_id}:{frame_position}", f"{action} not in [{lower}, {upper}]"))
            if frame.get("terminated") and not is_final:
                issues.append(Issue("early_termination", f"{episode_id}:{frame_position}", "terminated before final frame"))
        if frames and not frames[-1].get("terminated"):
            issues.append(Issue("missing_terminal_marker", episode_id, "final frame is not terminated"))

    split_names = sorted(groups_by_split)
    for index, left_split in enumerate(split_names):
        for right_split in split_names[index + 1 :]:
            overlap = groups_by_split[left_split] & groups_by_split[right_split]
            for group in sorted(overlap):
                issues.append(Issue("group_split_overlap", group, f"present in {left_split} and {right_split}"))
    return issues


def summarize(issues: list[Issue]) -> dict[str, int]:
    codes = {issue.code for issue in issues}
    return {
        "issue_count": len(issues),
        "issue_type_count": len(codes),
        "group_overlap_count": sum(issue.code == "group_split_overlap" for issue in issues),
    }
