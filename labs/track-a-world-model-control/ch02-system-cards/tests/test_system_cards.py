from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from system_cards import (  # noqa: E402
    analyze_noisy_history_belief,
    analyze_state_aliasing,
    load_fixture,
    summarize,
    validate_fixture,
)


class SystemCardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = load_fixture(LAB_ROOT / "fixtures/system-cards.json")

    def test_current_fixture_covers_eight_categories(self) -> None:
        self.assertEqual(validate_fixture(self.fixture), [])
        self.assertEqual(summarize(self.fixture)["category_count"], 8)

    def test_vla_cannot_be_silently_relabelled_as_world_model(self) -> None:
        changed = deepcopy(self.fixture)
        vla = next(card for card in changed["cards"] if card["category"] == "vla_policy")
        vla["relation"] = "learned_latent_world_model"
        self.assertIn("VLA card must not be classified as an automatic world model", validate_fixture(changed))

    def test_every_card_must_record_an_evidence_limit(self) -> None:
        changed = deepcopy(self.fixture)
        changed["cards"][0]["unsupported_claims"] = []
        errors = validate_fixture(changed)
        self.assertTrue(any("unsupported claim" in error for error in errors))

    def test_scope_dependent_digital_twin_does_not_force_binary_dynamics(self) -> None:
        digital_twin = next(card for card in self.fixture["cards"] if card["category"] == "digital_twin")
        self.assertIsNone(digital_twin["learned_dynamics"])
        self.assertIsNone(digital_twin["action_conditioning"])

    def test_capability_summary_exposes_conjunctions_instead_of_names(self) -> None:
        summary = summarize(self.fixture)
        self.assertEqual(summary["cards_with_transition_evidence"], 6)
        self.assertEqual(summary["cards_with_action_intervention"], 5)
        self.assertEqual(summary["learned_action_conditioned_candidates"], 3)
        self.assertEqual(summary["scope_dependent_transition_cards"], 1)
        self.assertEqual(summary["policy_without_transition_cards"], 1)

    def test_action_output_cannot_be_relabelled_as_transition_evidence(self) -> None:
        changed = deepcopy(self.fixture)
        vla = next(card for card in changed["cards"] if card["category"] == "vla_policy")
        vla["claim_status"]["temporal_or_transition_model"] = "supported"
        self.assertIn(
            "VLA card must not infer an independent transition from action output",
            validate_fixture(changed),
        )

    def test_learned_action_conditioned_claim_requires_both_inputs(self) -> None:
        changed = deepcopy(self.fixture)
        video = next(card for card in changed["cards"] if card["category"] == "no_action_video_predictor")
        video["claim_status"]["learned_action_conditioned_transition"] = "supported"
        self.assertTrue(any("requires both" in error for error in validate_fixture(changed)))

    def test_claim_status_contract_is_closed_and_tri_state(self) -> None:
        for mutation in ("remove", "invalid", "wrong_type"):
            changed = deepcopy(self.fixture)
            statuses = changed["cards"][0]["claim_status"]
            if mutation == "remove":
                statuses.pop("candidate_action_intervention")
            elif mutation == "invalid":
                statuses["candidate_action_intervention"] = "maybe"
            else:
                statuses["candidate_action_intervention"] = []
            with self.subTest(mutation=mutation):
                self.assertTrue(any("claim_status" in error for error in validate_fixture(changed)))

    def test_duplicate_identity_and_weak_evidence_are_rejected(self) -> None:
        changed = deepcopy(self.fixture)
        changed["cards"][1]["id"] = changed["cards"][0]["id"]
        changed["cards"][2]["evidence"]["url"] = "http://example.invalid"
        changed["cards"][3]["axes"]["dynamics"] = ""
        errors = validate_fixture(changed)
        self.assertTrue(any("duplicate card id" in error for error in errors))
        self.assertTrue(any("must use https" in error for error in errors))
        self.assertTrue(any("axis values" in error for error in errors))

    def test_fixture_metadata_and_card_types_are_rejected_cleanly(self) -> None:
        for changed in (
            [],
            {"fixture_version": 1, "audit_date": "2026-08-31", "scope": "", "cards": []},
            {"fixture_version": 2, "audit_date": "2026-09-01", "scope": "test", "cards": "bad"},
            {"fixture_version": 2, "audit_date": "2026-09-01", "scope": "test", "cards": [{"category": []}] * 8},
        ):
            with self.subTest(changed=changed):
                self.assertTrue(validate_fixture(changed))

    def test_current_observation_aliases_contexts_with_different_optimal_actions(self) -> None:
        aliasing = summarize(self.fixture)["state_aliasing"]
        self.assertEqual(aliasing["current_observation"], "occluded-corridor")
        self.assertEqual(aliasing["context_optimal_actions"], {"clear": "advance", "blocked": "hold"})
        self.assertTrue(aliasing["context_optimal_actions_differ"])

    def test_history_disambiguation_closes_fixed_decision_regret(self) -> None:
        aliasing = summarize(self.fixture)["state_aliasing"]
        self.assertEqual(aliasing["mean_return_by_shared_action"], {"advance": 0.0, "hold": 0.1})
        self.assertEqual(aliasing["aliased_selected_action"], "hold")
        self.assertEqual(aliasing["aliased_mean_return"], 0.1)
        self.assertEqual(aliasing["aliased_mean_regret"], 0.5)
        self.assertEqual(aliasing["history_aware_mean_return"], 0.6)
        self.assertEqual(aliasing["history_aware_mean_regret"], 0.0)

    def test_aliasing_case_requires_unique_history_and_consistent_actions(self) -> None:
        for mutation in ("history", "actions", "context_tie", "aliased_tie"):
            changed = deepcopy(self.fixture["state_aliasing_case"])
            if mutation == "history":
                changed["contexts"][1]["history_cue"] = changed["contexts"][0]["history_cue"]
            elif mutation == "actions":
                changed["contexts"][1]["action_returns"] = {"advance": -1.0, "wait": 0.2}
            elif mutation == "context_tie":
                changed["contexts"][0]["action_returns"] = {"advance": 1.0, "hold": 1.0}
            else:
                changed["contexts"][0]["action_returns"] = {"advance": 1.0, "hold": 0.0}
                changed["contexts"][1]["action_returns"] = {"advance": 0.0, "hold": 1.0}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analyze_state_aliasing(changed)

    def test_aliasing_case_rejects_non_finite_and_non_numeric_returns(self) -> None:
        for invalid in (True, "bad", float("nan"), float("inf")):
            changed = deepcopy(self.fixture["state_aliasing_case"])
            changed["contexts"][0]["action_returns"]["advance"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                analyze_state_aliasing(changed)

    def test_noisy_history_retains_posterior_uncertainty_and_changes_action(self) -> None:
        belief = summarize(self.fixture)["noisy_history_belief"]
        self.assertEqual(
            belief["posterior_by_cue"],
            {
                "clear_signal": {"blocked": 0.2, "clear": 0.8},
                "blocked_signal": {"blocked": 0.8, "clear": 0.2},
            },
        )
        self.assertEqual(
            belief["selected_action_by_cue"],
            {"clear_signal": "advance", "blocked_signal": "hold"},
        )

    def test_noisy_history_improves_but_does_not_close_oracle_regret(self) -> None:
        belief = summarize(self.fixture)["noisy_history_belief"]
        self.assertEqual(belief["current_only_mean_return"], 0.1)
        self.assertEqual(belief["noisy_history_mean_return"], 0.38)
        self.assertEqual(belief["perfect_history_mean_return"], 0.6)
        self.assertEqual(belief["noisy_history_gain_over_current"], 0.28)
        self.assertEqual(belief["noisy_history_mean_regret"], 0.22)

    def test_noisy_history_rejects_invalid_priors(self) -> None:
        for priors in (
            {"clear": 0.6, "blocked": 0.6},
            {"clear": 1.0},
            {"clear": True, "blocked": 0.0},
        ):
            changed = deepcopy(self.fixture["noisy_history_belief_case"])
            changed["context_priors"] = priors
            with self.subTest(priors=priors), self.assertRaises(ValueError):
                analyze_noisy_history_belief(self.fixture["state_aliasing_case"], changed)

    def test_noisy_history_rejects_invalid_likelihood_contracts(self) -> None:
        for mutation in ("missing_context", "not_normalized", "tie"):
            changed = deepcopy(self.fixture["noisy_history_belief_case"])
            if mutation == "missing_context":
                del changed["cue_likelihoods"]["clear_signal"]["blocked"]
            elif mutation == "not_normalized":
                changed["cue_likelihoods"]["clear_signal"]["clear"] = 0.9
            else:
                changed["cue_likelihoods"] = {
                    "tie_a": {"clear": 0.6, "blocked": 0.5},
                    "tie_b": {"clear": 0.4, "blocked": 0.5},
                }
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analyze_noisy_history_belief(self.fixture["state_aliasing_case"], changed)


if __name__ == "__main__":
    unittest.main()
