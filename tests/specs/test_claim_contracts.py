from __future__ import annotations

import unittest

from scripts.check_book import check_claim_contract, check_figure_contract


class ClaimContractTest(unittest.TestCase):
    def test_accepts_canonical_bidirectional_contract(self) -> None:
        text = (
            "`CLAIM-06-01`（fact）：directly supported statement\n"
            "`CLAIM-06-02`（result）：fixed fixture output\n"
        )
        self.assertEqual(
            [],
            check_claim_contract(
                6,
                ["CLAIM-06-01", "CLAIM-06-02"],
                text,
                {"CLAIM-06-02"},
            ),
        )

    def test_rejects_missing_and_unregistered_definitions(self) -> None:
        errors = check_claim_contract(
            6,
            ["CLAIM-06-01"],
            "`CLAIM-06-02`（fact）：unregistered\n",
        )
        self.assertTrue(any("does not define registered claim: CLAIM-06-01" in item for item in errors))
        self.assertTrue(any("defines unregistered claim: CLAIM-06-02" in item for item in errors))

    def test_rejects_duplicate_definition(self) -> None:
        text = "\n".join(
            [
                "`CLAIM-06-01`（fact）：first",
                "`CLAIM-06-01`（fact）：second",
            ]
        )
        errors = check_claim_contract(6, ["CLAIM-06-01"], text)
        self.assertTrue(any("defines claim more than once" in item for item in errors))

    def test_rejects_foreign_chapter_and_noncanonical_type(self) -> None:
        text = "`CLAIM-07-01`（fact about protocol semantics）：statement\n"
        errors = check_claim_contract(6, ["CLAIM-07-01"], text)
        self.assertTrue(any("foreign registered claim ID" in item for item in errors))
        self.assertTrue(any("defines foreign claim ID" in item for item in errors))
        self.assertTrue(any("non-canonical type" in item for item in errors))

    def test_result_requires_experiment_card_binding(self) -> None:
        text = "`CLAIM-06-01`（result）：fixture output\n"
        errors = check_claim_contract(6, ["CLAIM-06-01"], text, set())
        self.assertTrue(any("not bound by a registered experiment card" in item for item in errors))


class FigureContractTest(unittest.TestCase):
    def test_accepts_registered_in_chapter_ids(self) -> None:
        text = "`FIG-15-01` / `TAB-15-01`\n*TAB-15-01: caption*\n"
        self.assertEqual([], check_figure_contract(15, ["FIG-15-01", "TAB-15-01"], text))

    def test_rejects_unregistered_missing_and_foreign_ids(self) -> None:
        text = "`FIG-15-01` / `TAB-14-01`\n"
        errors = check_figure_contract(15, ["FIG-15-01", "TAB-15-02"], text)
        self.assertTrue(any("does not contain registered" in item for item in errors))
        self.assertTrue(any("contains unregistered" in item for item in errors))
        self.assertTrue(any("invalid or foreign" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
