"""Generate prefect.yaml from product manifests."""

from pathlib import Path

import yaml

from rawlake.core.logging import Logger
from rawlake.manifests.loader import load_all_manifests

logger = Logger.get("deploy")

PREFECT_YAML_PATH = Path("prefect.yaml")


def generate_prefect_yaml() -> int:
    manifests = load_all_manifests()
    deployments = []

    for manifest in manifests:
        if manifest.schedule is None or not manifest.schedule.enabled:
            logger.info(f"Skipping {manifest.dataset_key}: no schedule or disabled")
            continue

        deployments.append(
            {
                "name": f"ingest-{manifest.dataset_key}",
                "entrypoint": "src/rawlake/flows/ingestion_flow.py:run_ingestion",
                "work_pool": {"name": "rawlake-worker", "work_queue_name": "default"},
                "parameters": {
                    "dataset_key": manifest.dataset_key,
                    "trigger_type": "scheduled",
                },
                "schedule": {
                    "cron": manifest.schedule.cron,
                    "timezone": manifest.schedule.timezone,
                },
            }
        )
        logger.info(f"Added deployment: ingest-{manifest.dataset_key}")

    config = {
        "prefect_version": "3.x",
        "deployments": deployments,
    }

    with open(PREFECT_YAML_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Generated {PREFECT_YAML_PATH} with {len(deployments)} deployment(s)")
    return len(deployments)
