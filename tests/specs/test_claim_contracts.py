from __future__ import annotations

import unittest

from scripts.check_book import (
    check_chapter_sections,
    check_claim_contract,
    check_figure_contract,
    check_glossary_contract,
    check_heading_hierarchy,
    check_mermaid_accessibility,
)


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


class MermaidAccessibilityTest(unittest.TestCase):
    def test_accepts_registered_title_and_description(self) -> None:
        text = (
            "```mermaid\nflowchart LR\n"
            "    accTitle: FIG-15-01 VLA contract\n"
            "    accDescr: Inputs are decoded and checked before the controller executes actions.\n"
            "    A --> B\n```\n"
        )
        self.assertEqual([], check_mermaid_accessibility(15, ["FIG-15-01", "TAB-15-01"], text))

    def test_rejects_missing_description_and_mismatched_id(self) -> None:
        text = "```mermaid\nflowchart LR\n    accTitle: FIG-14-01 wrong chapter\n    A --> B\n```\n"
        errors = check_mermaid_accessibility(15, ["FIG-15-01"], text)
        self.assertTrue(any("foreign accTitle" in item for item in errors))
        self.assertTrue(any("no useful accDescr" in item for item in errors))
        self.assertTrue(any("accTitle is not a registered figure" in item for item in errors))


class HeadingHierarchyTest(unittest.TestCase):
    def test_accepts_single_h1_and_sequential_levels(self) -> None:
        text = "# Chapter\n\n## Section\n\n### Detail\n\n## Next\n"
        self.assertEqual([], check_heading_hierarchy(6, text))

    def test_rejects_multiple_h1_and_level_skip_but_ignores_code(self) -> None:
        text = "# Chapter\n\n```text\n#### not a heading\n```\n\n### Skipped\n\n# Duplicate\n"
        errors = check_heading_hierarchy(6, text)
        self.assertTrue(any("exactly one H1" in item for item in errors))
        self.assertTrue(any("heading level skips" in item for item in errors))


class ChapterSectionContractTest(unittest.TestCase):
    def test_accepts_numbered_summary_and_terminal_handoff(self) -> None:
        shared = "\n".join(
            [
                "# Chapter",
                "## 本章契约",
                "## 22.10 小结",
                "## 练习",
                "## 延伸阅读",
                "## 全书出口",
                "## 验收与审查记录",
            ]
        )
        self.assertEqual([], check_chapter_sections(22, shared))

    def test_rejects_combined_or_missing_teaching_sections(self) -> None:
        text = "# Chapter\n\n## 本章契约\n\n## 小结与练习\n\n## 下一章接口与审查记录\n"
        errors = check_chapter_sections(7, text)
        self.assertTrue(any("小结" in item for item in errors))
        self.assertTrue(any("练习" in item for item in errors))
        self.assertTrue(any("验收与审查记录" in item for item in errors))


class GlossaryContractTest(unittest.TestCase):
    def test_accepts_all_reader_critical_terms(self) -> None:
        terms = "RSSM MPC CEM VLM OOD IDM ESS RLOO RTC KL divergence NLL MAE / RMSE IoU LPIPS FVD"
        self.assertEqual([], check_glossary_contract(terms, terms))

    def test_reports_author_and_reader_omissions_separately(self) -> None:
        errors = check_glossary_contract("RSSM", "MPC")
        self.assertTrue(any("author terminology" in item and "MPC" in item for item in errors))
        self.assertTrue(any("reader glossary" in item and "RSSM" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
