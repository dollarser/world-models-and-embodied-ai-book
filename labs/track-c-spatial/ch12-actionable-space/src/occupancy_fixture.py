"""Tri-state occupancy and actionability fixtures for Chapter 12."""

from __future__ import annotations

from collections import deque


GRID_SIZE = 7
ORIGIN = (3, 0)
ENDPOINTS = ((1, 4), (3, 4), (5, 4))
Cell = tuple[int, int]


def trace_line(start: Cell, end: Cell) -> list[Cell]:
    """Integer Bresenham line including both endpoints."""
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


def path_is_safe(grid: dict[Cell, str], path: tuple[Cell, ...], unknown_is_free: bool = False) -> bool:
    for cell in path:
        if cell not in grid:
            return False
        status = grid[cell]
        if status == "occupied" or (status == "unknown" and not unknown_is_free):
            return False
    return True


def occupied_iou(first: set[Cell], second: set[Cell]) -> float:
    union = first | second
    return len(first & second) / len(union) if union else 1.0


def shifted_occupied(grid: dict[Cell, str], dx: int = 1, dy: int = 0) -> set[Cell]:
    return {
        (x + dx, y + dy)
        for (x, y), status in grid.items()
        if status == "occupied" and 0 <= x + dx < GRID_SIZE and 0 <= y + dy < GRID_SIZE
    }


def dynamic_update(grid: dict[Cell, str], old: Cell = (3, 4), new: Cell = (4, 4)) -> dict[Cell, str]:
    updated = dict(grid)
    updated[old] = "free"
    updated[new] = "occupied"
    return updated


def evaluate() -> dict[str, object]:
    grid = build_occupancy()
    counts = {status: sum(value == status for value in grid.values()) for status in ("free", "occupied", "unknown")}
    occupied = {cell for cell, status in grid.items() if status == "occupied"}
    shifted = shifted_occupied(grid)
    dynamic_path = ((4, 1), (4, 2), (4, 3), (4, 4))
    updated = dynamic_update(grid)
    return {
        "state_counts": counts,
        "occluded_cell_is_unknown": grid[(3, 5)] == "unknown",
        "reachable_free_count": len(reachable_free(grid)),
        "approach_affordance_count": len(approach_affordances(grid)),
        "one_cell_shift_occupied_iou": occupied_iou(occupied, shifted),
        "dynamic_path_safe_tristate_before_update": path_is_safe(grid, dynamic_path),
        "dynamic_path_safe_binary_unknown_as_free": path_is_safe(grid, dynamic_path, unknown_is_free=True),
        "dynamic_path_safe_after_update": path_is_safe(updated, dynamic_path),
    }
