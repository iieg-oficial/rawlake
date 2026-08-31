from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from rawlake.core.config import config
from rawlake.core.exceptions import ManifestError
from rawlake.schemas.product_manifest import ProductManifest

_PRODUCTS_DIR = Path(config.RAWLAKE_CONFIGS_DIR) / "products"


def load_manifest(dataset_key: str) -> ProductManifest:
    manifest_path = _PRODUCTS_DIR / f"{dataset_key}.yaml"
    if not manifest_path.exists():
        raise ManifestError(dataset_key, f"Manifest file not found: {manifest_path}")

    with open(manifest_path) as f:
        raw = yaml.safe_load(f)

    try:
        return ProductManifest(**raw)
    except ValidationError as e:
        raise ManifestError(dataset_key, f"Validation failed: {e}") from e


def load_all_manifests() -> list[ProductManifest]:
    if not _PRODUCTS_DIR.exists():
        raise ManifestError(
            dataset_key="*",
            reason=f"Products directory not found: {_PRODUCTS_DIR}",
        )

    results: list[ProductManifest] = []
    for yaml_file in sorted(_PRODUCTS_DIR.glob("*.yaml")):
        key = yaml_file.stem
        results.append(load_manifest(key))
    return results
