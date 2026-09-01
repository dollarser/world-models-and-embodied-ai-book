from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_book import (
    check_chapter_sections,
    check_claim_contract,
    check_critical_recommendation_contract,
    check_documented_asset_version_contract,
    check_exercise_self_check_contract,
    check_fact_evidence_contract,
    check_floating_github_source_contract,
    check_experiment_asset_contract,
    check_figure_contract,
    check_glossary_contract,
    check_heading_hierarchy,
    check_inference_evidence_contract,
    check_mermaid_accessibility,
    check_prd_experiment_tiers,
    check_research_radar_contract,
    check_reading_map_contract,
    check_review_index_contract,
)


class ReviewIndexContractTest(unittest.TestCase):
    def test_accepts_indexed_review_records(self) -> None:
        self.assertEqual(
            [],
            check_review_index_contract(
                ["chapter-review.md", "book-review.md"],
                "[chapter](chapter-review.md)\n[book](book-review.md)\n",
            ),
        )

    def test_rejects_unindexed_review_records(self) -> None:
        self.assertEqual(
            ["review record is missing from reviews/README.md: missing-review.md"],
            check_review_index_contract(
                ["indexed-review.md", "missing-review.md"],
                "[indexed](indexed-review.md)\n",
            ),
        )


class FloatingGitHubSourceContractTest(unittest.TestCase):
    def test_rejects_main_and_master_but_accepts_full_commit(self) -> None:
        commit = "0123456789abcdef0123456789abcdef01234567"
        errors = check_floating_github_source_contract(
            {
                "docs/ch01.md": "https://github.com/example/project/blob/main/model.py",
                "docs/ch02.md": "https://github.com/example/project/tree/master/docs",
                "docs/ch03.md": f"https://github.com/example/project/blob/{commit}/model.py",
            }
        )
        self.assertEqual(2, len(errors))
        self.assertTrue(any("docs/ch01.md" in item and "blob/main" in item for item in errors))
        self.assertTrue(any("docs/ch02.md" in item and "tree/master" in item for item in errors))

    def test_accepts_non_github_and_repository_landing_pages(self) -> None:
        self.assertEqual(
            [],
            check_floating_github_source_contract(
                {
                    "docs/ch01.md": "https://arxiv.org/abs/1234.56789",
                    "docs/ch02.md": "https://github.com/example/project",
                }
            ),
        )


class ClaimContractTest(unittest.TestCase):
    def test_accepts_canonical_bidirectional_contract(self) -> None:
        text = (
            "`CLAIM-06-01`（fact）：directly supported statement\n"
            "`CLAIM-06-02`（result）：fixed fixture output，不代表 model performance\n"
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
        text = "`CLAIM-06-01`（result）：fixture output; this does not establish model performance\n"
        errors = check_claim_contract(6, ["CLAIM-06-01"], text, set())
        self.assertTrue(any("not bound by a registered experiment card" in item for item in errors))

    def test_result_requires_explicit_scope_boundary(self) -> None:
        text = "`CLAIM-06-01`（result）：fixture output is 0.5\n"
        errors = check_claim_contract(6, ["CLAIM-06-01"], text, {"CLAIM-06-01"})
        self.assertTrue(any("must state a limitation" in item for item in errors))


class DocumentedAssetVersionContractTest(unittest.TestCase):
    def test_accepts_current_experiment_and_benchmark_versions(self) -> None:
        documents = {
            "docs/ch02.md": "`EXP-02-01` v3 current fixture",
            "docs/ch20.md": "`benchmarks/BENCH-20-01.json` v5 frozen protocol",
        }
        versions = {"EXP-02-01": "v3", "BENCH-20-01": "fixture-v5"}
        self.assertEqual([], check_documented_asset_version_contract(documents, versions))

    def test_rejects_stale_and_unregistered_explicit_versions(self) -> None:
        documents = {
            "docs/ch21.md": "`EXP-21-01` v5 old; `EXP-99-01` v1 missing",
        }
        errors = check_documented_asset_version_contract(documents, {"EXP-21-01": "v6"})
        self.assertTrue(any("stale EXP-21-01 version v5" in item for item in errors))
        self.assertTrue(any("without a registered card: EXP-99-01" in item for item in errors))

    def test_ignores_unversioned_asset_references(self) -> None:
        self.assertEqual(
            [],
            check_documented_asset_version_contract(
                {"docs/ch04.md": "Run `EXP-04-01`; version is resolved from its card."},
                {"EXP-04-01": "v4"},
            ),
        )


class ReadingMapContractTest(unittest.TestCase):
    def test_accepts_complete_running_case_map(self) -> None:
        chapters = [
            {"number": 1, "document": "docs/part/ch01.md"},
            {"number": 2, "document": "docs/part/ch02.md"},
        ]
        text = "\n".join(
            [
                "遮挡条件下移动杯子；施工改道中的切入车辆。它们不是新增实验。",
                "observation state action prediction horizon success uncertainty",
                "[第1章](part/ch01.md) 与 [第2章](part/ch02.md)",
                "不能把22个smoke相加成端到端证据。",
            ]
        )
        self.assertEqual([], check_reading_map_contract(text, chapters))

    def test_rejects_missing_duplicate_and_overclaiming_map(self) -> None:
        chapters = [
            {"number": 1, "document": "docs/part/ch01.md"},
            {"number": 2, "document": "docs/part/ch02.md"},
        ]
        text = "[一次](part/ch01.md) [重复](part/ch01.md) observation state action"
        errors = check_reading_map_contract(text, chapters)
        self.assertTrue(any("chapter 1 exactly once, found 2" in item for item in errors))
        self.assertTrue(any("chapter 2 exactly once, found 0" in item for item in errors))
        self.assertTrue(any("evidence progression for: prediction" in item for item in errors))
        self.assertTrue(any("missing running task" in item for item in errors))
        self.assertTrue(any("not new experiments" in item for item in errors))


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


class ExerciseSelfCheckContractTest(unittest.TestCase):
    def test_accepts_bidirectional_numbered_self_checks(self) -> None:
        text = (
            "# Chapter\n\n## 练习\n\n"
            "1. **概念判断**：first\n"
            "2. **代码实验**：second\n\n"
            "## 自检要点\n\n"
            "<details markdown=\"1\">\n<summary>SELF-CHECK-03-01：概念判断</summary>\n\n"
            "合格答案应指出接口、前提和不能推出的结论，并给出一个可以复查的反例或命令；还要说明证据来自正文、结果文件还是外部来源。\n\n</details>\n\n"
            "<details markdown=\"1\">\n<summary>SELF-CHECK-03-02：代码实验</summary>\n\n"
            "合格答案应给出预期变化、固定分母、验证命令和失败边界，不能只写运行成功；若结果不同，还应先检查输入、版本和随机性。\n\n</details>\n"
        )
        self.assertEqual([], check_exercise_self_check_contract(3, text, True))

    def test_rejects_self_check_without_markdown_rendering(self) -> None:
        text = (
            "# Chapter\n\n## 练习\n\n1. **概念判断**：first\n\n## 自检要点\n\n"
            "<details>\n<summary>SELF-CHECK-03-01：概念判断</summary>\n\n"
            "这段答案包含 `metric_name`、验证步骤、失败边界和足够长度，但容器没有启用 Markdown-in-HTML。\n\n"
            "</details>\n"
        )
        errors = check_exercise_self_check_contract(3, text, True)
        self.assertTrue(any("Markdown content is rendered" in item for item in errors))

    def test_rejects_missing_foreign_and_unmatched_self_checks(self) -> None:
        text = (
            "# Chapter\n\n## 练习\n\n1. **概念判断**：first\n2. **实验**：second\n\n"
            "## 自检要点\n\n<details>\n"
            "<summary>SELF-CHECK-04-01：wrong owner</summary>\n\n"
            "这是一段足够长的错误归属答案，用来确认门禁会同时报告外章编号、缺项和未匹配项。\n\n</details>\n"
        )
        errors = check_exercise_self_check_contract(3, text, True)
        self.assertTrue(any("foreign self-check" in item for item in errors))
        self.assertTrue(any("exercise 1 has no self-check" in item for item in errors))
        self.assertTrue(any("exercise 2 has no self-check" in item for item in errors))

    def test_rejects_duplicate_short_and_unclosed_blocks(self) -> None:
        text = (
            "# Chapter\n\n## 练习\n\n1. **概念判断**：first\n\n## 自检要点\n\n"
            "<details>\n<summary>SELF-CHECK-03-01：first</summary>\nshort\n</details>\n"
            "<details>\n<summary>SELF-CHECK-03-01：duplicate</summary>\nshort\n"
        )
        errors = check_exercise_self_check_contract(3, text, True)
        self.assertTrue(any("more than once" in item for item in errors))
        self.assertTrue(any("unbalanced" in item for item in errors))
        self.assertTrue(any("too short" in item for item in errors))

    def test_ignores_non_enrolled_chapter_without_self_checks(self) -> None:
        text = "# Chapter\n\n## 练习\n\n1. **概念判断**：first\n"
        self.assertEqual([], check_exercise_self_check_contract(5, text, False))
        undeclared = (
            text
            + "\n## 自检要点\n\n<details>\n"
            + "<summary>SELF-CHECK-05-01：first</summary>\n\n"
            + "这段答案足够长，但章节没有登记覆盖，因此仍应被拒绝，避免源码与 manifest 的覆盖状态漂移。\n\n</details>\n"
        )
        errors = check_exercise_self_check_contract(5, undeclared, False)
        self.assertTrue(any("not enrolled" in item for item in errors))


class GlossaryContractTest(unittest.TestCase):
    def test_accepts_all_reader_critical_terms(self) -> None:
        terms = "RSSM MPC CEM VLM OOD IDM ESS RLOO RTC KL divergence NLL MAE / RMSE IoU LPIPS FVD"
        self.assertEqual([], check_glossary_contract(terms, terms))

    def test_reports_author_and_reader_omissions_separately(self) -> None:
        errors = check_glossary_contract("RSSM", "MPC")
        self.assertTrue(any("author terminology" in item and "MPC" in item for item in errors))
        self.assertTrue(any("reader glossary" in item and "RSSM" in item for item in errors))


class FactEvidenceContractTest(unittest.TestCase):
    def test_accepts_primary_source_with_boundary(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-06-01",
                    "basis": "primary_source",
                    "maturity": ["P"],
                    "anchors": ["https://example.org/paper"],
                    "scope_note": "This source supports the named algorithm interface but not a book reproduction result.",
                }
            ],
        }
        self.assertEqual([], check_fact_evidence_contract({"CLAIM-06-01"}, registry))

    def test_rejects_missing_and_stale_claim_entries(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-07-01",
                    "basis": "primary_source",
                    "maturity": ["P"],
                    "anchors": ["https://example.org/paper"],
                    "scope_note": "This source supports the named method but not any unregistered claim or result.",
                }
            ],
        }
        errors = check_fact_evidence_contract({"CLAIM-06-01"}, registry)
        self.assertTrue(any("no evidence registry entry" in item for item in errors))
        self.assertTrue(any("non-fact or missing claim" in item for item in errors))

    def test_rejects_source_basis_without_matching_anchor(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-06-01",
                    "basis": "vendor_statement",
                    "maturity": ["V"],
                    "anchors": ["specs/terminology.md"],
                    "scope_note": "A vendor statement must remain a vendor claim and cannot become independent validation.",
                }
            ],
        }
        errors = check_fact_evidence_contract({"CLAIM-06-01"}, registry)
        self.assertTrue(any("requires an external anchor" in item for item in errors))

    def test_rejects_vendor_statement_without_vendor_maturity(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-11-05",
                    "basis": "vendor_statement",
                    "maturity": ["O"],
                    "anchors": ["https://example.org/product"],
                    "scope_note": "The product page records only the vendor's statement and is not independent validation.",
                }
            ],
        }
        errors = check_fact_evidence_contract({"CLAIM-11-05"}, registry)
        self.assertTrue(any("must be labeled V" in item for item in errors))

    def test_rejects_floating_github_official_asset(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-06-05",
                    "basis": "official_asset",
                    "maturity": ["O"],
                    "anchors": ["https://github.com/example/project/blob/main/model.py"],
                    "scope_note": "The implementation detail is valid only for the exact source revision named by the evidence anchor.",
                }
            ],
        }
        errors = check_fact_evidence_contract({"CLAIM-06-05"}, registry)
        self.assertTrue(any("40-character commit" in item for item in errors))

    def test_accepts_commit_pinned_github_official_asset(self) -> None:
        commit = "0123456789abcdef0123456789abcdef01234567"
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-06-05",
                    "basis": "official_asset",
                    "maturity": ["O"],
                    "anchors": [f"https://github.com/example/project/blob/{commit}/model.py"],
                    "scope_note": "The implementation detail is valid only for the exact source revision named by the evidence anchor.",
                }
            ],
        }
        self.assertEqual([], check_fact_evidence_contract({"CLAIM-06-05"}, registry))


class InferenceEvidenceContractTest(unittest.TestCase):
    def test_accepts_explicit_premises_counterexample_and_scope(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-17-04",
                    "premises": [
                        "Rank agreement is measured only over the declared finite policy population.",
                        "Absolute calibration requires outcomes rather than ordering information alone.",
                    ],
                    "anchors": ["https://example.org/study"],
                    "counterexample": "A separate prospective calibration study could support absolute predictions in its declared population.",
                    "scope_note": "The inference limits correlation alone and does not reject a separately calibrated proxy evaluator.",
                }
            ],
        }
        self.assertEqual([], check_inference_evidence_contract({"CLAIM-17-04"}, registry))

    def test_rejects_floating_github_inference_anchor(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-18-05",
                    "premises": [
                        "Planning requires candidate-dependent consequences and a comparison rule.",
                        "Interactive simulation requires recursive state and termination semantics.",
                    ],
                    "anchors": ["https://github.com/example/project"],
                    "counterexample": "A validated deployed interface could expose every required component despite using another taxonomy.",
                    "scope_note": "The inference classifies observable capability and does not reject a separately validated implementation.",
                }
            ],
        }
        errors = check_inference_evidence_contract({"CLAIM-18-05"}, registry)
        self.assertTrue(any("40-character commit" in item for item in errors))

    def test_accepts_commit_pinned_github_inference_anchor(self) -> None:
        commit = "0123456789abcdef0123456789abcdef01234567"
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-18-05",
                    "premises": [
                        "Planning requires candidate-dependent consequences and a comparison rule.",
                        "Interactive simulation requires recursive state and termination semantics.",
                    ],
                    "anchors": [f"https://github.com/example/project/blob/{commit}/model.py"],
                    "counterexample": "A validated deployed interface could expose every required component despite using another taxonomy.",
                    "scope_note": "The inference classifies observable capability and does not reject a separately validated implementation.",
                }
            ],
        }
        self.assertEqual([], check_inference_evidence_contract({"CLAIM-18-05"}, registry))

    def test_rejects_missing_and_stale_inference_entries(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-18-05",
                    "premises": ["A sufficiently long first premise for this inference contract.", "A second sufficiently long premise."],
                    "anchors": ["https://example.org/study"],
                    "counterexample": "A sufficiently explicit counterexample that would weaken the inference in scope.",
                    "scope_note": "A sufficiently explicit statement that bounds what this inference can support.",
                }
            ],
        }
        errors = check_inference_evidence_contract({"CLAIM-17-04"}, registry)
        self.assertTrue(any("no evidence registry entry" in item for item in errors))
        self.assertTrue(any("non-inference or missing claim" in item for item in errors))

    def test_rejects_implicit_premises_and_missing_falsifier(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "claims": [
                {
                    "claim_id": "CLAIM-17-04",
                    "premises": ["too short"],
                    "anchors": ["https://example.org/study"],
                    "counterexample": "none",
                    "scope_note": "A sufficiently explicit scope boundary for the inference under review.",
                }
            ],
        }
        errors = check_inference_evidence_contract({"CLAIM-17-04"}, registry)
        self.assertTrue(any("two explicit premises" in item for item in errors))
        self.assertTrue(any("counterexample or falsifier" in item for item in errors))


class CriticalRecommendationContractTest(unittest.TestCase):
    def test_accepts_explicit_trigger_action_fallback_and_authority_boundary(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "selection_basis": "Recommendations that change resource escalation, publication, or safety-critical execution decisions.",
            "claims": [
                {
                    "claim_id": "CLAIM-21-05",
                    "category": "deployment_safety",
                    "applies_when": "A runtime gateway receives invalid, late, or unsafe model output.",
                    "required_action": "Select only a predefined and embodiment-specific validated fallback mode.",
                    "fallback_or_stop": "Refuse activation when no reachable and validated fallback mode exists.",
                    "not_authorized": "A language model is not authorized to invent an execution fallback.",
                }
            ],
        }
        self.assertEqual([], check_critical_recommendation_contract({"CLAIM-21-05"}, registry))

    def test_rejects_stale_type_and_missing_stop_boundary(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "selection_basis": "Recommendations that change resource escalation, publication, or safety-critical execution decisions.",
            "claims": [
                {
                    "claim_id": "CLAIM-21-06",
                    "category": "deployment_safety",
                    "applies_when": "A runtime system handles a safety-relevant output during execution.",
                    "required_action": "Select only a predefined and independently validated behavior.",
                    "fallback_or_stop": "none",
                    "not_authorized": "The model is not authorized to invent an execution fallback.",
                }
            ],
        }
        errors = check_critical_recommendation_contract({"CLAIM-21-05"}, registry)
        self.assertTrue(any("non-recommendation or missing claim" in item for item in errors))
        self.assertTrue(any("fallback_or_stop" in item for item in errors))


class PrdExperimentTierContractTest(unittest.TestCase):
    def test_accepts_delivered_s_tier_and_optional_upgrade(self) -> None:
        text = "\n".join(
            [
                "#### 第1章 Entry",
                "- S 档（已交付，`EXP-01-01`）：fixed CPU fixture.",
                "- M 档（可选待验证）：learned model in simulation.",
            ]
        )
        self.assertEqual([], check_prd_experiment_tiers(text, {1: ["EXP-01-01"]}))

    def test_rejects_unregistered_and_untiered_experiments(self) -> None:
        text = "\n".join(
            [
                "#### 第1章 Entry",
                "- 实验：run the planned model.",
                "- S 档（已交付，`EXP-01-02`）：stale experiment.",
            ]
        )
        errors = check_prd_experiment_tiers(text, {1: ["EXP-01-01"]})
        self.assertTrue(any("does not mark delivered S-tier" in item for item in errors))
        self.assertTrue(any("unregistered experiment" in item for item in errors))
        self.assertTrue(any("no optional pending M/L" in item for item in errors))
        self.assertTrue(any("un-tiered experiment" in item for item in errors))


class ExperimentAssetContractTest(unittest.TestCase):
    def test_accepts_minimal_runnable_asset_package(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            lab = root / "labs/example"
            (lab / "src").mkdir(parents=True)
            (lab / "scripts").mkdir()
            (lab / "tests").mkdir()
            (root / "results/ch01").mkdir(parents=True)
            (lab / "README.md").write_text("scope", encoding="utf-8")
            (lab / "src/fixture.py").write_text("VALUE = 1\n", encoding="utf-8")
            (lab / "scripts/smoke.py").write_text("print('{}')\n", encoding="utf-8")
            (lab / "tests/test_fixture.py").write_text("def test_fixture(): pass\n", encoding="utf-8")
            (root / "results/ch01/result.json").write_text("{}\n", encoding="utf-8")
            card = lab / "experiment-card.json"
            card.write_text(
                '{"id":"EXP-01-01","artifacts":["results/ch01/result.json"]}\n',
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                check_experiment_asset_contract({"EXP-01-01"}, [card], root),
            )

    def test_rejects_stale_incomplete_asset_package(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            lab = root / "labs/example"
            lab.mkdir(parents=True)
            card = lab / "experiment-card.json"
            card.write_text(
                '{"id":"EXP-01-02","artifacts":["results/ch01/missing.json"]}\n',
                encoding="utf-8",
            )
            errors = check_experiment_asset_contract({"EXP-01-01"}, [card], root)
            self.assertTrue(any("no asset package" in item for item in errors))
            self.assertTrue(any("not registered" in item for item in errors))
            self.assertTrue(any("missing README.md" in item for item in errors))
            self.assertTrue(any("no testable src" in item for item in errors))
            self.assertTrue(any("missing result artifact" in item for item in errors))


class ResearchRadarContractTest(unittest.TestCase):
    def test_accepts_dated_scoped_entry(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "entries": [
                {
                    "id": "RADAR-2026-01",
                    "title": "A current embodied world-model study",
                    "chapters": [9, 17],
                    "book_action": "case_card",
                    "problem": "The study asks whether learned rollouts can support a declared downstream evaluation use.",
                    "why_it_matters": "It tests a boundary already taught by the book without replacing stable chapter definitions.",
                    "sources": [
                        {
                            "url": "https://arxiv.org/abs/2601.00001",
                            "kind": "paper",
                            "maturity": "A",
                            "revision": "arXiv v1",
                        }
                    ],
                    "assets": {"code": "unknown", "weights": "unknown", "data": "unknown"},
                    "reproduction": "R0",
                    "resource_path": "Read and audit the paper at S tier; any model execution remains an optional M or L path.",
                    "scope_boundary": "The entry records an author-reported method and does not convert its metrics into book results.",
                    "review_triggers": ["A new paper revision changes the method or evaluation scope."],
                    "last_verified": "2026-09-01",
                }
            ],
        }
        self.assertEqual([], check_research_radar_contract(registry))

    def test_rejects_undated_unscoped_or_unlocked_entry(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "today",
            "entries": [
                {
                    "id": "latest",
                    "title": "new",
                    "chapters": [23],
                    "book_action": "rewrite_everything",
                    "problem": "short",
                    "why_it_matters": "short",
                    "sources": [{"url": "http://example.org", "kind": "blog", "maturity": "P"}],
                    "assets": {"code": "maybe"},
                    "reproduction": "done",
                    "resource_path": "short",
                    "scope_boundary": "short",
                    "review_triggers": [],
                    "last_verified": "unknown",
                }
            ],
        }
        errors = check_research_radar_contract(registry)
        self.assertTrue(any("ISO audit_date" in item for item in errors))
        self.assertTrue(any("invalid entry id" in item for item in errors))
        self.assertTrue(any("lock a revision" in item for item in errors))
        self.assertTrue(any("code/weights/data openness" in item for item in errors))
        self.assertTrue(any("review triggers" in item for item in errors))

    def test_rejects_floating_github_repository_snapshot(self) -> None:
        registry = {
            "version": 1,
            "audit_date": "2026-09-01",
            "entries": [
                {
                    "id": "RADAR-2026-01",
                    "title": "A current embodied world-model repository",
                    "chapters": [10],
                    "book_action": "case_card",
                    "problem": "The repository exposes a fast-moving implementation interface that the chapter needs to audit.",
                    "why_it_matters": "A floating default branch can silently change the evidence behind a dated implementation statement.",
                    "sources": [
                        {
                            "url": "https://github.com/example/project",
                            "kind": "official_repository",
                            "maturity": "O",
                            "revision": "main checked 2026-09-01",
                        }
                    ],
                    "assets": {"code": "open", "weights": "unknown", "data": "unknown"},
                    "reproduction": "R1",
                    "resource_path": "Audit source and metadata at S tier; model execution remains an optional resource-gated path.",
                    "scope_boundary": "The source snapshot proves only the inspected interface and does not establish model performance.",
                    "review_triggers": ["A new release changes the interface or asset license."],
                    "last_verified": "2026-09-01",
                }
            ],
        }
        errors = check_research_radar_contract(registry)
        self.assertTrue(any("40-character commit" in item for item in errors))
        commit = "0123456789abcdef0123456789abcdef01234567"
        registry["entries"][0]["sources"][0]["url"] = f"https://github.com/example/project/tree/{commit}"
        registry["entries"][0]["sources"][0]["revision"] = f"commit {commit}"
        self.assertEqual([], check_research_radar_contract(registry))


if __name__ == "__main__":
    unittest.main()
