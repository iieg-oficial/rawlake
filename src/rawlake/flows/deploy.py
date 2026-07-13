from __future__ import annotations

from prefect.deployments import Deployment

from rawlake.core.logging import Logger
from rawlake.flows.ingestion_flow import run_ingestion
from rawlake.manifests.loader import load_all_manifests

logger = Logger.get("deploy")


def deploy_all() -> int:
    manifests = load_all_manifests()
    count = 0

    for manifest in manifests:
        if manifest.schedule is None or not manifest.schedule.enabled:
            logger.info(f"Skipping {manifest.dataset_key}: no schedule or disabled")
            continue

        deployment = Deployment.build_from_flow(
            flow=run_ingestion,
            name=f"ingest-{manifest.dataset_key}",
            parameters={
                "dataset_key": manifest.dataset_key,
                "trigger_type": "scheduled",
            },
            schedule={"cron": manifest.schedule.cron, "timezone": manifest.schedule.timezone},
        )
        deployment.apply()
        logger.info(f"Deployed: {manifest.dataset_key} ({manifest.schedule.cron})")
        count += 1

    return count
