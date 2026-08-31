from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from system_cards import load_fixture, summarize, validate_fixture  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
