"""Standard-library data-contract audit for Chapter 4 fixtures."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path
from typing import Any


REQUIRED_FEATURES = {"observation.state", "action", "timestamp"}
IDENTITY_OVERLAP_CODES = {
    "source_asset_id": "source_asset_split_overlap",
    "content_fingerprint": "content_fingerprint_split_overlap",
    "similarity_cluster_id": "similarity_cluster_split_overlap",
}


@dataclass(frozen=True)
class Issue:
    code: str
    location: str
    detail: str


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)


def bootstrap_allowed(frame: dict[str, Any]) -> bool:
    """Return the continuation-mask semantics after a validated final frame.

    A natural MDP termination stops bootstrapping. An external truncation ends
    the recorded sequence but does not assert that the underlying state is
    terminal, so a value target may still bootstrap from the final observation.
    """

    return not frame.get("terminated", False)


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
    expected_delta = 1.0 / fps if is_finite_number(fps) and fps > 0 else None
    cadence_tolerance = dataset.get("cadence_tolerance_seconds", 1e-6)
    if not is_finite_number(cadence_tolerance) or cadence_tolerance < 0:
        issues.append(Issue("invalid_cadence_tolerance", "dataset.cadence_tolerance_seconds", "must be finite and non-negative"))
        cadence_tolerance = 0.0

    sensor_sync = dataset.get("sensor_sync")
    required_sensors: list[str] = []
    max_sensor_skew: float | None = None
    if sensor_sync is not None:
        if not isinstance(sensor_sync, dict):
            issues.append(Issue("invalid_sensor_sync_contract", "dataset.sensor_sync", "must be an object"))
        else:
            configured_sensors = sensor_sync.get("required_sensors")
            configured_skew = sensor_sync.get("max_skew_seconds")
            if (
                not isinstance(configured_sensors, list)
                or not configured_sensors
                or any(not isinstance(name, str) or not name for name in configured_sensors)
                or len(configured_sensors) != len(set(configured_sensors))
            ):
                issues.append(
                    Issue("invalid_sensor_sync_contract", "dataset.sensor_sync.required_sensors", "must be unique non-empty names")
                )
            else:
                required_sensors = configured_sensors
            if not is_finite_number(configured_skew) or configured_skew < 0:
                issues.append(
                    Issue("invalid_sensor_sync_contract", "dataset.sensor_sync.max_skew_seconds", "must be finite and non-negative")
                )
            else:
                max_sensor_skew = float(configured_skew)

    action_range = dataset.get("action_range", [None, None])
    lower, upper = action_range if isinstance(action_range, list) and len(action_range) == 2 else (None, None)

    groups_by_split: dict[str, set[str]] = {}
    identities_by_field_and_split: dict[str, dict[str, set[str]]] = {
        field: {} for field in IDENTITY_OVERLAP_CODES
    }
    episode_ids: set[str] = set()
    for episode in episodes:
        episode_id = episode.get("episode_id", "<missing>")
        if episode_id in episode_ids:
            issues.append(Issue("duplicate_episode_id", episode_id, "episode id is not unique"))
        episode_ids.add(episode_id)
        split = episode.get("split", "<missing>")
        groups_by_split.setdefault(split, set()).add(episode.get("group_id", "<missing>"))
        for field in IDENTITY_OVERLAP_CODES:
            value = episode.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(
                    Issue(
                        "invalid_episode_identity",
                        f"{episode_id}:{field}",
                        "must be a non-empty string",
                    )
                )
                continue
            identities_by_field_and_split[field].setdefault(split, set()).add(value)

        frames = episode.get("frames", [])
        last_sensor_timestamps: dict[str, float] = {}
        indices = [frame.get("frame_index") for frame in frames]
        if indices != list(range(len(frames))):
            issues.append(Issue("noncontiguous_frame_index", episode_id, f"found {indices}"))
        timestamps = [frame.get("timestamp") for frame in frames]
        if any(not is_finite_number(value) for value in timestamps):
            issues.append(Issue("invalid_timestamp", episode_id, "timestamps must be finite numeric values"))
        elif expected_delta is not None:
            for previous, current in zip(timestamps, timestamps[1:]):
                if current <= previous:
                    issues.append(Issue("nonmonotonic_timestamp", episode_id, f"{previous} -> {current}"))
                    break
                if abs((current - previous) - expected_delta) > cadence_tolerance:
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
                elif not isfinite(action):
                    issues.append(Issue("nonfinite_action", f"{episode_id}:{frame_position}", f"found {action}"))
                elif isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
                    if not lower <= action <= upper:
                        issues.append(Issue("action_out_of_range", f"{episode_id}:{frame_position}", f"{action} not in [{lower}, {upper}]"))

            terminated = frame.get("terminated")
            truncated = frame.get("truncated")
            if not isinstance(terminated, bool) or not isinstance(truncated, bool):
                issues.append(
                    Issue("invalid_end_flag", f"{episode_id}:{frame_position}", "terminated and truncated must be booleans")
                )
            else:
                if not is_final and (terminated or truncated):
                    issues.append(Issue("early_episode_end", f"{episode_id}:{frame_position}", "end flag before final frame"))
                if is_final and not (terminated or truncated):
                    issues.append(Issue("missing_episode_end", episode_id, "final frame needs terminated or truncated"))
                if is_final and (terminated or truncated):
                    reason = frame.get("end_reason")
                    if not isinstance(reason, str) or not reason:
                        issues.append(Issue("missing_end_reason", episode_id, "ended episode needs a non-empty reason"))

            sensor_records = frame.get("sensors")
            if required_sensors and not isinstance(sensor_records, dict):
                issues.append(
                    Issue("missing_sensor_record", f"{episode_id}:{frame_position}", "required sensors need explicit records")
                )
                continue
            for sensor_name in required_sensors:
                record = sensor_records.get(sensor_name) if isinstance(sensor_records, dict) else None
                location = f"{episode_id}:{frame_position}:{sensor_name}"
                if not isinstance(record, dict):
                    issues.append(Issue("missing_sensor_record", location, "use valid=false for a missing sample"))
                    continue
                valid = record.get("valid")
                sensor_timestamp = record.get("timestamp")
                if not isinstance(valid, bool):
                    issues.append(Issue("invalid_sensor_validity", location, "valid must be boolean"))
                    continue
                if not valid:
                    if sensor_timestamp is not None:
                        issues.append(Issue("masked_sensor_has_timestamp", location, "masked sample timestamp must be null"))
                    continue
                if not is_finite_number(sensor_timestamp):
                    issues.append(Issue("invalid_sensor_timestamp", location, "valid sample needs a finite timestamp"))
                    continue
                previous_sensor_timestamp = last_sensor_timestamps.get(sensor_name)
                if previous_sensor_timestamp is not None and sensor_timestamp <= previous_sensor_timestamp:
                    issues.append(
                        Issue(
                            "nonmonotonic_sensor_timestamp",
                            location,
                            f"{previous_sensor_timestamp} -> {sensor_timestamp}",
                        )
                    )
                last_sensor_timestamps[sensor_name] = float(sensor_timestamp)
                frame_timestamp = frame.get("timestamp")
                if (
                    max_sensor_skew is not None
                    and is_finite_number(frame_timestamp)
                    and abs(sensor_timestamp - frame_timestamp) > max_sensor_skew
                ):
                    issues.append(
                        Issue(
                            "sensor_sync_skew",
                            location,
                            f"skew {abs(sensor_timestamp - frame_timestamp)} exceeds {max_sensor_skew}",
                        )
                    )

    split_names = sorted(groups_by_split)
    for index, left_split in enumerate(split_names):
        for right_split in split_names[index + 1 :]:
            overlap = groups_by_split[left_split] & groups_by_split[right_split]
            for group in sorted(overlap):
                issues.append(Issue("group_split_overlap", group, f"present in {left_split} and {right_split}"))
            for field, overlap_code in IDENTITY_OVERLAP_CODES.items():
                values_by_split = identities_by_field_and_split[field]
                overlap = values_by_split.get(left_split, set()) & values_by_split.get(right_split, set())
                for value in sorted(overlap):
                    issues.append(Issue(overlap_code, value, f"{field} present in {left_split} and {right_split}"))
    return issues


def summarize(issues: list[Issue]) -> dict[str, int]:
    codes = {issue.code for issue in issues}
    return {
        "issue_count": len(issues),
        "issue_type_count": len(codes),
        "group_overlap_count": sum(issue.code == "group_split_overlap" for issue in issues),
        "identity_overlap_count": sum(issue.code in IDENTITY_OVERLAP_CODES.values() for issue in issues),
    }


def describe_fixture(fixture: dict[str, Any]) -> dict[str, int | float]:
    """Return transparent coverage counts, not a dataset-quality score."""

    episodes = fixture.get("episodes", [])
    frames = [frame for episode in episodes for frame in episode.get("frames", [])]
    valid_sensor_skews = []
    masked_sensor_samples = 0
    for frame in frames:
        frame_timestamp = frame.get("timestamp")
        for record in frame.get("sensors", {}).values():
            if record.get("valid") is False:
                masked_sensor_samples += 1
            elif record.get("valid") is True and is_finite_number(record.get("timestamp")) and is_finite_number(frame_timestamp):
                valid_sensor_skews.append(abs(record["timestamp"] - frame_timestamp))
    return {
        "episode_count": len(episodes),
        "frame_count": len(frames),
        "terminated_episode_count": sum(bool(episode.get("frames")) and episode["frames"][-1].get("terminated") is True for episode in episodes),
        "truncated_episode_count": sum(bool(episode.get("frames")) and episode["frames"][-1].get("truncated") is True for episode in episodes),
        "masked_sensor_sample_count": masked_sensor_samples,
        "maximum_valid_sensor_skew_seconds": round(max(valid_sensor_skews, default=0.0), 6),
    }
