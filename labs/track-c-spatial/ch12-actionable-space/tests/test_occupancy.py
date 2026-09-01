from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from occupancy_fixture import (  # noqa: E402
    approach_affordances,
    build_occupancy,
    dynamic_update,
    expire_stale_observations,
    occupied_iou,
    path_is_safe,
    path_risk_report,
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

    def test_dynamic_move_does_not_invent_clearing_evidence(self):
        grid = build_occupancy()
        self.assertEqual(dynamic_update(grid)[(3, 4)], "unknown")
        self.assertEqual(dynamic_update(grid, old_cell_observed_free=True)[(3, 4)], "free")

    def test_footprint_can_invalidate_a_safe_centerline(self):
        grid = build_occupancy()
        path = ((3, 1), (3, 2), (3, 3))
        self.assertTrue(path_is_safe(grid, path))
        report = path_risk_report(grid, path, footprint_radius_cells=1)
        self.assertFalse(report["safe"])
        self.assertEqual(report["path_step_count"], 3)
        self.assertGreater(report["occupied_cell_count"] + report["unknown_cell_count"], 0)

    def test_stale_free_evidence_expires_to_unknown(self):
        grid = build_occupancy()
        path = ((3, 0), (3, 1), (3, 2), (3, 3))
        self.assertTrue(path_is_safe(grid, path))
        expired = expire_stale_observations(grid, {(3, 2): 0}, current_step=3, max_age_steps=2)
        self.assertEqual(expired[(3, 2)], "unknown")
        self.assertFalse(path_is_safe(expired, path))

    def test_one_cell_frame_shift_breaks_occupied_alignment(self):
        grid = build_occupancy()
        occupied = {cell for cell, status in grid.items() if status == "occupied"}
        self.assertEqual(occupied_iou(occupied, shifted_occupied(grid)), 0.0)

    def test_empty_occupancy_iou_is_defined(self):
        self.assertEqual(occupied_iou(set(), set()), 1.0)

    def test_out_of_bounds_is_never_treated_as_free(self):
        grid = build_occupancy()
        self.assertFalse(path_is_safe(grid, ((3, 0), (3, -1)), unknown_is_free=True))

    def test_empty_path_and_invalid_footprint_are_rejected(self):
        grid = build_occupancy()
        with self.assertRaises(ValueError):
            path_is_safe(grid, ())
        with self.assertRaises(ValueError):
            path_is_safe(grid, ((3, 0),), footprint_radius_cells=-1)

    def test_out_of_bounds_returns_and_updates_are_rejected(self):
        with self.assertRaises(ValueError):
            build_occupancy(((3, 7),))
        with self.assertRaises(ValueError):
            dynamic_update(build_occupancy(), new=(7, 4))

    def test_future_observation_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            expire_stale_observations(build_occupancy(), {(3, 2): 4}, current_step=3, max_age_steps=2)


if __name__ == "__main__":
    unittest.main()
