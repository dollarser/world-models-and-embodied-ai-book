"""Tri-state occupancy and actionability fixtures for Chapter 12."""

from __future__ import annotations

from collections import deque
import math


GRID_SIZE = 7
ORIGIN = (3, 0)
ENDPOINTS = ((1, 4), (3, 4), (5, 4))
Cell = tuple[int, int]
VALID_STATES = frozenset({"free", "occupied", "unknown"})
GRID_ORIGIN_XY_M = (0.0, 0.0)
GRID_RESOLUTION_M = 0.5


def _validate_cell(cell: Cell, *, name: str, require_in_bounds: bool = True) -> None:
    if (
        not isinstance(cell, tuple)
        or len(cell) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) for value in cell)
    ):
        raise ValueError(f"{name} must be a pair of integer grid coordinates")
    if require_in_bounds and not (0 <= cell[0] < GRID_SIZE and 0 <= cell[1] < GRID_SIZE):
        raise ValueError(f"{name} is outside the {GRID_SIZE}x{GRID_SIZE} grid")


def _validate_grid(grid: dict[Cell, str]) -> None:
    if not isinstance(grid, dict):
        raise ValueError("grid must be a dictionary")
    for cell in grid:
        _validate_cell(cell, name="grid cell")
    expected = {(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
    if set(grid) != expected:
        raise ValueError("grid must contain exactly the fixture's in-bounds cells")
    if any(status not in VALID_STATES for status in grid.values()):
        raise ValueError("grid contains an invalid occupancy state")


def _validate_metric_pair(value: tuple[float, float], *, name: str) -> None:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in value
        )
    ):
        raise ValueError(f"{name} must be a finite metric-coordinate pair")


def world_to_cell(
    point_xy_m: tuple[float, float],
    *,
    origin_xy_m: tuple[float, float] = GRID_ORIGIN_XY_M,
    resolution_m: float = GRID_RESOLUTION_M,
) -> Cell:
    """Map a metric point to half-open grid cells using floor, not truncation.

    Cell ``(i, j)`` covers ``[origin_x + i*r, origin_x + (i+1)*r)``
    by ``[origin_y + j*r, origin_y + (j+1)*r)``.  The returned cell may be
    outside this fixture's finite grid; callers must check bounds explicitly.
    """
    _validate_metric_pair(point_xy_m, name="point_xy_m")
    _validate_metric_pair(origin_xy_m, name="origin_xy_m")
    if (
        isinstance(resolution_m, bool)
        or not isinstance(resolution_m, (int, float))
        or not math.isfinite(resolution_m)
        or resolution_m <= 0
    ):
        raise ValueError("resolution_m must be a finite positive number")
    return (
        math.floor((point_xy_m[0] - origin_xy_m[0]) / resolution_m),
        math.floor((point_xy_m[1] - origin_xy_m[1]) / resolution_m),
    )


def cell_center(
    cell: Cell,
    *,
    origin_xy_m: tuple[float, float] = GRID_ORIGIN_XY_M,
    resolution_m: float = GRID_RESOLUTION_M,
) -> tuple[float, float]:
    """Return the metric center of a cell under the same grid contract."""
    _validate_cell(cell, name="cell", require_in_bounds=False)
    _validate_metric_pair(origin_xy_m, name="origin_xy_m")
    if (
        isinstance(resolution_m, bool)
        or not isinstance(resolution_m, (int, float))
        or not math.isfinite(resolution_m)
        or resolution_m <= 0
    ):
        raise ValueError("resolution_m must be a finite positive number")
    return (
        origin_xy_m[0] + (cell[0] + 0.5) * resolution_m,
        origin_xy_m[1] + (cell[1] + 0.5) * resolution_m,
    )


def cell_is_in_bounds(cell: Cell) -> bool:
    _validate_cell(cell, name="cell", require_in_bounds=False)
    return 0 <= cell[0] < GRID_SIZE and 0 <= cell[1] < GRID_SIZE


def grid_boundary_report() -> dict[str, object]:
    """Expose correct half-open indexing and two common boundary failures."""
    center_point = (0.75, 0.25)
    center_cell = world_to_cell(center_point)
    just_before_origin = (-0.01, 0.25)
    floor_cell = world_to_cell(just_before_origin)
    truncation_cell = (
        int((just_before_origin[0] - GRID_ORIGIN_XY_M[0]) / GRID_RESOLUTION_M),
        int((just_before_origin[1] - GRID_ORIGIN_XY_M[1]) / GRID_RESOLUTION_M),
    )
    upper_edge_cell = world_to_cell((GRID_SIZE * GRID_RESOLUTION_M, 0.25))
    return {
        "origin_xy_m": list(GRID_ORIGIN_XY_M),
        "resolution_m": GRID_RESOLUTION_M,
        "axis_order": "(x_index, y_index)",
        "interval_convention": "half-open [lower, upper)",
        "center_point_xy_m": list(center_point),
        "center_point_cell": list(center_cell),
        "center_round_trip_xy_m": list(cell_center(center_cell)),
        "negative_edge_point_xy_m": list(just_before_origin),
        "negative_edge_floor_cell": list(floor_cell),
        "negative_edge_floor_in_bounds": cell_is_in_bounds(floor_cell),
        "negative_edge_truncation_cell": list(truncation_cell),
        "negative_edge_truncation_in_bounds": cell_is_in_bounds(truncation_cell),
        "upper_edge_cell": list(upper_edge_cell),
        "upper_edge_in_bounds": cell_is_in_bounds(upper_edge_cell),
    }


def trace_line(start: Cell, end: Cell) -> list[Cell]:
    """Integer Bresenham line including both endpoints."""
    _validate_cell(start, name="start", require_in_bounds=False)
    _validate_cell(end, name="end", require_in_bounds=False)
    x0, y0 = start
    x1, y1 = end
    dx, sx = abs(x1 - x0), 1 if x0 < x1 else -1
    dy, sy = -abs(y1 - y0), 1 if y0 < y1 else -1
    error = dx + dy
    cells = []
    while True:
        cells.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return cells
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def build_occupancy(endpoints: tuple[Cell, ...] = ENDPOINTS) -> dict[Cell, str]:
    """Mark observed ray interiors free, returns occupied, and all else unknown."""
    if not endpoints:
        raise ValueError("at least one depth-return endpoint is required")
    for index, endpoint in enumerate(endpoints):
        _validate_cell(endpoint, name=f"endpoints[{index}]")
    grid = {(x, y): "unknown" for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
    free = set()
    for endpoint in endpoints:
        free.update(trace_line(ORIGIN, endpoint)[:-1])
    for cell in free:
        grid[cell] = "free"
    for endpoint in endpoints:
        grid[endpoint] = "occupied"
    return grid


def neighbors(cell: Cell) -> tuple[Cell, ...]:
    x, y = cell
    return tuple(
        candidate
        for candidate in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        if 0 <= candidate[0] < GRID_SIZE and 0 <= candidate[1] < GRID_SIZE
    )


def reachable_free(grid: dict[Cell, str], start: Cell = ORIGIN) -> set[Cell]:
    if grid[start] != "free":
        return set()
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for candidate in neighbors(current):
            if candidate not in visited and grid[candidate] == "free":
                visited.add(candidate)
                queue.append(candidate)
    return visited


def approach_affordances(grid: dict[Cell, str]) -> set[Cell]:
    """Reachable free cells adjacent to an occupied cell."""
    reachable = reachable_free(grid)
    occupied = {cell for cell, status in grid.items() if status == "occupied"}
    return {cell for cell in reachable if any(candidate in occupied for candidate in neighbors(cell))}


def path_risk_report(
    grid: dict[Cell, str],
    path: tuple[Cell, ...],
    unknown_is_free: bool = False,
    footprint_radius_cells: int = 0,
    interpolate_segments: bool = True,
) -> dict[str, int | bool]:
    """Audit a square footprint over rasterized segments of a static path.

    Bresenham interpolation closes gaps between integer waypoints. It is still
    a discrete grid approximation, not continuous collision checking.
    """
    _validate_grid(grid)
    if not isinstance(unknown_is_free, bool):
        raise ValueError("unknown_is_free must be boolean")
    if (
        isinstance(footprint_radius_cells, bool)
        or not isinstance(footprint_radius_cells, int)
        or footprint_radius_cells < 0
    ):
        raise ValueError("footprint_radius_cells must be a non-negative integer")
    if not isinstance(interpolate_segments, bool):
        raise ValueError("interpolate_segments must be boolean")
    if not path:
        raise ValueError("path must contain at least one cell")
    for index, cell in enumerate(path):
        _validate_cell(cell, name=f"path[{index}]", require_in_bounds=False)

    if interpolate_segments:
        center_cells = set(path[:1])
        for start, end in zip(path, path[1:]):
            center_cells.update(trace_line(start, end))
    else:
        center_cells = set(path)

    swept = {
        (x + dx, y + dy)
        for x, y in center_cells
        for dx in range(-footprint_radius_cells, footprint_radius_cells + 1)
        for dy in range(-footprint_radius_cells, footprint_radius_cells + 1)
    }
    in_bounds = swept & set(grid)
    occupied_count = sum(grid[cell] == "occupied" for cell in in_bounds)
    unknown_count = sum(grid[cell] == "unknown" for cell in in_bounds)
    out_of_bounds_count = len(swept - in_bounds)
    return {
        "path_step_count": len(path),
        "sampled_waypoint_count": len(path),
        "traced_center_cell_count": len(center_cells),
        "segment_interpolation_enabled": interpolate_segments,
        "checked_cell_count": len(in_bounds),
        "occupied_cell_count": occupied_count,
        "unknown_cell_count": unknown_count,
        "out_of_bounds_cell_count": out_of_bounds_count,
        "safe": occupied_count == 0
        and out_of_bounds_count == 0
        and (unknown_is_free or unknown_count == 0),
    }


def path_is_safe(
    grid: dict[Cell, str],
    path: tuple[Cell, ...],
    unknown_is_free: bool = False,
    footprint_radius_cells: int = 0,
    interpolate_segments: bool = True,
) -> bool:
    return bool(
        path_risk_report(
            grid,
            path,
            unknown_is_free,
            footprint_radius_cells,
            interpolate_segments,
        )["safe"]
    )


def occupied_iou(first: set[Cell], second: set[Cell]) -> float:
    union = first | second
    return len(first & second) / len(union) if union else 1.0


def shifted_occupied(grid: dict[Cell, str], dx: int = 1, dy: int = 0) -> set[Cell]:
    return {
        (x + dx, y + dy)
        for (x, y), status in grid.items()
        if status == "occupied" and 0 <= x + dx < GRID_SIZE and 0 <= y + dy < GRID_SIZE
    }


def dynamic_update(
    grid: dict[Cell, str],
    old: Cell = (3, 4),
    new: Cell = (4, 4),
    old_cell_observed_free: bool = False,
) -> dict[Cell, str]:
    """Move a return without inventing clearing evidence at its old cell."""
    _validate_grid(grid)
    _validate_cell(old, name="old")
    _validate_cell(new, name="new")
    if not isinstance(old_cell_observed_free, bool):
        raise ValueError("old_cell_observed_free must be boolean")
    updated = dict(grid)
    updated[old] = "free" if old_cell_observed_free else "unknown"
    updated[new] = "occupied"
    return updated


def expire_stale_observations(
    grid: dict[Cell, str],
    observed_at: dict[Cell, int],
    current_step: int,
    max_age_steps: int,
) -> dict[Cell, str]:
    """Return explicitly timestamped stale evidence to unknown."""
    _validate_grid(grid)
    for name, value in (("current_step", current_step), ("max_age_steps", max_age_steps)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    updated = dict(grid)
    for cell, step in observed_at.items():
        _validate_cell(cell, name="observed_at cell")
        if isinstance(step, bool) or not isinstance(step, int) or not 0 <= step <= current_step:
            raise ValueError("observation steps must be integers between zero and current_step")
        if current_step - step > max_age_steps and updated[cell] != "unknown":
            updated[cell] = "unknown"
    return updated


def evaluate() -> dict[str, object]:
    grid = build_occupancy()
    counts = {status: sum(value == status for value in grid.values()) for status in ("free", "occupied", "unknown")}
    occupied = {cell for cell, status in grid.items() if status == "occupied"}
    shifted = shifted_occupied(grid)
    dynamic_path = ((4, 1), (4, 2), (4, 3), (4, 4))
    updated = dynamic_update(grid)
    updated_with_clearing = dynamic_update(grid, old_cell_observed_free=True)
    centerline_path = ((3, 1), (3, 2), (3, 3))
    footprint_report = path_risk_report(grid, centerline_path, footprint_radius_cells=1)
    fresh_path = ((3, 0), (3, 1), (3, 2), (3, 3))
    stale_grid = expire_stale_observations(grid, {(3, 2): 0}, current_step=3, max_age_steps=2)
    sparse_waypoints = ((3, 3), (3, 5))
    sparse_waypoint_only_report = path_risk_report(
        grid, sparse_waypoints, unknown_is_free=True, interpolate_segments=False
    )
    sparse_segment_report = path_risk_report(
        grid, sparse_waypoints, unknown_is_free=True, interpolate_segments=True
    )
    return {
        "state_counts": counts,
        "occluded_cell_is_unknown": grid[(3, 5)] == "unknown",
        "reachable_free_count": len(reachable_free(grid)),
        "approach_affordance_count": len(approach_affordances(grid)),
        "one_cell_shift_occupied_iou": occupied_iou(occupied, shifted),
        "dynamic_path_safe_tristate_before_update": path_is_safe(grid, dynamic_path),
        "dynamic_path_safe_binary_unknown_as_free": path_is_safe(grid, dynamic_path, unknown_is_free=True),
        "dynamic_path_safe_after_update": path_is_safe(updated, dynamic_path),
        "dynamic_old_cell_without_clearing_evidence": updated[(3, 4)],
        "dynamic_old_cell_with_clearing_evidence": updated_with_clearing[(3, 4)],
        "centerline_point_path_safe": path_is_safe(grid, centerline_path),
        "centerline_radius_one_footprint_report": footprint_report,
        "fresh_free_path_safe": path_is_safe(grid, fresh_path),
        "stale_free_path_safe": path_is_safe(stale_grid, fresh_path),
        "expired_cell_count": sum(grid[cell] != stale_grid[cell] for cell in grid),
        "sparse_waypoint_only_report": sparse_waypoint_only_report,
        "sparse_segment_report": sparse_segment_report,
        "grid_boundary_report": grid_boundary_report(),
    }
