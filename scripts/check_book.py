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
    "docs/part-02-world-models/ch06-rssm.md",
)
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CHAPTER_STATUS_PATTERN = re.compile(r"^> 状态：`([^`]+)`", re.MULTILINE)
CLAIM_DEFINITION_PATTERN = re.compile(
    r"`(CLAIM-(\d{2})-(\d{2}))`（([^）]+)）："
)
CLAIM_ID_PATTERN = re.compile(r"^CLAIM-(\d{2})-(\d{2})$")
ALLOWED_CLAIM_TYPES = {"fact", "result", "inference", "recommendation", "unverified"}
FIGURE_ID_PATTERN = re.compile(r"\b((?:FIG|TAB)-(\d{2})-(\d{2}))\b")
MERMAID_BLOCK_PATTERN = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
MERMAID_ACC_TITLE_PATTERN = re.compile(r"^\s*accTitle:\s*(FIG-(\d{2})-(\d{2}))\s+(.+)$", re.MULTILINE)
MERMAID_ACC_DESCR_PATTERN = re.compile(r"^\s*accDescr:\s*(.+)$", re.MULTILINE)
FENCED_BLOCK_PATTERN = re.compile(r"^```[^\n]*\n.*?^```\s*$", re.MULTILINE | re.DOTALL)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


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


def check_manifest() -> list[str]:
    path = ROOT / "specs/book-manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    chapters = manifest.get("chapters", [])
    numbers = [chapter.get("number") for chapter in chapters if isinstance(chapter, dict)]
    errors: list[str] = []
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
    chapter_count = len(re.findall(r"^#### 第\d+章", prd.read_text(encoding="utf-8"), re.MULTILINE))
    return [] if chapter_count == 22 else [f"expected 22 PRD chapters, found {chapter_count}"]


def main() -> int:
    errors = check_required() + check_json() + check_manifest() + check_markdown_links() + check_prd_chapters()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "book checks passed: required files, JSON, bidirectional claim/figure contracts, Mermaid accessibility, "
        "heading hierarchy, "
        "manifest, local links, 22-chapter PRD"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
