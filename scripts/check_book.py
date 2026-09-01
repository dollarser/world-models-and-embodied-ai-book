#!/usr/bin/env python3
"""Fast standard-library checks for the current book skeleton."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "LICENSE",
    "README.md",
    "mkdocs.yml",
    "specs/README.md",
    "specs/chapter-template.md",
    "specs/terminology.md",
    "specs/writing-style.md",
    "specs/evidence-policy.md",
    "specs/fact-evidence.json",
    "specs/inference-evidence.json",
    "specs/critical-recommendations.json",
    "specs/research-radar.json",
    "specs/experiment-card.schema.json",
    "specs/benchmark-card.schema.json",
    "specs/chapter-status.schema.json",
    "specs/book-manifest.schema.json",
    "specs/book-manifest.json",
    "specs/figure-guidelines.md",
    "specs/license-and-data-policy.md",
    "specs/book-quality-gates.md",
    "docs/index.md",
    "docs/status.md",
    "docs/glossary.md",
    "docs/research-radar.md",
    "docs/part-02-world-models/ch06-rssm.md",
)
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CHAPTER_STATUS_PATTERN = re.compile(r"^> 状态：`([^`]+)`", re.MULTILINE)
CLAIM_DEFINITION_PATTERN = re.compile(
    r"`(CLAIM-(\d{2})-(\d{2}))`（([^）]+)）："
)
RESULT_DEFINITION_PATTERN = re.compile(r"`(CLAIM-\d{2}-\d{2})`（result）：([^\n]+)")
CLAIM_ID_PATTERN = re.compile(r"^CLAIM-(\d{2})-(\d{2})$")
ALLOWED_CLAIM_TYPES = {"fact", "result", "inference", "recommendation", "unverified"}
FIGURE_ID_PATTERN = re.compile(r"\b((?:FIG|TAB)-(\d{2})-(\d{2}))\b")
MERMAID_BLOCK_PATTERN = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
MERMAID_ACC_TITLE_PATTERN = re.compile(r"^\s*accTitle:\s*(FIG-(\d{2})-(\d{2}))\s+(.+)$", re.MULTILINE)
MERMAID_ACC_DESCR_PATTERN = re.compile(r"^\s*accDescr:\s*(.+)$", re.MULTILINE)
FENCED_BLOCK_PATTERN = re.compile(r"^```[^\n]*\n.*?^```\s*$", re.MULTILINE | re.DOTALL)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
EXERCISE_ITEM_PATTERN = re.compile(r"^(\d+)\.\s+\*\*[^*\n]+\*\*：", re.MULTILINE)
SELF_CHECK_SUMMARY_PATTERN = re.compile(
    r"<summary>SELF-CHECK-(\d{2})-(\d{2})：[^<\n]+</summary>"
)
SELF_CHECK_BLOCK_PATTERN = re.compile(
    r"<details>\s*<summary>SELF-CHECK-(\d{2})-(\d{2})：[^<\n]+</summary>(.*?)</details>",
    re.DOTALL,
)
PRD_CHAPTER_HEADING_PATTERN = re.compile(r"^#### 第(\d+)章[^\n]*$", re.MULTILINE)
EXPERIMENT_ID_PATTERN = re.compile(r"\bEXP-\d{2}-\d{2}\b")
DOCUMENTED_ASSET_VERSION_PATTERN = re.compile(
    r"\b((?:EXP|BENCH)-\d{2}-\d{2})(?:\.json)?`?(?:\s+的)?\s+((?:fixture-)?v\d+)\b"
)
REQUIRED_CHAPTER_SECTIONS = ("本章契约", "小结", "练习", "延伸阅读", "验收与审查记录")
REQUIRED_READER_TERMS = (
    "RSSM",
    "MPC",
    "CEM",
    "VLM",
    "OOD",
    "IDM",
    "ESS",
    "RLOO",
    "RTC",
    "KL divergence",
    "NLL",
    "MAE / RMSE",
    "IoU",
    "LPIPS",
    "FVD",
)
ALLOWED_FACT_EVIDENCE_BASES = {
    "primary_source",
    "official_asset",
    "vendor_statement",
    "book_definition",
    "repository_contract",
    "mathematical_identity",
}
ALLOWED_SOURCE_MATURITY = {"P", "A", "O", "V", "T", "internal"}
ALLOWED_RECOMMENDATION_CATEGORIES = {
    "resource_escalation",
    "data_governance",
    "evaluation_publication",
    "deployment_safety",
}
ALLOWED_RADAR_SOURCE_KINDS = {"paper", "official_repository", "project_page", "vendor_page"}
ALLOWED_RADAR_ACTIONS = {"monitor", "case_card", "body_candidate"}
ALLOWED_RADAR_ASSET_STATES = {"open", "partial", "unknown", "closed", "not_applicable"}
ALLOWED_RADAR_REPRODUCTION = {"R0", "R1", "R2", "R3", "R4", "R0-R1"}
RESULT_BOUNDARY_MARKERS = ("不", "不能", "只", "未", "无法", "并非", "不是", "没有")
PINNED_GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/(?:blob|tree|commit)/([0-9a-f]{40})(?:/|$)"
)


def pinned_github_commit(url: str) -> str | None:
    """Return the immutable commit embedded in a GitHub URL, if present."""

    match = PINNED_GITHUB_URL_PATTERN.match(url)
    return match.group(1) if match else None


def check_required() -> list[str]:
    return [f"missing required file: {path}" for path in REQUIRED if not (ROOT / path).is_file()]


def check_json() -> list[str]:
    errors: list[str] = []
    paths = (
        list((ROOT / "specs").glob("*.json"))
        + list(ROOT.glob("labs/**/experiment-card.json"))
        + list(ROOT.glob("benchmarks/*.json"))
    )
    for path in paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    return errors


def check_documented_asset_version_contract(
    documents: dict[str, str], registered_versions: dict[str, str]
) -> list[str]:
    """Keep explicit EXP/BENCH versions in current reader documents aligned with their cards."""

    errors: list[str] = []
    normalized_versions = {
        asset_id: version.removeprefix("fixture-")
        for asset_id, version in registered_versions.items()
    }
    for document, text in documents.items():
        for match in DOCUMENTED_ASSET_VERSION_PATTERN.finditer(text):
            asset_id, documented_version = match.groups()
            expected_version = normalized_versions.get(asset_id)
            if expected_version is None:
                errors.append(
                    f"current document {document} names versioned asset without a registered card: {asset_id}"
                )
                continue
            if documented_version.removeprefix("fixture-") != expected_version:
                errors.append(
                    f"current document {document} has stale {asset_id} version "
                    f"{documented_version}; registered card is {registered_versions[asset_id]}"
                )
    return errors


def check_documented_asset_versions() -> list[str]:
    """Load current chapter documents and card versions, excluding historical review snapshots."""

    try:
        manifest = json.loads((ROOT / "specs/book-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    documents: dict[str, str] = {}
    for chapter in manifest.get("chapters", []):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("document"), str):
            continue
        document = chapter["document"]
        path = ROOT / document
        if path.is_file():
            documents[document] = path.read_text(encoding="utf-8")

    registered_versions: dict[str, str] = {}
    for card_path in ROOT.glob("labs/**/experiment-card.json"):
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        asset_id = card.get("id") if isinstance(card, dict) else None
        version = card.get("data", {}).get("version") if isinstance(card, dict) else None
        if isinstance(asset_id, str) and isinstance(version, str):
            registered_versions[asset_id] = version
    for card_path in ROOT.glob("benchmarks/*.json"):
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        asset_id = card.get("id") if isinstance(card, dict) else None
        version = card.get("protocol", {}).get("version") if isinstance(card, dict) else None
        if isinstance(asset_id, str) and isinstance(version, str):
            registered_versions[asset_id] = version
    return check_documented_asset_version_contract(documents, registered_versions)


def check_claim_contract(
    chapter_number: int,
    registered_claims: object,
    document_text: str,
    experiment_claims: set[str] | None = None,
) -> list[str]:
    """Check bidirectional claim registration, syntax, ownership, and result evidence."""

    errors: list[str] = []
    if not isinstance(registered_claims, list) or any(not isinstance(item, str) for item in registered_claims):
        return [f"chapter {chapter_number} manifest claims must be a list of strings"]

    definitions = [
        (match.group(1), int(match.group(2)), match.group(4))
        for match in CLAIM_DEFINITION_PATTERN.finditer(document_text)
    ]
    defined_ids = [claim_id for claim_id, _, _ in definitions]
    registered_set = set(registered_claims)
    defined_set = set(defined_ids)

    duplicates = sorted({claim_id for claim_id in defined_ids if defined_ids.count(claim_id) > 1})
    for claim_id in duplicates:
        errors.append(f"chapter {chapter_number} defines claim more than once: {claim_id}")

    for claim_id in sorted(registered_set - defined_set):
        errors.append(f"chapter {chapter_number} document does not define registered claim: {claim_id}")
    for claim_id in sorted(defined_set - registered_set):
        errors.append(f"chapter {chapter_number} document defines unregistered claim: {claim_id}")

    for claim_id in registered_claims:
        match = CLAIM_ID_PATTERN.fullmatch(claim_id)
        if match is None or int(match.group(1)) != chapter_number:
            errors.append(f"chapter {chapter_number} has invalid or foreign registered claim ID: {claim_id}")

    seen_types: dict[str, str] = {}
    for claim_id, owner_chapter, claim_type in definitions:
        seen_types.setdefault(claim_id, claim_type)
        if owner_chapter != chapter_number:
            errors.append(f"chapter {chapter_number} defines foreign claim ID: {claim_id}")
        if claim_type not in ALLOWED_CLAIM_TYPES:
            errors.append(
                f"chapter {chapter_number} claim {claim_id} has non-canonical type {claim_type!r}; "
                f"expected one of {sorted(ALLOWED_CLAIM_TYPES)}"
            )

    if experiment_claims is not None:
        for claim_id, claim_type in seen_types.items():
            if claim_type == "result" and claim_id not in experiment_claims:
                errors.append(
                    f"chapter {chapter_number} result claim is not bound by a registered experiment card: {claim_id}"
                )
    for match in RESULT_DEFINITION_PATTERN.finditer(document_text):
        claim_id, body = match.groups()
        if not any(marker in body for marker in RESULT_BOUNDARY_MARKERS):
            errors.append(
                f"chapter {chapter_number} result claim must state a limitation or non-generalization boundary: "
                f"{claim_id}"
            )
    return errors


def check_figure_contract(chapter_number: int, registered_figures: object, document_text: str) -> list[str]:
    """Check that every in-chapter FIG/TAB identifier is registered and owned by the chapter."""

    if not isinstance(registered_figures, list) or any(not isinstance(item, str) for item in registered_figures):
        return [f"chapter {chapter_number} manifest figures must be a list of strings"]

    errors: list[str] = []
    registered_set = set(registered_figures)
    document_ids = {match.group(1) for match in FIGURE_ID_PATTERN.finditer(document_text)}
    for figure_id in sorted(registered_set - document_ids):
        errors.append(f"chapter {chapter_number} document does not contain registered figure/table: {figure_id}")
    for figure_id in sorted(document_ids - registered_set):
        errors.append(f"chapter {chapter_number} document contains unregistered figure/table: {figure_id}")
    for figure_id in sorted(registered_set | document_ids):
        match = FIGURE_ID_PATTERN.fullmatch(figure_id)
        if match is None or int(match.group(2)) != chapter_number:
            errors.append(f"chapter {chapter_number} has invalid or foreign figure/table ID: {figure_id}")
    return errors


def check_mermaid_accessibility(chapter_number: int, registered_figures: object, document_text: str) -> list[str]:
    """Require every registered Mermaid figure to expose a stable title and useful description."""

    if not isinstance(registered_figures, list) or any(not isinstance(item, str) for item in registered_figures):
        return []

    errors: list[str] = []
    expected_ids = {item for item in registered_figures if item.startswith("FIG-")}
    actual_ids: list[str] = []
    for index, block in enumerate(MERMAID_BLOCK_PATTERN.findall(document_text), start=1):
        title_match = MERMAID_ACC_TITLE_PATTERN.search(block)
        description_match = MERMAID_ACC_DESCR_PATTERN.search(block)
        if title_match is None:
            errors.append(f"chapter {chapter_number} Mermaid diagram {index} has no canonical accTitle with FIG ID")
        else:
            figure_id = title_match.group(1)
            actual_ids.append(figure_id)
            if int(title_match.group(2)) != chapter_number:
                errors.append(f"chapter {chapter_number} Mermaid diagram {index} has foreign accTitle: {figure_id}")
        if description_match is None or len(description_match.group(1).strip()) < 20:
            errors.append(f"chapter {chapter_number} Mermaid diagram {index} has no useful accDescr")

    actual_set = set(actual_ids)
    for figure_id in sorted(actual_set - expected_ids):
        errors.append(f"chapter {chapter_number} Mermaid accTitle is not a registered figure: {figure_id}")
    if len(actual_ids) != len(actual_set):
        errors.append(f"chapter {chapter_number} has duplicate Mermaid accTitle IDs")
    return errors


def check_heading_hierarchy(chapter_number: int, document_text: str) -> list[str]:
    """Keep the chapter outline navigable for screen readers and generated TOCs."""

    text_without_code = FENCED_BLOCK_PATTERN.sub("", document_text)
    headings = [(len(match.group(1)), match.group(2).strip()) for match in HEADING_PATTERN.finditer(text_without_code)]
    errors: list[str] = []
    h1_count = sum(level == 1 for level, _ in headings)
    if h1_count != 1:
        errors.append(f"chapter {chapter_number} must contain exactly one H1 heading, found {h1_count}")
    if headings and headings[0][0] != 1:
        errors.append(f"chapter {chapter_number} first heading must be H1")
    for (previous_level, previous_title), (level, title) in zip(headings, headings[1:]):
        if level > previous_level + 1:
            errors.append(
                f"chapter {chapter_number} heading level skips from H{previous_level} {previous_title!r} "
                f"to H{level} {title!r}"
            )
    return errors


def check_chapter_sections(chapter_number: int, document_text: str) -> list[str]:
    """Enforce stable teaching and handoff sections without forbidding numbered headings."""

    text_without_code = FENCED_BLOCK_PATTERN.sub("", document_text)
    titles = [
        match.group(2).strip()
        for match in HEADING_PATTERN.finditer(text_without_code)
        if len(match.group(1)) == 2
    ]
    canonical_titles = {
        re.sub(rf"^{chapter_number}\.\d+(?:\.\d+)*\s+", "", title)
        for title in titles
    }
    errors = [
        f"chapter {chapter_number} is missing required H2 section: {section}"
        for section in REQUIRED_CHAPTER_SECTIONS
        if section not in canonical_titles
    ]
    handoff = "全书出口" if chapter_number == 22 else "下一章接口"
    if handoff not in canonical_titles:
        errors.append(f"chapter {chapter_number} is missing required H2 section: {handoff}")
    return errors


def _h2_section(text: str, title: str) -> str | None:
    match = re.search(rf"^## {re.escape(title)}\s*$", text, re.MULTILINE)
    if match is None:
        return None
    next_heading = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end]


def check_exercise_self_check_contract(
    chapter_number: int, text: str, required: bool
) -> list[str]:
    """Keep numbered exercises and opt-in self-check blocks bidirectionally aligned."""

    errors: list[str] = []
    exercise_section = _h2_section(text, "练习")
    exercise_numbers = (
        [int(number) for number in EXERCISE_ITEM_PATTERN.findall(exercise_section)]
        if exercise_section is not None
        else []
    )
    self_check_section = _h2_section(text, "自检要点")
    if not required and self_check_section is None:
        return []
    if not required and self_check_section is not None:
        errors.append(
            f"chapter {chapter_number} has exercise self-checks but is not enrolled in the manifest"
        )
    if required and self_check_section is None:
        return [f"chapter {chapter_number} is enrolled for exercise self-checks but has no 自检要点 H2"]
    if not exercise_numbers:
        errors.append(f"chapter {chapter_number} self-check contract has no numbered exercises")
    elif exercise_numbers != list(range(1, len(exercise_numbers) + 1)):
        errors.append(f"chapter {chapter_number} exercises must be numbered consecutively from 1")

    assert self_check_section is not None
    summaries = [
        (int(owner), int(number))
        for owner, number in SELF_CHECK_SUMMARY_PATTERN.findall(self_check_section)
    ]
    blocks = SELF_CHECK_BLOCK_PATTERN.findall(self_check_section)
    if self_check_section.count("<details>") != self_check_section.count("</details>"):
        errors.append(f"chapter {chapter_number} self-check details tags are unbalanced")
    if len(blocks) != len(summaries):
        errors.append(f"chapter {chapter_number} has a malformed or unclosed self-check block")

    duplicate_numbers = sorted(
        {number for owner, number in summaries if summaries.count((owner, number)) > 1}
    )
    for number in duplicate_numbers:
        errors.append(f"chapter {chapter_number} defines self-check {number} more than once")
    for owner, number in summaries:
        if owner != chapter_number:
            errors.append(
                f"chapter {chapter_number} contains foreign self-check ID SELF-CHECK-{owner:02d}-{number:02d}"
            )

    expected = set(exercise_numbers)
    actual = {number for owner, number in summaries if owner == chapter_number}
    for number in sorted(expected - actual):
        errors.append(f"chapter {chapter_number} exercise {number} has no self-check block")
    for number in sorted(actual - expected):
        errors.append(f"chapter {chapter_number} self-check {number} has no matching exercise")
    for owner, number, body in blocks:
        if int(owner) == chapter_number and len(re.sub(r"\s+", " ", body).strip()) < 40:
            errors.append(f"chapter {chapter_number} self-check {int(number)} is too short to be useful")
    return errors


def check_glossary_contract(terminology_text: str, glossary_text: str) -> list[str]:
    """Keep frequently used abbreviations visible in both the author and reader references."""

    errors: list[str] = []
    for term in REQUIRED_READER_TERMS:
        if term not in terminology_text:
            errors.append(f"author terminology baseline is missing reader-critical term: {term}")
        if term not in glossary_text:
            errors.append(f"reader glossary is missing reader-critical term: {term}")
    return errors


def check_fact_evidence_contract(
    fact_claim_ids: set[str], registry: object, root: Path = ROOT
) -> list[str]:
    """Require every canonical fact to name its evidence basis, anchors, and scope boundary."""

    if not isinstance(registry, dict):
        return ["fact evidence registry must be a JSON object"]
    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append("fact evidence registry version must be 1")
    audit_date = registry.get("audit_date")
    if not isinstance(audit_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", audit_date) is None:
        errors.append("fact evidence registry must have an ISO audit_date")
    entries = registry.get("claims")
    if not isinstance(entries, list):
        return errors + ["fact evidence registry claims must be a list"]

    entry_ids = [entry.get("claim_id") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({claim_id for claim_id in entry_ids if entry_ids.count(claim_id) > 1})
    for claim_id in duplicates:
        errors.append(f"fact evidence registry contains duplicate claim: {claim_id}")
    registered_ids = {claim_id for claim_id in entry_ids if isinstance(claim_id, str)}
    for claim_id in sorted(fact_claim_ids - registered_ids):
        errors.append(f"fact claim has no evidence registry entry: {claim_id}")
    for claim_id in sorted(registered_ids - fact_claim_ids):
        errors.append(f"fact evidence registry contains non-fact or missing claim: {claim_id}")

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("fact evidence registry entry must be an object")
            continue
        claim_id = entry.get("claim_id", "<missing>")
        basis = entry.get("basis")
        if basis not in ALLOWED_FACT_EVIDENCE_BASES:
            errors.append(f"fact evidence {claim_id} has invalid basis: {basis!r}")
        maturity = entry.get("maturity")
        if (
            not isinstance(maturity, list)
            or not maturity
            or any(item not in ALLOWED_SOURCE_MATURITY for item in maturity)
        ):
            errors.append(f"fact evidence {claim_id} has invalid maturity labels")
        elif basis == "primary_source" and not {"P", "A"}.intersection(maturity):
            errors.append(f"fact evidence {claim_id} primary source must be labeled P or A")
        elif basis == "official_asset" and "O" not in maturity:
            errors.append(f"fact evidence {claim_id} official asset must be labeled O")
        elif basis == "vendor_statement" and "V" not in maturity:
            errors.append(f"fact evidence {claim_id} vendor statement must be labeled V")
        elif basis in {"book_definition", "repository_contract", "mathematical_identity"} and "internal" not in maturity:
            errors.append(f"fact evidence {claim_id} internal basis must be labeled internal")
        anchors = entry.get("anchors")
        if not isinstance(anchors, list) or not anchors or any(not isinstance(item, str) for item in anchors):
            errors.append(f"fact evidence {claim_id} must have string anchors")
            continue
        external_anchors = [item for item in anchors if "://" in item]
        local_anchors = [item for item in anchors if "://" not in item]
        if basis in {"primary_source", "official_asset", "vendor_statement"} and not external_anchors:
            errors.append(f"fact evidence {claim_id} basis {basis} requires an external anchor")
        if basis == "official_asset":
            for anchor in external_anchors:
                if anchor.startswith("https://github.com/") and pinned_github_commit(anchor) is None:
                    errors.append(
                        f"fact evidence {claim_id} GitHub official asset must pin a 40-character commit: {anchor}"
                    )
        if basis in {"book_definition", "repository_contract", "mathematical_identity"} and not local_anchors:
            errors.append(f"fact evidence {claim_id} basis {basis} requires a local anchor")
        for anchor in local_anchors:
            local_path = anchor.split("#", 1)[0]
            if not local_path or not (root / local_path).is_file():
                errors.append(f"fact evidence {claim_id} has missing local anchor: {anchor}")
        note = entry.get("scope_note")
        if not isinstance(note, str) or len(note.strip()) < 40:
            errors.append(f"fact evidence {claim_id} must explain its support boundary")
    return errors


def check_inference_evidence_contract(
    inference_claim_ids: set[str], registry: object, root: Path = ROOT
) -> list[str]:
    """Require each inference to expose premises, anchors, a counterexample, and scope."""

    if not isinstance(registry, dict):
        return ["inference evidence registry must be a JSON object"]
    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append("inference evidence registry version must be 1")
    audit_date = registry.get("audit_date")
    if not isinstance(audit_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", audit_date) is None:
        errors.append("inference evidence registry must have an ISO audit_date")
    entries = registry.get("claims")
    if not isinstance(entries, list):
        return errors + ["inference evidence registry claims must be a list"]

    entry_ids = [entry.get("claim_id") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({claim_id for claim_id in entry_ids if entry_ids.count(claim_id) > 1})
    for claim_id in duplicates:
        errors.append(f"inference evidence registry contains duplicate claim: {claim_id}")
    registered_ids = {claim_id for claim_id in entry_ids if isinstance(claim_id, str)}
    for claim_id in sorted(inference_claim_ids - registered_ids):
        errors.append(f"inference claim has no evidence registry entry: {claim_id}")
    for claim_id in sorted(registered_ids - inference_claim_ids):
        errors.append(f"inference evidence registry contains non-inference or missing claim: {claim_id}")

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("inference evidence registry entry must be an object")
            continue
        claim_id = entry.get("claim_id", "<missing>")
        premises = entry.get("premises")
        if (
            not isinstance(premises, list)
            or len(premises) < 2
            or any(not isinstance(item, str) or len(item.strip()) < 20 for item in premises)
        ):
            errors.append(f"inference evidence {claim_id} must contain at least two explicit premises")
        anchors = entry.get("anchors")
        if not isinstance(anchors, list) or not anchors or any(not isinstance(item, str) for item in anchors):
            errors.append(f"inference evidence {claim_id} must have string anchors")
        else:
            for anchor in (item for item in anchors if "://" not in item):
                local_path = anchor.split("#", 1)[0]
                if not local_path or not (root / local_path).is_file():
                    errors.append(f"inference evidence {claim_id} has missing local anchor: {anchor}")
        counterexample = entry.get("counterexample")
        if not isinstance(counterexample, str) or len(counterexample.strip()) < 40:
            errors.append(f"inference evidence {claim_id} must state a counterexample or falsifier")
        note = entry.get("scope_note")
        if not isinstance(note, str) or len(note.strip()) < 40:
            errors.append(f"inference evidence {claim_id} must explain its scope boundary")
    return errors


def check_critical_recommendation_contract(
    recommendation_claim_ids: set[str], registry: object
) -> list[str]:
    """Require high-consequence author choices to expose trigger, action, fallback, and authority limits."""

    if not isinstance(registry, dict):
        return ["critical recommendation registry must be a JSON object"]
    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append("critical recommendation registry version must be 1")
    audit_date = registry.get("audit_date")
    if not isinstance(audit_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", audit_date) is None:
        errors.append("critical recommendation registry must have an ISO audit_date")
    selection_basis = registry.get("selection_basis")
    if not isinstance(selection_basis, str) or len(selection_basis.strip()) < 60:
        errors.append("critical recommendation registry must explain its selection basis")
    entries = registry.get("claims")
    if not isinstance(entries, list):
        return errors + ["critical recommendation registry claims must be a list"]

    entry_ids = [entry.get("claim_id") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({claim_id for claim_id in entry_ids if entry_ids.count(claim_id) > 1})
    for claim_id in duplicates:
        errors.append(f"critical recommendation registry contains duplicate claim: {claim_id}")
    registered_ids = {claim_id for claim_id in entry_ids if isinstance(claim_id, str)}
    for claim_id in sorted(registered_ids - recommendation_claim_ids):
        errors.append(f"critical recommendation registry contains non-recommendation or missing claim: {claim_id}")

    required_fields = ("applies_when", "required_action", "fallback_or_stop", "not_authorized")
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("critical recommendation registry entry must be an object")
            continue
        claim_id = entry.get("claim_id", "<missing>")
        category = entry.get("category")
        if category not in ALLOWED_RECOMMENDATION_CATEGORIES:
            errors.append(f"critical recommendation {claim_id} has invalid category: {category!r}")
        for field in required_fields:
            value = entry.get(field)
            if not isinstance(value, str) or len(value.strip()) < 30:
                errors.append(f"critical recommendation {claim_id} must state {field}")
    return errors


def check_experiment_asset_contract(
    manifest_experiment_ids: set[str], card_paths: list[Path], root: Path = ROOT
) -> list[str]:
    """Require every manifest experiment to have one runnable, documented S-tier asset package."""

    errors: list[str] = []
    cards: list[tuple[Path, dict[str, object]]] = []
    for card_path in card_paths:
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(card, dict):
            cards.append((card_path, card))

    card_ids = [card.get("id") for _, card in cards if isinstance(card.get("id"), str)]
    duplicates = sorted({experiment_id for experiment_id in card_ids if card_ids.count(experiment_id) > 1})
    for experiment_id in duplicates:
        errors.append(f"experiment asset contract contains duplicate card: {experiment_id}")
    registered_card_ids = set(card_ids)
    for experiment_id in sorted(manifest_experiment_ids - registered_card_ids):
        errors.append(f"manifest experiment has no asset package: {experiment_id}")
    for experiment_id in sorted(registered_card_ids - manifest_experiment_ids):
        errors.append(f"experiment asset package is not registered in manifest: {experiment_id}")

    for card_path, card in cards:
        experiment_id = card.get("id", "<missing>")
        lab_root = card_path.parent
        required_files = (lab_root / "README.md", lab_root / "scripts/smoke.py")
        for required_path in required_files:
            if not required_path.is_file():
                errors.append(
                    f"experiment {experiment_id} asset package is missing {required_path.relative_to(lab_root)}"
                )
        if not any((lab_root / "src").glob("*.py")):
            errors.append(f"experiment {experiment_id} asset package has no testable src/*.py module")
        if not any((lab_root / "tests").glob("test_*.py")):
            errors.append(f"experiment {experiment_id} asset package has no tests/test_*.py")
        artifacts = card.get("artifacts")
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if isinstance(artifact, str) and not (root / artifact).is_file():
                    errors.append(f"experiment {experiment_id} references missing result artifact: {artifact}")
    return errors


def check_research_radar_contract(registry: object) -> list[str]:
    """Keep fast-moving research entries dated, scoped, and separate from book results."""

    if not isinstance(registry, dict):
        return ["research radar must be a JSON object"]
    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append("research radar version must be 1")
    audit_date = registry.get("audit_date")
    if not isinstance(audit_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", audit_date) is None:
        errors.append("research radar must have an ISO audit_date")
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        return errors + ["research radar entries must be a non-empty list"]

    entry_ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({entry_id for entry_id in entry_ids if entry_ids.count(entry_id) > 1})
    for entry_id in duplicates:
        errors.append(f"research radar contains duplicate entry: {entry_id}")

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("research radar entry must be an object")
            continue
        entry_id = entry.get("id", "<missing>")
        if not isinstance(entry_id, str) or re.fullmatch(r"RADAR-\d{4}-\d{2}", entry_id) is None:
            errors.append(f"research radar has invalid entry id: {entry_id!r}")
        title = entry.get("title")
        if not isinstance(title, str) or len(title.strip()) < 8:
            errors.append(f"research radar {entry_id} must have a useful title")
        chapters = entry.get("chapters")
        if (
            not isinstance(chapters, list)
            or not chapters
            or any(not isinstance(chapter, int) or chapter < 1 or chapter > 22 for chapter in chapters)
        ):
            errors.append(f"research radar {entry_id} must reference book chapters 1..22")
        if entry.get("book_action") not in ALLOWED_RADAR_ACTIONS:
            errors.append(f"research radar {entry_id} has invalid book_action")
        if entry.get("reproduction") not in ALLOWED_RADAR_REPRODUCTION:
            errors.append(f"research radar {entry_id} has invalid reproduction state")
        for field in ("problem", "why_it_matters", "resource_path", "scope_boundary"):
            value = entry.get(field)
            if not isinstance(value, str) or len(value.strip()) < 40:
                errors.append(f"research radar {entry_id} must explain {field}")
        last_verified = entry.get("last_verified")
        if not isinstance(last_verified, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", last_verified) is None:
            errors.append(f"research radar {entry_id} must have an ISO last_verified date")
        sources = entry.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"research radar {entry_id} must have at least one primary or official source")
        else:
            for source in sources:
                if not isinstance(source, dict):
                    errors.append(f"research radar {entry_id} source must be an object")
                    continue
                url = source.get("url")
                if not isinstance(url, str) or not url.startswith("https://"):
                    errors.append(f"research radar {entry_id} source must use an https URL")
                if source.get("kind") not in ALLOWED_RADAR_SOURCE_KINDS:
                    errors.append(f"research radar {entry_id} source has invalid kind")
                maturity = source.get("maturity")
                if maturity not in ALLOWED_SOURCE_MATURITY - {"internal"}:
                    errors.append(f"research radar {entry_id} source has invalid maturity")
                revision = source.get("revision")
                if not isinstance(revision, str) or len(revision.strip()) < 3:
                    errors.append(f"research radar {entry_id} source must lock a revision or dated snapshot")
                if (
                    source.get("kind") == "official_repository"
                    and isinstance(url, str)
                    and url.startswith("https://github.com/")
                ):
                    commit = pinned_github_commit(url)
                    if commit is None:
                        errors.append(
                            f"research radar {entry_id} GitHub repository must pin a 40-character commit"
                        )
                    elif not isinstance(revision, str) or commit not in revision:
                        errors.append(
                            f"research radar {entry_id} revision must name its pinned GitHub commit"
                        )
        assets = entry.get("assets")
        if not isinstance(assets, dict) or set(assets) != {"code", "weights", "data"}:
            errors.append(f"research radar {entry_id} must state code/weights/data openness")
        elif any(value not in ALLOWED_RADAR_ASSET_STATES for value in assets.values()):
            errors.append(f"research radar {entry_id} has invalid asset openness")
        triggers = entry.get("review_triggers")
        if (
            not isinstance(triggers, list)
            or not triggers
            or any(not isinstance(trigger, str) or len(trigger.strip()) < 15 for trigger in triggers)
        ):
            errors.append(f"research radar {entry_id} must define explicit review triggers")
    return errors


def check_manifest() -> list[str]:
    path = ROOT / "specs/book-manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    chapters = manifest.get("chapters", [])
    self_check_chapters = manifest.get("exercise_self_check_chapters", [])
    numbers = [chapter.get("number") for chapter in chapters if isinstance(chapter, dict)]
    errors: list[str] = []
    if not isinstance(self_check_chapters, list) or any(
        not isinstance(number, int) or isinstance(number, bool) or number < 1 or number > 22
        for number in self_check_chapters
    ):
        errors.append("manifest exercise_self_check_chapters must be chapter numbers 1..22")
        self_check_chapter_set: set[int] = set()
    else:
        self_check_chapter_set = set(self_check_chapters)
        if len(self_check_chapter_set) != len(self_check_chapters):
            errors.append("manifest exercise_self_check_chapters must not contain duplicates")
    if numbers != list(range(1, 23)):
        errors.append(f"manifest chapters must be ordered 1..22, found {numbers}")
    experiment_ids: list[str] = []
    experiment_claims: dict[str, set[str]] = {}
    for card_path in ROOT.glob("labs/**/experiment-card.json"):
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(card, dict) and isinstance(card.get("id"), str):
            experiment_claims[card["id"]] = {
                claim_id for claim_id in card.get("claim_ids", []) if isinstance(claim_id, str)
            }
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        number = chapter.get("number")
        dependencies = chapter.get("dependencies", [])
        if isinstance(number, int) and any(not isinstance(dep, int) or dep >= number for dep in dependencies):
            errors.append(f"chapter {number} has a forward or invalid dependency")
        document = chapter.get("document")
        if isinstance(document, str) and not (ROOT / document).is_file():
            errors.append(f"chapter {number} document is missing: {document}")
        if isinstance(document, str) and (ROOT / document).is_file():
            document_text = (ROOT / document).read_text(encoding="utf-8")
            status_match = CHAPTER_STATUS_PATTERN.search(document_text)
            manifest_phase = chapter.get("status", {}).get("phase")
            if not status_match:
                errors.append(f"chapter {number} document has no status header")
            elif status_match.group(1) != manifest_phase:
                errors.append(
                    f"chapter {number} document status {status_match.group(1)} != manifest status {manifest_phase}"
                )
            bound_claims = {
                claim_id
                for experiment_id in chapter.get("experiments", [])
                for claim_id in experiment_claims.get(experiment_id, set())
            }
            if isinstance(number, int):
                errors.extend(
                    check_claim_contract(number, chapter.get("claims", []), document_text, bound_claims)
                )
            if isinstance(number, int):
                errors.extend(check_figure_contract(number, chapter.get("figures", []), document_text))
                errors.extend(check_mermaid_accessibility(number, chapter.get("figures", []), document_text))
                errors.extend(check_heading_hierarchy(number, document_text))
                errors.extend(check_chapter_sections(number, document_text))
                errors.extend(
                    check_exercise_self_check_contract(
                        number,
                        document_text,
                        number in self_check_chapter_set,
                    )
                )
            if manifest_phase in {"reviewed", "reproducible", "published"}:
                for review_name in ("内容审查", "代码审查", "一致性审查", "教学审查"):
                    if f"- {review_name}：通过" not in document_text:
                        errors.append(f"chapter {number} is {manifest_phase} but {review_name} is not passed in the document")
                record_match = re.search(r"审查记录路径：`([^`]+)`", document_text)
                if not record_match or not (ROOT / record_match.group(1)).is_file():
                    errors.append(f"chapter {number} is {manifest_phase} but its review record is missing")
        experiment_ids.extend(chapter.get("experiments", []))
    if len(experiment_ids) != len(set(experiment_ids)):
        errors.append("manifest contains duplicate experiment IDs")
    return errors


def check_experiment_assets() -> list[str]:
    manifest_path = ROOT / "specs/book-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    experiment_ids = {
        experiment_id
        for chapter in manifest.get("chapters", [])
        if isinstance(chapter, dict)
        for experiment_id in chapter.get("experiments", [])
        if isinstance(experiment_id, str)
    }
    return check_experiment_asset_contract(
        experiment_ids,
        list(ROOT.glob("labs/**/experiment-card.json")),
    )


def check_markdown_links() -> list[str]:
    errors: list[str] = []
    for source in ROOT.rglob("*.md"):
        if ".git" in source.parts or "site" in source.parts:
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"broken local link: {source.relative_to(ROOT)} -> {raw_target}")
    return errors


def check_prd_chapters() -> list[str]:
    prd = ROOT / "specs/PRD/世界模型与具身智能_书籍设计方案-v0_6.md"
    if not prd.is_file():
        return ["missing v0.6 PRD"]
    prd_text = prd.read_text(encoding="utf-8")
    chapter_count = len(PRD_CHAPTER_HEADING_PATTERN.findall(prd_text))
    errors = [] if chapter_count == 22 else [f"expected 22 PRD chapters, found {chapter_count}"]
    manifest_path = ROOT / "specs/book-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return errors
    chapter_experiments = {
        chapter["number"]: chapter.get("experiments", [])
        for chapter in manifest.get("chapters", [])
        if isinstance(chapter, dict) and isinstance(chapter.get("number"), int)
    }
    return errors + check_prd_experiment_tiers(prd_text, chapter_experiments)


def check_prd_experiment_tiers(prd_text: str, chapter_experiments: dict[int, object]) -> list[str]:
    """Keep PRD S-tier delivery claims aligned with manifest experiments and optional upgrades."""

    errors: list[str] = []
    headings = list(PRD_CHAPTER_HEADING_PATTERN.finditer(prd_text))
    sections = {
        int(match.group(1)): prd_text[match.end() : headings[index + 1].start() if index + 1 < len(headings) else len(prd_text)]
        for index, match in enumerate(headings)
    }
    for chapter_number, registered_experiments in chapter_experiments.items():
        if not isinstance(registered_experiments, list) or any(
            not isinstance(item, str) for item in registered_experiments
        ):
            errors.append(f"chapter {chapter_number} manifest experiments must be a list of strings")
            continue
        section = sections.get(chapter_number)
        if section is None:
            errors.append(f"PRD has no detailed section for chapter {chapter_number}")
            continue
        for experiment_id in registered_experiments:
            marker = f"- S 档（已交付，`{experiment_id}`）："
            if marker not in section:
                errors.append(f"PRD chapter {chapter_number} does not mark delivered S-tier experiment: {experiment_id}")
        documented_ids = set(EXPERIMENT_ID_PATTERN.findall(section))
        registered_ids = set(registered_experiments)
        for experiment_id in sorted(documented_ids - registered_ids):
            errors.append(f"PRD chapter {chapter_number} documents unregistered experiment: {experiment_id}")
        if re.search(r"^- M(?:/L)? 档（可选待验证）：", section, re.MULTILINE) is None:
            errors.append(f"PRD chapter {chapter_number} has no optional pending M/L upgrade path")
        if re.search(r"^- 实验：", section, re.MULTILINE):
            errors.append(f"PRD chapter {chapter_number} contains an un-tiered experiment description")
    return errors


def check_glossary_files() -> list[str]:
    terminology_path = ROOT / "specs/terminology.md"
    glossary_path = ROOT / "docs/glossary.md"
    if not terminology_path.is_file() or not glossary_path.is_file():
        return []
    return check_glossary_contract(
        terminology_path.read_text(encoding="utf-8"),
        glossary_path.read_text(encoding="utf-8"),
    )


def check_fact_evidence_files() -> list[str]:
    manifest_path = ROOT / "specs/book-manifest.json"
    registry_path = ROOT / "specs/fact-evidence.json"
    if not manifest_path.is_file() or not registry_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    fact_claim_ids: set[str] = set()
    for chapter in manifest.get("chapters", []):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("document"), str):
            continue
        document_path = ROOT / chapter["document"]
        if not document_path.is_file():
            continue
        for match in CLAIM_DEFINITION_PATTERN.finditer(document_path.read_text(encoding="utf-8")):
            if match.group(4) == "fact":
                fact_claim_ids.add(match.group(1))
    return check_fact_evidence_contract(fact_claim_ids, registry)


def check_inference_evidence_files() -> list[str]:
    manifest_path = ROOT / "specs/book-manifest.json"
    registry_path = ROOT / "specs/inference-evidence.json"
    if not manifest_path.is_file() or not registry_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    inference_claim_ids: set[str] = set()
    for chapter in manifest.get("chapters", []):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("document"), str):
            continue
        document_path = ROOT / chapter["document"]
        if not document_path.is_file():
            continue
        for match in CLAIM_DEFINITION_PATTERN.finditer(document_path.read_text(encoding="utf-8")):
            if match.group(4) == "inference":
                inference_claim_ids.add(match.group(1))
    return check_inference_evidence_contract(inference_claim_ids, registry)


def check_critical_recommendation_files() -> list[str]:
    manifest_path = ROOT / "specs/book-manifest.json"
    registry_path = ROOT / "specs/critical-recommendations.json"
    if not manifest_path.is_file() or not registry_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    recommendation_claim_ids: set[str] = set()
    for chapter in manifest.get("chapters", []):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("document"), str):
            continue
        document_path = ROOT / chapter["document"]
        if not document_path.is_file():
            continue
        for match in CLAIM_DEFINITION_PATTERN.finditer(document_path.read_text(encoding="utf-8")):
            if match.group(4) == "recommendation":
                recommendation_claim_ids.add(match.group(1))
    return check_critical_recommendation_contract(recommendation_claim_ids, registry)


def check_research_radar_file() -> list[str]:
    path = ROOT / "specs/research-radar.json"
    if not path.is_file():
        return []
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return check_research_radar_contract(registry)


def main() -> int:
    errors = (
        check_required()
        + check_json()
        + check_documented_asset_versions()
        + check_manifest()
        + check_experiment_assets()
        + check_markdown_links()
        + check_prd_chapters()
        + check_glossary_files()
        + check_fact_evidence_files()
        + check_inference_evidence_files()
        + check_critical_recommendation_files()
        + check_research_radar_file()
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "book checks passed: required files, JSON, bidirectional claim/figure contracts, Mermaid accessibility, "
        "experiment asset packages, explicit asset versions, heading hierarchy, chapter teaching sections, exercise self-checks, reader terminology, "
        "fact/inference evidence, critical "
        "recommendation policy, research radar, manifest, "
        "local links, 22-chapter PRD tier mapping"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
