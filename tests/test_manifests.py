from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from rawlake.core.exceptions import ManifestError
from rawlake.manifests import loader
from rawlake.manifests.loader import load_manifest
from rawlake.schemas.product_manifest import ProductManifest


@pytest.fixture
def tmp_manifest(tmp_path):
    def _write(data: dict, filename: str = "test_product.yaml"):
        p = tmp_path / filename
        with open(p, "w") as f:
            yaml.dump(data, f)
        return p

    return _write


def _minimal_manifest(**overrides):
    base = {
        "dataset_key": "test_product",
        "nombre": "Test Product",
        "extractor": {
            "type": "http",
            "url": "https://example.com/data.csv",
        },
    }
    base.update(overrides)
    return base


class TestProductManifestSchema:
    def test_http_manifest_minimal(self):
        data = _minimal_manifest()
        m = ProductManifest(**data)
        assert m.dataset_key == "test_product"
        assert m.extractor.type == "http"
        assert m.landing.period_label_strategy == "current_month"
        assert m.storage.backend == "local"

    def test_custom_manifest(self):
        data = _minimal_manifest()
        data["extractor"] = {
            "type": "custom",
            "module": "rawlake.extractors.products.semadet",
            "class": "SemadetExtractor",
            "config": {"api_key_env": "SEMADET_KEY"},
        }
        m = ProductManifest(**data)
        assert m.extractor.type == "custom"
        assert m.extractor.class_name == "SemadetExtractor"

    def test_with_schedule(self):
        data = _minimal_manifest()
        data["schedule"] = {"cron": "0 9 5 * *", "timezone": "America/Mexico_City", "enabled": True}
        m = ProductManifest(**data)
        assert m.schedule is not None
        assert m.schedule.cron == "0 9 5 * *"

    def test_missing_required_fields_raises(self):
        with pytest.raises(Exception):
            ProductManifest(dataset_key="x")


class TestLoadManifest:
    def test_load_manifest_not_found(self, monkeypatch):
        monkeypatch.setattr(loader, "_PRODUCTS_DIR", Path(tempfile.mkdtemp()))
        with pytest.raises(ManifestError, match="not found"):
            load_manifest("nonexistent")

    def test_load_manifest_valid(self, monkeypatch, tmp_path):
        monkeypatch.setattr(loader, "_PRODUCTS_DIR", tmp_path)
        data = _minimal_manifest()
        with open(tmp_path / "test_product.yaml", "w") as f:
            yaml.dump(data, f)

        m = load_manifest("test_product")
        assert m.dataset_key == "test_product"

    def test_load_manifest_invalid_yaml(self, monkeypatch, tmp_path):
        monkeypatch.setattr(loader, "_PRODUCTS_DIR", tmp_path)
        with open(tmp_path / "bad.yaml", "w") as f:
            yaml.dump({"dataset_key": "bad"}, f)

        with pytest.raises(ManifestError, match="Validation failed"):
            load_manifest("bad")
