from __future__ import annotations

from datetime import UTC, datetime

from prefect import flow, get_run_logger, task

from rawlake.core.logging import Logger
from rawlake.extractors.registry import resolve_extractor
from rawlake.manifests.loader import load_manifest
from rawlake.manifests.sync import sync_dataset_from_manifest
from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.schemas.product_manifest import ProductManifest
from rawlake.services.ingestion_service import IngestionService

logger = Logger.get("ingestion_flow")


def _resolve_period_label(strategy: str) -> str:
    if strategy == "manual":
        raise ValueError("period_label_strategy 'manual' requires an explicit period_label")
    return datetime.now(UTC).strftime("%Y-%m")


@task(name="load_manifest")
def task_load_manifest(dataset_key: str) -> ProductManifest:
    return load_manifest(dataset_key)


@task(name="sync_dataset")
def task_sync_dataset(manifest: ProductManifest):
    return sync_dataset_from_manifest(manifest)


@task(name="extract_files")
def task_extract_files(manifest: ProductManifest, dataset, period_label: str):
    extractor = resolve_extractor(manifest, dataset)
    file_paths = extractor.run(period_label=period_label)
    return extractor, file_paths


@task(name="register_archivos")
def task_register_archivos(
    dataset_key: str,
    period_label: str,
    file_paths: list,
    manifest: ProductManifest,
    trigger_type: str,
) -> list[dict]:
    service = IngestionService()
    results = []
    for file_path in file_paths:
        result = service.register_archivo(
            dataset_key=dataset_key,
            period_label=period_label,
            file_path=str(file_path),
            ingestion_mode=IngestionMode.AUTOMATED,
            trigger_type=TriggerType(trigger_type),
            actor="prefect-flow",
            source_url=manifest.extractor.url if manifest.extractor.type == "http" else None,
        )
        results.append(
            {
                "file": str(file_path),
                "success": result.success,
                "is_duplicate": result.is_duplicate,
                "error": result.error_message,
            }
        )
    return results


@flow(name="run_ingestion", retries=3, retry_delay_seconds=60)
def run_ingestion(
    dataset_key: str,
    trigger_type: str = "manual_cli",
    period_label: str | None = None,
) -> dict:
    prefect_logger = get_run_logger()
    prefect_logger.info(f"Starting ingestion for dataset: {dataset_key}")

    manifest = task_load_manifest(dataset_key)
    prefect_logger.info(f"Manifest loaded: {manifest.dataset_key}")

    dataset = task_sync_dataset(manifest)
    prefect_logger.info(f"Dataset synced: {dataset.nombre_corto} (id={dataset.id})")

    if period_label is None:
        period_label = _resolve_period_label(manifest.landing.period_label_strategy)

    extractor, file_paths = task_extract_files(manifest, dataset, period_label)
    prefect_logger.info(f"Extracted {len(file_paths)} file(s)")

    results = task_register_archivos(
        dataset_key=dataset_key,
        period_label=period_label,
        file_paths=file_paths,
        manifest=manifest,
        trigger_type=trigger_type,
    )

    extractor.cleanup(file_paths)

    prefect_logger.info(f"Ingestion completed: {len(results)} file(s) processed")
    return {"dataset_key": dataset_key, "period_label": period_label, "results": results}
