from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from protocol_fixture import (  # noqa: E402
    EPISODES,
    audit_episode_rows,
    comparability_warnings,
    exact_paired_cluster_bootstrap,
    evaluate_protocol,
    factorial_protocol_effects,
    wilson_interval,
)


class ProtocolFixtureTests(unittest.TestCase):
    def test_easy_goal_only_protocol_reports_all_success(self):
        result = evaluate_protocol("easy_goal_only")
        self.assertEqual(result["episode_count"], 4)
        self.assertEqual(result["success_rate"], 1.0)

    def test_safety_aware_protocol_rejects_collision_and_intervention(self):
        result = evaluate_protocol("full_safety_aware")
        self.assertEqual(result["episode_count"], 8)
        self.assertEqual(result["success_rate"], 0.625)
        self.assertEqual(result["collision_rate"], 0.125)
        self.assertEqual(result["intervention_rate"], 0.125)

    def test_factorial_cells_isolate_protocol_dimensions(self):
        self.assertEqual(evaluate_protocol("easy_safety_aware")["success_rate"], 1.0)
        self.assertEqual(evaluate_protocol("full_goal_only")["success_rate"], 0.875)

    def test_protocol_effects_are_not_additive_main_causes(self):
        effects = factorial_protocol_effects()
        self.assertEqual(effects["population_effect_under_goal_only"], -0.125)
        self.assertEqual(effects["population_effect_under_safety_aware"], -0.375)
        self.assertEqual(effects["safety_rule_effect_on_easy"], 0.0)
        self.assertEqual(effects["safety_rule_effect_on_full"], -0.25)
        self.assertEqual(effects["interaction"], -0.25)

    def test_valid_timeout_remains_in_the_denominator_as_failure(self):
        result = evaluate_protocol("full_safety_aware")
        self.assertEqual(result["attempted_count"], 8)
        self.assertEqual(result["valid_episode_count"], 8)
        self.assertEqual(result["truncated_episode_count"], 1)
        self.assertEqual(result["invalid_episode_count"], 0)
        self.assertEqual(result["success_count"], 5)

    def test_declared_invalid_attempt_is_reported_and_blocks_aggregation(self):
        invalid = dict(EPISODES[0], id="easy-invalid", valid=False, invalid_reason="reset_failed")
        rows = (*EPISODES, invalid)
        audit = audit_episode_rows(rows)
        self.assertEqual(audit["invalid_episode_count"], 1)
        self.assertEqual(audit["invalid_episode_ids"], ["easy-invalid"])
        with self.assertRaisesRegex(ValueError, "easy-invalid"):
            evaluate_protocol("easy_goal_only", rows)

    def test_simultaneous_terminal_and_timeout_is_accounted_in_both_counts(self):
        simultaneous = dict(EPISODES[0], id="easy-simultaneous", truncated=True)
        audit = audit_episode_rows((simultaneous,))
        self.assertEqual(audit["terminated_episode_count"], 1)
        self.assertEqual(audit["truncated_episode_count"], 1)

    def test_ended_row_requires_at_least_one_end_flag(self):
        malformed = dict(EPISODES[0], id="easy-malformed", terminated=False)
        with self.assertRaises(ValueError):
            audit_episode_rows((malformed,))

    def test_invalid_row_requires_a_reason(self):
        malformed = dict(EPISODES[0], id="easy-invalid", valid=False)
        with self.assertRaises(ValueError):
            audit_episode_rows((malformed,))
        with self.assertRaises(ValueError):
            evaluate_protocol("easy_goal_only", ("not-a-row",))

    def test_comparability_audit_finds_three_differences(self):
        self.assertEqual(
            comparability_warnings("easy_goal_only", "full_safety_aware"),
            ["task_population_differs", "success_definition_differs", "denominator_differs"],
        )

    def test_unknown_protocol_is_rejected(self):
        with self.assertRaises(KeyError):
            evaluate_protocol("unknown")

    def test_wilson_interval_contains_observed_proportion(self):
        interval = wilson_interval(5, 8)
        self.assertLess(interval["lower"], 0.625)
        self.assertGreater(interval["upper"], 0.625)

    def test_perfect_small_sample_does_not_imply_certainty(self):
        interval = wilson_interval(4, 4)
        self.assertLess(interval["lower"], 1.0)
        self.assertEqual(interval["upper"], 1.0)

    def test_wilson_interval_rejects_invalid_counts(self):
        for successes, trials in ((-1, 4), (5, 4), (0, 0)):
            with self.subTest(successes=successes, trials=trials):
                with self.assertRaises(ValueError):
                    wilson_interval(successes, trials)
        with self.assertRaises(TypeError):
            wilson_interval(True, 4)
        with self.assertRaises(ValueError):
            wilson_interval(2, 4, float("nan"))

    def test_cluster_macro_and_episode_micro_answer_different_estimands(self):
        result = exact_paired_cluster_bootstrap()
        self.assertEqual(result["pair_count"], 10)
        self.assertEqual(result["cluster_count"], 4)
        self.assertEqual(result["micro_paired_difference"], 0.3)
        self.assertEqual(result["macro_cluster_difference"], 0.0)
        self.assertEqual(result["cluster_pair_counts"], {"route-a": 4, "route-b": 4, "route-c": 1, "route-d": 1})

    def test_exact_cluster_bootstrap_preserves_pairs_and_resamples_routes(self):
        result = exact_paired_cluster_bootstrap()
        self.assertEqual(result["cluster_differences"], {"route-a": 0.0, "route-b": 1.0, "route-c": -1.0, "route-d": 0.0})
        self.assertEqual(result["cluster_bootstrap_95"], {"lower": -0.75, "upper": 0.75})
        self.assertEqual(result["bootstrap_resample_count"], 256)

    def test_cluster_bootstrap_rejects_broken_sampling_contracts(self):
        duplicate = (
            {"pair_id": "same", "cluster": "a", "candidate_success": True, "baseline_success": False},
            {"pair_id": "same", "cluster": "b", "candidate_success": False, "baseline_success": True},
        )
        with self.assertRaisesRegex(ValueError, "pair_id"):
            exact_paired_cluster_bootstrap(duplicate)
        one_cluster = (
            {"pair_id": "one", "cluster": "a", "candidate_success": True, "baseline_success": False},
        )
        with self.assertRaisesRegex(ValueError, "at least two clusters"):
            exact_paired_cluster_bootstrap(one_cluster)
        with self.assertRaises(ValueError):
            exact_paired_cluster_bootstrap(confidence=1.0)
        with self.assertRaisesRegex(ValueError, "max_exact_resamples"):
            exact_paired_cluster_bootstrap(max_exact_resamples=100)


if __name__ == "__main__":
    unittest.main()
