from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from prefect import flow, get_run_logger, task

from rawlake.core.database import get_db_session
from rawlake.core.exceptions import DatasetNotFoundError
from rawlake.core.logging import Logger
from rawlake.extractors.registry import resolve_extractor
from rawlake.manifests.loader import load_manifest
from rawlake.manifests.sync import SyncedDataset, sync_dataset_from_manifest
from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.metadata.repository import Repository
from rawlake.schemas.product_manifest import (
    DEFAULT_PERIOD_LABEL_PATTERN,
    LandingConfig,
    ProductManifest,
)
from rawlake.services.ingestion_service import IngestionService

logger = Logger.get("ingestion_flow")


def _now_period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _resolve_period_labels(
    landing: LandingConfig,
    file_paths: list[Path],
    explicit_period: str | None = None,
) -> list[tuple[Path, str]]:
    if explicit_period is not None:
        return [(p, explicit_period) for p in file_paths]

    strategy = landing.period_label_strategy
    if strategy == "manual":
        raise ValueError(
            "period_label_strategy 'manual' requires an explicit period_label, "
            "and is not supported for multi-file extractors"
        )
    if strategy == "current_month":
        return [(p, _now_period()) for p in file_paths]

    pattern = landing.period_label_pattern or DEFAULT_PERIOD_LABEL_PATTERN
    compiled = re.compile(pattern)
    fallback = landing.period_label_fallback

    results: list[tuple[Path, str]] = []
    for path in file_paths:
        match = compiled.search(path.name)
        if match:
            year = match.group("year")
            month = match.group("month")
            results.append((path, f"{year}-{month}"))
        elif strategy == "from_filename_with_fallback" and fallback == "current_month":
            logger.warning(
                f"period_label pattern did not match {path.name!r}; using current_month fallback"
            )
            results.append((path, _now_period()))
        else:
            raise ValueError(
                f"Could not extract period_label from filename {path.name!r} "
                f"with pattern {pattern!r}"
            )
    return results


@task(name="load_manifest")
def task_load_manifest(dataset_key: str) -> ProductManifest:
    return load_manifest(dataset_key)


@task(name="sync_dataset")
def task_sync_dataset(manifest: ProductManifest) -> SyncedDataset:
    return sync_dataset_from_manifest(manifest)


@task(name="extract_files")
def task_extract_files(manifest: ProductManifest, dataset_key: str):
    with get_db_session() as session:
        repo = Repository(session)
        dataset = repo.get_dataset_by_key(dataset_key)
    if dataset is None:
        raise DatasetNotFoundError(dataset_key)
    extractor = resolve_extractor(manifest, dataset)
    file_paths = extractor.run()
    return extractor, file_paths


@task(name="register_archivos")
def task_register_archivos(
    dataset_key: str,
    file_period_pairs: list[tuple[Path, str]],
    manifest: ProductManifest,
    trigger_type: str,
    dry_run: bool = False,
) -> list[dict]:
    service = IngestionService()
    source_url = manifest.extractor.url if manifest.extractor.type == "http" else None
    results = []
    for file_path, period_label in file_period_pairs:
        if dry_run:
            results.append(
                {
                    "file": str(file_path),
                    "period_label": period_label,
                    "success": True,
                    "is_duplicate": False,
                    "error": None,
                    "dry_run": True,
                }
            )
            continue
        result = service.register_archivo(
            dataset_key=dataset_key,
            period_label=period_label,
            file_path=str(file_path),
            ingestion_mode=IngestionMode.AUTOMATED,
            trigger_type=TriggerType(trigger_type),
            actor="prefect-flow",
            source_url=source_url,
        )
        results.append(
            {
                "file": str(file_path),
                "period_label": period_label,
                "success": result.success,
                "is_duplicate": result.is_duplicate,
                "error": result.error_message,
                "dry_run": False,
            }
        )
    return results


@flow(name="run_ingestion", retries=3, retry_delay_seconds=60)
def run_ingestion(
    dataset_key: str,
    trigger_type: str = "manual_cli",
    period_label: str | None = None,
    dry_run: bool = False,
) -> dict:
    prefect_logger = get_run_logger()
    prefect_logger.info(f"Starting ingestion for dataset: {dataset_key} (dry_run={dry_run})")

    manifest = task_load_manifest(dataset_key)
    prefect_logger.info(f"Manifest loaded: {manifest.dataset_key}")

    synced = task_sync_dataset(manifest)
    prefect_logger.info(f"Dataset synced: {synced.nombre_corto} (id={synced.id})")

    extractor, file_paths = task_extract_files(manifest, dataset_key)
    prefect_logger.info(f"Extracted {len(file_paths)} file(s)")

    file_period_pairs = _resolve_period_labels(
        manifest.landing, file_paths, explicit_period=period_label
    )
    for fp, pl in file_period_pairs:
        prefect_logger.info(f"  {Path(fp).name} -> {pl}")

    results = task_register_archivos(
        dataset_key=dataset_key,
        file_period_pairs=file_period_pairs,
        manifest=manifest,
        trigger_type=trigger_type,
        dry_run=dry_run,
    )

    extractor.cleanup(file_paths)

    summary = {
        "dataset_key": dataset_key,
        "dry_run": dry_run,
        "results": results,
    }
    if period_label is not None:
        summary["period_label"] = period_label
    prefect_logger.info(f"Ingestion completed: {len(results)} file(s) processed")
    return summary
