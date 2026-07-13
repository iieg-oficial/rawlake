from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from rawlake.core.exceptions import ManifestError
from rawlake.schemas.product_manifest import ProductManifest

_PRODUCTS_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "products"


def _manifests_dir() -> Path:
    return _PRODUCTS_DIR


def load_manifest(dataset_key: str) -> ProductManifest:
    manifest_path = _manifests_dir() / f"{dataset_key}.yaml"
    if not manifest_path.exists():
        raise ManifestError(dataset_key, f"Manifest file not found: {manifest_path}")

    with open(manifest_path) as f:
        raw = yaml.safe_load(f)

    try:
        return ProductManifest(**raw)
    except ValidationError as e:
        raise ManifestError(dataset_key, f"Validation failed: {e}") from e


def load_all_manifests() -> list[ProductManifest]:
    manifests_dir = _manifests_dir()
    if not manifests_dir.exists():
        return []

    results: list[ProductManifest] = []
    for yaml_file in sorted(manifests_dir.glob("*.yaml")):
        key = yaml_file.stem
        results.append(load_manifest(key))
    return results
