from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from protocol_fixture import (  # noqa: E402
    CHECKPOINT_SELECTION_ROWS,
    EPISODES,
    audit_episode_rows,
    checkpoint_selection_audit,
    comparability_warnings,
    exact_mcnemar_report,
    exact_paired_cluster_bootstrap,
    evaluate_protocol,
    factorial_protocol_effects,
    hoeffding_mean_interval,
    hoeffding_required_samples,
    paired_margin_diagnostic,
    wilson_interval,
    zero_event_pseudoreplication_audit,
    zero_event_upper_bound,
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

    def test_zero_events_still_have_a_positive_risk_upper_bound(self):
        self.assertEqual(zero_event_upper_bound(20), 0.139108)
        self.assertEqual(zero_event_upper_bound(100), 0.029513)
        self.assertEqual(zero_event_upper_bound(1000), 0.002991)

    def test_zero_event_bound_shrinks_with_exposure(self):
        self.assertGreater(zero_event_upper_bound(20), zero_event_upper_bound(100))
        self.assertGreater(zero_event_upper_bound(100), zero_event_upper_bound(1000))

    def test_zero_event_bound_rejects_invalid_inputs(self):
        for trials in (0, -1):
            with self.assertRaises(ValueError):
                zero_event_upper_bound(trials)
        with self.assertRaises(TypeError):
            zero_event_upper_bound(True)
        for confidence in (0.0, 1.0, float("nan")):
            with self.assertRaises(ValueError):
                zero_event_upper_bound(100, confidence)

    def test_zero_event_repeats_do_not_create_independent_clusters(self):
        audit = zero_event_pseudoreplication_audit()
        self.assertEqual(audit["nominal_episode_count"], 100)
        self.assertEqual(audit["episode_iid_upper_if_independent"], 0.029513)
        self.assertEqual(audit["cluster_incidence_upper_if_clusters_independent"], 0.258866)
        self.assertTrue(audit["estimands_are_different"])

    def test_repetition_does_not_create_clusters_and_changes_cluster_outcome(self):
        one_replay = zero_event_pseudoreplication_audit(repeats_per_cluster=1)
        ten_replays = zero_event_pseudoreplication_audit(repeats_per_cluster=10)
        self.assertEqual(
            one_replay["cluster_incidence_upper_if_clusters_independent"],
            ten_replays["cluster_incidence_upper_if_clusters_independent"],
        )
        self.assertGreater(
            one_replay["episode_iid_upper_if_independent"],
            ten_replays["episode_iid_upper_if_independent"],
        )
        self.assertNotEqual(one_replay["cluster_estimand"], ten_replays["cluster_estimand"])

    def test_pseudoreplication_audit_rejects_invalid_cluster_counts(self):
        for clusters, repeats in ((0, 10), (10, 0), (-1, 10)):
            with self.subTest(clusters=clusters, repeats=repeats):
                with self.assertRaises(ValueError):
                    zero_event_pseudoreplication_audit(clusters, repeats)
        with self.assertRaises(TypeError):
            zero_event_pseudoreplication_audit(True, 10)

    def test_checkpoint_selection_keeps_final_set_out_of_selection(self):
        audit = checkpoint_selection_audit()
        self.assertEqual(audit["selection_split_selected_checkpoint"], "checkpoint-a")
        self.assertEqual(audit["selection_selected_final_score"], 0.5)
        self.assertTrue(audit["split_roles_are_distinct"])

    def test_final_set_reuse_exposes_an_authored_confirmation_gap(self):
        audit = checkpoint_selection_audit()
        self.assertEqual(audit["test_reuse_selected_checkpoint"], "checkpoint-d")
        self.assertEqual(audit["test_reuse_reported_final_score"], 0.75)
        self.assertEqual(audit["test_reuse_confirmation_score"], 0.5)
        self.assertEqual(audit["test_reuse_authored_optimism_gap"], 0.25)

    def test_checkpoint_selection_rejects_ambiguous_or_invalid_rows(self):
        duplicate = (*CHECKPOINT_SELECTION_ROWS, dict(CHECKPOINT_SELECTION_ROWS[0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            checkpoint_selection_audit(duplicate)
        tied = tuple(
            dict(row, final_score=0.75) if row["checkpoint"] == "checkpoint-c" else row
            for row in CHECKPOINT_SELECTION_ROWS
        )
        with self.assertRaisesRegex(ValueError, "exactly one"):
            checkpoint_selection_audit(tied)
        for bad_value in (True, float("nan"), 1.1):
            malformed = (dict(CHECKPOINT_SELECTION_ROWS[0], selection_score=bad_value), *CHECKPOINT_SELECTION_ROWS[1:])
            with self.subTest(bad_value=bad_value):
                with self.assertRaises((TypeError, ValueError)):
                    checkpoint_selection_audit(malformed)

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

    def test_identical_margins_can_hide_different_pairing_uncertainty(self):
        diagnostic = paired_margin_diagnostic()
        high = diagnostic["high_concordance"]
        more = diagnostic["more_discordant"]
        self.assertTrue(diagnostic["marginal_rates_equal_across_tables"])
        for report in (high, more):
            self.assertEqual(report["candidate_success_rate"], 0.6)
            self.assertEqual(report["baseline_success_rate"], 0.4)
            self.assertEqual(report["paired_difference"], 0.2)
        self.assertEqual(high["discordant_pair_count"], 4)
        self.assertEqual(more["discordant_pair_count"], 12)
        self.assertEqual(high["exact_conditional_two_sided_p"], 0.125)
        self.assertEqual(more["exact_conditional_two_sided_p"], 0.387695)

    def test_exact_mcnemar_uses_only_discordant_direction_counts(self):
        tied = (
            {"pair_id": "a", "candidate_success": True, "baseline_success": True},
            {"pair_id": "b", "candidate_success": False, "baseline_success": False},
        )
        report = exact_mcnemar_report(tied)
        self.assertEqual(report["discordant_pair_count"], 0)
        self.assertEqual(report["exact_conditional_two_sided_p"], 1.0)

    def test_paired_difference_interval_is_separate_from_mcnemar_p_value(self):
        diagnostic = paired_margin_diagnostic()
        high = diagnostic["high_concordance"]
        more = diagnostic["more_discordant"]
        expected = {
            "sample_count": 20,
            "mean": 0.2,
            "radius": 0.607361,
            "lower": -0.407361,
            "upper": 0.807361,
        }
        self.assertEqual(high["paired_difference_hoeffding_95"], expected)
        self.assertEqual(more["paired_difference_hoeffding_95"], expected)
        self.assertNotEqual(
            high["exact_conditional_two_sided_p"],
            more["exact_conditional_two_sided_p"],
        )

    def test_twenty_pairs_do_not_fit_inside_predeclared_equivalence_band(self):
        for report in paired_margin_diagnostic().values():
            if isinstance(report, dict) and "interval_within_practical_equivalence_band" in report:
                self.assertEqual(report["predeclared_practical_equivalence_margin"], 0.3)
                self.assertFalse(report["interval_within_practical_equivalence_band"])
                self.assertEqual(
                    report["independent_pairs_sufficient_for_0_1_hoeffding_radius"], 738
                )

    def test_hoeffding_interval_rejects_invalid_contracts(self):
        with self.assertRaises(ValueError):
            hoeffding_mean_interval(())
        with self.assertRaises(ValueError):
            hoeffding_mean_interval((2.0,))
        with self.assertRaises(TypeError):
            hoeffding_mean_interval((True,))
        with self.assertRaises(ValueError):
            hoeffding_required_samples(0.0)
        with self.assertRaises(ValueError):
            hoeffding_required_samples(0.1, confidence=1.0)

    def test_exact_mcnemar_rejects_broken_pair_contracts(self):
        valid = {"pair_id": "one", "candidate_success": True, "baseline_success": False}
        with self.assertRaisesRegex(ValueError, "unique"):
            exact_mcnemar_report((valid, dict(valid)))
        with self.assertRaisesRegex(ValueError, "boolean"):
            exact_mcnemar_report((dict(valid, candidate_success=1),))
        with self.assertRaises(ValueError):
            exact_mcnemar_report(())


if __name__ == "__main__":
    unittest.main()
