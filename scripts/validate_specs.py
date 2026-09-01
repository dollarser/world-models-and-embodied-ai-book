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


def validate_schemas() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    list[str],
]:
    paths = {
        "experiment": "specs/experiment-card.schema.json",
        "benchmark": "specs/benchmark-card.schema.json",
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
    return (
        schemas["experiment"],
        schemas["benchmark"],
        schemas["manifest"],
        schemas["chapter_status"],
        errors,
    )


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


def validate_benchmarks(schema: dict[str, object], manifest: dict[str, object]) -> list[str]:
    """Validate frozen protocols and their links to chapters, runs, and artifacts."""

    errors: list[str] = []
    chapters = {
        chapter.get("number"): chapter
        for chapter in manifest.get("chapters", [])
        if isinstance(chapter, dict) and isinstance(chapter.get("number"), int)
    }
    experiment_chapters = {
        experiment_id: chapter_number
        for chapter_number, chapter in chapters.items()
        for experiment_id in chapter.get("experiments", [])
    }
    experiment_cards: dict[str, dict[str, object]] = {}
    for experiment_path in ROOT.glob("labs/**/experiment-card.json"):
        experiment_card = json.loads(experiment_path.read_text(encoding="utf-8"))
        if isinstance(experiment_card, dict) and isinstance(experiment_card.get("id"), str):
            experiment_cards[experiment_card["id"]] = experiment_card

    seen_ids: set[str] = set()
    benchmark_cards: dict[str, dict[str, object]] = {}
    for path in sorted(ROOT.glob("benchmarks/*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        label = str(path.relative_to(ROOT))
        errors.extend(schema_errors(card, schema, label))
        if not isinstance(card, dict):
            continue

        benchmark_id = card.get("id")
        chapter_number = card.get("chapter")
        if isinstance(benchmark_id, str):
            if benchmark_id in seen_ids:
                errors.append(f"duplicate benchmark card id: {benchmark_id}")
            seen_ids.add(benchmark_id)
            benchmark_cards[benchmark_id] = card
            if isinstance(chapter_number, int) and not benchmark_id.startswith(f"BENCH-{chapter_number:02d}-"):
                errors.append(f"{label}: id does not match chapter {chapter_number}: {benchmark_id}")

        chapter = chapters.get(chapter_number)
        if chapter is None:
            errors.append(f"{label}: chapter is not registered in manifest: {chapter_number}")
            continue
        registered_claims = set(chapter.get("claims", []))
        for claim_id in card.get("claim_ids", []):
            if claim_id not in registered_claims:
                errors.append(f"{label}: claim is not registered in chapter {chapter_number}: {claim_id}")

        for experiment_id in card.get("experiment_ids", []):
            registered_chapter = experiment_chapters.get(experiment_id)
            if registered_chapter is None:
                errors.append(f"{label}: experiment is not registered in manifest: {experiment_id}")
            elif registered_chapter != chapter_number:
                errors.append(
                    f"{label}: experiment {experiment_id} belongs to chapter {registered_chapter}, not {chapter_number}"
                )
            experiment_card = experiment_cards.get(experiment_id)
            if (
                experiment_card is not None
                and isinstance(benchmark_id, str)
                and benchmark_id not in experiment_card.get("benchmark_ids", [])
            ):
                errors.append(f"{label}: experiment {experiment_id} does not link back to {benchmark_id}")
        for artifact in card.get("artifacts", []):
            if isinstance(artifact, str) and not (ROOT / artifact).is_file():
                errors.append(f"{label}: artifact does not exist: {artifact}")

        layers = set(card.get("evaluation_layers", []))
        metric_ids: set[str] = set()
        for metric in card.get("metrics", []):
            if not isinstance(metric, dict):
                continue
            metric_id = metric.get("id")
            if isinstance(metric_id, str):
                if metric_id in metric_ids:
                    errors.append(f"{label}: duplicate metric id: {metric_id}")
                metric_ids.add(metric_id)
                if isinstance(chapter_number, int) and not metric_id.startswith(f"METRIC-{chapter_number:02d}-"):
                    errors.append(f"{label}: metric id does not match chapter {chapter_number}: {metric_id}")
            if metric.get("layer") not in layers:
                errors.append(f"{label}: metric {metric_id} uses an undeclared evaluation layer: {metric.get('layer')}")

        system_names = [item.get("name") for item in card.get("systems", []) if isinstance(item, dict)]
        if len(system_names) != len(set(system_names)):
            errors.append(f"{label}: system names must be unique")
        declared_download = card.get("resources", {}).get("download_bytes") if isinstance(card.get("resources"), dict) else None
        dataset_download = sum(
            item.get("download_bytes", 0)
            for item in card.get("datasets", [])
            if isinstance(item, dict) and isinstance(item.get("download_bytes", 0), int)
        )
        if declared_download != dataset_download:
            errors.append(
                f"{label}: resource download_bytes {declared_download} != dataset total {dataset_download}"
            )

    for experiment_id, experiment_card in experiment_cards.items():
        experiment_chapter = experiment_card.get("chapter")
        for benchmark_id in experiment_card.get("benchmark_ids", []):
            benchmark_card = benchmark_cards.get(benchmark_id)
            if benchmark_card is None:
                errors.append(f"{experiment_id}: benchmark card does not exist: {benchmark_id}")
            elif benchmark_card.get("chapter") != experiment_chapter:
                errors.append(
                    f"{experiment_id}: benchmark {benchmark_id} belongs to chapter "
                    f"{benchmark_card.get('chapter')}, not {experiment_chapter}"
                )
            elif experiment_id not in benchmark_card.get("experiment_ids", []):
                errors.append(f"{experiment_id}: benchmark {benchmark_id} does not link back to the experiment")
    return errors


def main() -> int:
    experiment_schema, benchmark_schema, manifest_schema, status_schema, errors = validate_schemas()
    manifest, manifest_errors = validate_manifest(manifest_schema, status_schema)
    errors.extend(manifest_errors)
    errors.extend(validate_experiments(experiment_schema, manifest))
    errors.extend(validate_benchmarks(benchmark_schema, manifest))

    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    chapter_count = len(manifest["chapters"])
    card_count = sum(1 for _ in ROOT.glob("labs/**/experiment-card.json"))
    benchmark_count = sum(1 for _ in ROOT.glob("benchmarks/*.json"))
    print(
        f"strict specs passed: 4 schemas, {chapter_count} chapters, "
        f"{card_count} experiment card(s), {benchmark_count} benchmark card(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
