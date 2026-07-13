from __future__ import annotations

from datetime import datetime

from prefect import flow, get_run_logger

from rawlake.core.logging import Logger
from rawlake.extractors.registry import resolve_extractor
from rawlake.manifests.loader import load_manifest
from rawlake.manifests.sync import sync_dataset_from_manifest
from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.services.ingestion_service import IngestionService

logger = Logger.get("ingestion_flow")


def _resolve_period_label(strategy: str) -> str:
    if strategy == "current_month":
        return datetime.utcnow().strftime("%Y-%m")
    if strategy == "manual":
        raise ValueError("period_label_strategy 'manual' requires an explicit period_label")
    return datetime.utcnow().strftime("%Y-%m")


@flow(name="run_ingestion", retries=0)
def run_ingestion(
    dataset_key: str,
    trigger_type: str = "manual_cli",
    period_label: str | None = None,
) -> dict:
    prefect_logger = get_run_logger()
    prefect_logger.info(f"Starting ingestion for dataset: {dataset_key}")

    manifest = load_manifest(dataset_key)
    prefect_logger.info(f"Manifest loaded: {manifest.dataset_key}")

    dataset = sync_dataset_from_manifest(manifest)
    prefect_logger.info(f"Dataset synced: {dataset.nombre_corto} (id={dataset.id})")

    extractor = resolve_extractor(manifest, dataset)
    prefect_logger.info(f"Extractor resolved: {type(extractor).__name__}")

    if period_label is None:
        period_label = _resolve_period_label(manifest.landing.period_label_strategy)

    file_paths = extractor.run(period_label=period_label)
    prefect_logger.info(f"Extracted {len(file_paths)} file(s)")

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

    extractor.cleanup(file_paths)

    prefect_logger.info(f"Ingestion completed: {len(results)} file(s) processed")
    return {"dataset_key": dataset_key, "period_label": period_label, "results": results}
