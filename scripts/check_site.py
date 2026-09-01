#!/usr/bin/env python3
"""Audit internal href/src targets in the strictly generated site directory."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SELF_CHECK_ID_PATTERN = re.compile(r"SELF-CHECK-\d{2}-\d{2}")


class TargetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        relevant = {"a": "href", "img": "src", "link": "href", "script": "src"}.get(tag)
        if relevant is None:
            return
        for name, value in attrs:
            if name == relevant and value:
                self.targets.append(value)


def local_target(source: Path, raw_target: str) -> Path | None:
    if raw_target.startswith("//"):
        return None
    parsed = urlsplit(raw_target)
    if parsed.scheme or not parsed.path:
        return None
    path = unquote(parsed.path)
    target = SITE / path.lstrip("/") if path.startswith("/") else source.parent / path
    target = target.resolve()
    try:
        target.relative_to(SITE.resolve())
    except ValueError:
        return target
    if path.endswith("/") or target.is_dir():
        target /= "index.html"
    return target


def expected_chapter_pages() -> list[Path]:
    manifest = json.loads((ROOT / "specs/book-manifest.json").read_text(encoding="utf-8"))
    pages = []
    for chapter in manifest["chapters"]:
        document = Path(chapter["document"])
        relative = document.relative_to("docs").with_suffix("")
        pages.append(SITE / relative / "index.html")
    return pages


def main() -> int:
    if not (SITE / "index.html").is_file():
        print("ERROR: compiled site is missing; run 'make docs-build' first")
        return 1

    errors: list[str] = []
    html_pages = sorted(SITE.rglob("*.html"))
    accessible_mermaid = 0
    compiled_self_checks = 0
    for expected in expected_chapter_pages():
        if not expected.is_file():
            errors.append(f"missing compiled chapter: {expected.relative_to(ROOT)}")

    manifest = json.loads((ROOT / "specs/book-manifest.json").read_text(encoding="utf-8"))
    for chapter in manifest["chapters"]:
        source = ROOT / chapter["document"]
        relative = Path(chapter["document"]).relative_to("docs").with_suffix("")
        compiled = SITE / relative / "index.html"
        if not compiled.is_file():
            continue
        source_text = source.read_text(encoding="utf-8")
        compiled_text = compiled.read_text(encoding="utf-8")
        expected_titles = source_text.count("accTitle:")
        expected_descriptions = source_text.count("accDescr:")
        if compiled_text.count("accTitle:") != expected_titles:
            errors.append(f"compiled chapter lost Mermaid accTitle metadata: {compiled.relative_to(ROOT)}")
        if compiled_text.count("accDescr:") != expected_descriptions:
            errors.append(f"compiled chapter lost Mermaid accDescr metadata: {compiled.relative_to(ROOT)}")
        accessible_mermaid += expected_titles
        source_self_check_ids = SELF_CHECK_ID_PATTERN.findall(source_text)
        compiled_self_check_ids = SELF_CHECK_ID_PATTERN.findall(compiled_text)
        if compiled_self_check_ids != source_self_check_ids:
            errors.append(f"compiled chapter lost or reordered exercise self-checks: {compiled.relative_to(ROOT)}")
        if compiled_text.count("<details>") < len(source_self_check_ids):
            errors.append(f"compiled chapter lost foldable self-check containers: {compiled.relative_to(ROOT)}")
        compiled_self_checks += len(source_self_check_ids)

    checked_targets = 0
    for source in html_pages:
        parser = TargetParser()
        parser.feed(source.read_text(encoding="utf-8"))
        for raw_target in parser.targets:
            target = local_target(source, raw_target)
            if target is None:
                continue
            checked_targets += 1
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                errors.append(
                    f"generated target escapes site: {source.relative_to(ROOT)} -> {raw_target}"
                )
                continue
            if not target.exists():
                errors.append(
                    f"broken generated target: {source.relative_to(ROOT)} -> {raw_target}"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"site checks passed: {len(html_pages)} HTML page(s), "
        f"22 compiled chapter(s), {accessible_mermaid} accessible Mermaid diagram(s), "
        f"{compiled_self_checks} foldable exercise self-check(s), "
        f"{checked_targets} internal target(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
