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
            for claim_id in chapter.get("claims", []):
                if claim_id not in document_text:
                    errors.append(f"chapter {number} document does not contain registered claim: {claim_id}")
            for figure_id in chapter.get("figures", []):
                if figure_id not in document_text:
                    errors.append(f"chapter {number} document does not contain registered figure/table: {figure_id}")
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
    print("book checks passed: required files, JSON, manifest, local links, 22-chapter PRD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
