#!/usr/bin/env python3
"""Strict JSON Schema and cross-asset validation for book specifications."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> object:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def error_path(error: object) -> str:
    path = getattr(error, "absolute_path", ())
    return ".".join(str(part) for part in path) or "<root>"


def schema_errors(instance: object, schema: dict[str, object], label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        f"{label}:{error_path(error)}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def validate_schemas() -> tuple[dict[str, object], dict[str, object], dict[str, object], list[str]]:
    paths = {
        "experiment": "specs/experiment-card.schema.json",
        "manifest": "specs/book-manifest.schema.json",
        "chapter_status": "specs/chapter-status.schema.json",
    }
    schemas: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for name, path in paths.items():
        schema = load(path)
        if not isinstance(schema, dict):
            errors.append(f"{path}: schema root must be an object")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"{path}: invalid schema: {exc.message}")
        schemas[name] = schema
    return schemas["experiment"], schemas["manifest"], schemas["chapter_status"], errors


def validate_manifest(manifest_schema: dict[str, object], status_schema: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    manifest_path = "specs/book-manifest.json"
    manifest = load(manifest_path)
    errors = schema_errors(manifest, manifest_schema, manifest_path)
    if not isinstance(manifest, dict):
        return {}, errors

    chapters = manifest.get("chapters", [])
    if not isinstance(chapters, list):
        return manifest, errors

    numbers = [chapter.get("number") for chapter in chapters if isinstance(chapter, dict)]
    if numbers != list(range(1, 23)):
        errors.append(f"{manifest_path}: chapters must be ordered exactly 1..22, got {numbers}")

    experiment_ids: list[str] = []
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            continue
        number = chapter.get("number")
        errors.extend(schema_errors(chapter.get("status"), status_schema, f"{manifest_path}:chapters.{index}.status"))
        dependencies = chapter.get("dependencies", [])
        if isinstance(number, int) and any(not isinstance(dep, int) or dep >= number for dep in dependencies):
            errors.append(f"{manifest_path}: chapter {number} dependencies must refer to earlier chapters")
        document = chapter.get("document")
        if document is not None and not (ROOT / document).is_file():
            errors.append(f"{manifest_path}: chapter {number} document does not exist: {document}")
        for experiment_id in chapter.get("experiments", []):
            if experiment_id in experiment_ids:
                errors.append(f"{manifest_path}: duplicate experiment id: {experiment_id}")
            experiment_ids.append(experiment_id)

    prd = manifest.get("book", {}).get("prd") if isinstance(manifest.get("book"), dict) else None
    if not isinstance(prd, str) or not (ROOT / prd).is_file():
        errors.append(f"{manifest_path}: current PRD does not exist: {prd}")
    return manifest, errors


def validate_experiments(schema: dict[str, object], manifest: dict[str, object]) -> list[str]:
    errors: list[str] = []
    cards: dict[str, tuple[Path, dict[str, object]]] = {}
    for path in ROOT.glob("labs/**/experiment-card.json"):
        card = json.loads(path.read_text(encoding="utf-8"))
        label = str(path.relative_to(ROOT))
        errors.extend(schema_errors(card, schema, label))
        if not isinstance(card, dict):
            continue
        experiment_id = card.get("id")
        if isinstance(experiment_id, str):
            if experiment_id in cards:
                errors.append(f"duplicate experiment card id: {experiment_id}")
            cards[experiment_id] = (path, card)
        for artifact in card.get("artifacts", []):
            if isinstance(artifact, str) and not (ROOT / artifact).exists():
                errors.append(f"{label}: artifact does not exist: {artifact}")
        reviews = card.get("reviews")
        if isinstance(reviews, dict):
            record = reviews.get("record")
            if isinstance(record, str) and not (ROOT / record).is_file():
                errors.append(f"{label}: review record does not exist: {record}")

    manifest_ids: dict[str, int] = {}
    manifest_claims: dict[int, set[str]] = {}
    for chapter in manifest.get("chapters", []):
        if not isinstance(chapter, dict):
            continue
        chapter_number = chapter.get("number")
        if isinstance(chapter_number, int):
            manifest_claims[chapter_number] = set(chapter.get("claims", []))
        for experiment_id in chapter.get("experiments", []):
            manifest_ids[experiment_id] = chapter_number

    for experiment_id, chapter_number in manifest_ids.items():
        if experiment_id not in cards:
            errors.append(f"manifest experiment has no card: {experiment_id}")
            continue
        card_chapter = cards[experiment_id][1].get("chapter")
        if card_chapter != chapter_number:
            errors.append(f"{experiment_id}: card chapter {card_chapter} != manifest chapter {chapter_number}")
        for claim_id in cards[experiment_id][1].get("claim_ids", []):
            if claim_id not in manifest_claims.get(chapter_number, set()):
                errors.append(f"{experiment_id}: claim is not registered in chapter {chapter_number}: {claim_id}")
    for experiment_id in cards:
        if experiment_id not in manifest_ids:
            errors.append(f"experiment card is not registered in manifest: {experiment_id}")
    return errors


def main() -> int:
    experiment_schema, manifest_schema, status_schema, errors = validate_schemas()
    manifest, manifest_errors = validate_manifest(manifest_schema, status_schema)
    errors.extend(manifest_errors)
    errors.extend(validate_experiments(experiment_schema, manifest))

    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    chapter_count = len(manifest["chapters"])
    card_count = sum(1 for _ in ROOT.glob("labs/**/experiment-card.json"))
    print(f"strict specs passed: 3 schemas, {chapter_count} chapters, {card_count} experiment card(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
