from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]


class ExperimentSchemaContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads((ROOT / "specs/experiment-card.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema)
        cls.card = json.loads(
            (ROOT / "labs/track-a-world-model-control/ch06-rssm/experiment-card.json").read_text(encoding="utf-8")
        )

    def assert_valid(self, card: dict[str, object]) -> None:
        self.assertEqual([], list(self.validator.iter_errors(card)))

    def assert_invalid(self, card: dict[str, object]) -> None:
        self.assertNotEqual([], list(self.validator.iter_errors(card)))

    def test_current_smoke_card_is_valid(self) -> None:
        self.assert_valid(self.card)

    def test_planned_card_may_have_no_metrics(self) -> None:
        card = deepcopy(self.card)
        card["status"] = "planned"
        card["metrics"] = []
        card["commands"] = {}
        card["artifacts"] = []
        self.assert_valid(card)

    def test_smoke_requires_metrics_and_commands(self) -> None:
        card = deepcopy(self.card)
        card["metrics"] = []
        card["commands"] = {}
        self.assert_invalid(card)

    def test_reviewed_requires_four_passed_reviews(self) -> None:
        card = deepcopy(self.card)
        card["status"] = "reviewed"
        card["environment"] = {
            "runtime": "CPython 3.12",
            "os": "Linux",
            "container": True,
            "container_image": "example@sha256:abc",
            "hardware": "CPU"
        }
        self.assert_invalid(card)

    def test_reproducible_rejects_uncommitted_and_pending_license(self) -> None:
        card = deepcopy(self.card)
        card["status"] = "reproducible"
        card["environment"] = {
            "runtime": "CPython 3.12",
            "os": "Linux",
            "container": True,
            "container_image": "example@sha256:abc",
            "hardware": "CPU"
        }
        card["reviews"] = {
            "content": "passed",
            "code": "passed",
            "consistency": "passed",
            "teaching": "passed",
            "record": "reviews/ch06-review.md"
        }
        self.assert_invalid(card)

    def test_gpu_verified_requires_model_driver_and_vram(self) -> None:
        card = deepcopy(self.card)
        card["resources"]["gpu_verified"] = True
        self.assert_invalid(card)

    def test_fixture_cannot_require_download(self) -> None:
        card = deepcopy(self.card)
        card["data"]["download_bytes"] = 100
        self.assert_invalid(card)

    def test_benchmark_id_must_be_well_formed(self) -> None:
        card = deepcopy(self.card)
        card["benchmark_ids"] = ["benchmark-latest"]
        self.assert_invalid(card)


class BenchmarkSchemaContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads((ROOT / "specs/benchmark-card.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema)
        cls.card = json.loads((ROOT / "benchmarks/BENCH-09-01.json").read_text(encoding="utf-8"))

    def assert_valid(self, card: dict[str, object]) -> None:
        self.assertEqual([], list(self.validator.iter_errors(card)))

    def assert_invalid(self, card: dict[str, object]) -> None:
        self.assertNotEqual([], list(self.validator.iter_errors(card)))

    def test_current_benchmark_card_is_valid(self) -> None:
        self.assert_valid(self.card)

    def test_executed_benchmark_requires_artifact(self) -> None:
        card = deepcopy(self.card)
        card["artifacts"] = []
        self.assert_invalid(card)

    def test_frozen_benchmark_may_precede_any_run(self) -> None:
        card = deepcopy(self.card)
        card["status"] = "frozen"
        card["experiment_ids"] = []
        card["artifacts"] = []
        self.assert_valid(card)

    def test_executed_benchmark_requires_experiment(self) -> None:
        card = deepcopy(self.card)
        card["experiment_ids"] = []
        self.assert_invalid(card)

    def test_deterministic_protocol_rejects_seed_list(self) -> None:
        card = deepcopy(self.card)
        card["protocol"]["randomness"]["seeds"] = [0]
        self.assert_invalid(card)

    def test_stochastic_protocol_requires_seed(self) -> None:
        card = deepcopy(self.card)
        card["protocol"]["randomness"]["deterministic"] = False
        self.assert_invalid(card)

    def test_statistical_interval_requires_confidence_level(self) -> None:
        card = deepcopy(self.card)
        uncertainty = card["metrics"][0]["statistical_uncertainty"]
        uncertainty["method"] = "bootstrap"
        self.assert_invalid(card)

    def test_not_applicable_uncertainty_rejects_confidence_level(self) -> None:
        card = deepcopy(self.card)
        card["metrics"][0]["statistical_uncertainty"]["confidence_level"] = 0.95
        self.assert_invalid(card)

    def test_enabled_distribution_shift_requires_score_protocol(self) -> None:
        card = deepcopy(self.card)
        card["distribution_shift"] = {"enabled": True}
        self.assert_invalid(card)

    def test_fixture_dataset_cannot_declare_download(self) -> None:
        card = deepcopy(self.card)
        card["datasets"][0]["download_bytes"] = 1
        self.assert_invalid(card)


if __name__ == "__main__":
    unittest.main()
