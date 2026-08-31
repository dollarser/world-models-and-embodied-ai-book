from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from occupancy_fixture import (  # noqa: E402
    approach_affordances,
    build_occupancy,
    dynamic_update,
    occupied_iou,
    path_is_safe,
    shifted_occupied,
    trace_line,
)


class ActionableOccupancyTests(unittest.TestCase):
    def test_ray_marks_endpoint_but_not_cells_behind_it(self):
        grid = build_occupancy()
        self.assertEqual(grid[(3, 3)], "free")
        self.assertEqual(grid[(3, 4)], "occupied")
        self.assertEqual(grid[(3, 5)], "unknown")

    def test_line_trace_includes_both_endpoints(self):
        self.assertEqual(trace_line((0, 0), (0, 2)), [(0, 0), (0, 1), (0, 2)])

    def test_affordance_requires_reachable_free_approach(self):
        affordances = approach_affordances(build_occupancy())
        self.assertIn((3, 3), affordances)
        self.assertTrue(all(build_occupancy()[cell] == "free" for cell in affordances))

    def test_unknown_as_free_creates_false_safety(self):
        grid = build_occupancy()
        path = ((4, 1), (4, 2), (4, 3), (4, 4))
        self.assertFalse(path_is_safe(grid, path))
        self.assertTrue(path_is_safe(grid, path, unknown_is_free=True))
        self.assertFalse(path_is_safe(dynamic_update(grid), path))

    def test_one_cell_frame_shift_breaks_occupied_alignment(self):
        grid = build_occupancy()
        occupied = {cell for cell, status in grid.items() if status == "occupied"}
        self.assertEqual(occupied_iou(occupied, shifted_occupied(grid)), 0.0)

    def test_empty_occupancy_iou_is_defined(self):
        self.assertEqual(occupied_iou(set(), set()), 1.0)

    def test_out_of_bounds_is_never_treated_as_free(self):
        grid = build_occupancy()
        self.assertFalse(path_is_safe(grid, ((3, 0), (3, -1)), unknown_is_free=True))


if __name__ == "__main__":
    unittest.main()
