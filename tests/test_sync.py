from __future__ import annotations

from unittest.mock import MagicMock, patch

from rawlake.manifests.sync import SyncedDataset, sync_dataset_from_manifest
from rawlake.schemas.product_manifest import (
    HttpExtractorConfig,
    LandingConfig,
    ProductManifest,
)


def _manifest(**overrides) -> ProductManifest:
    base = {
        "dataset_key": "test_ds",
        "nombre": "Test Dataset",
        "extractor": HttpExtractorConfig(type="http", url="https://example.com/data.csv"),
        "landing": LandingConfig(),
    }
    base.update(overrides)
    return ProductManifest(**base)


class TestSyncDatasetFromManifestCreates:
    def test_returns_synced_dataset_with_id_and_key(self):
        manifest = _manifest()
        with patch("rawlake.manifests.sync.get_db_session") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            with patch("rawlake.manifests.sync.Repository") as mock_repo_cls:
                mock_repo = MagicMock()
                mock_repo.get_dataset_by_key.return_value = None
                created = MagicMock()
                created.id = 7
                created.nombre_corto = "test_ds"
                mock_repo.create_dataset.return_value = created
                mock_repo_cls.return_value = mock_repo

                result = sync_dataset_from_manifest(manifest)

        assert isinstance(result, SyncedDataset)
        assert result.id == 7
        assert result.nombre_corto == "test_ds"


class TestSyncDatasetFromManifestUpdates:
    def test_returns_synced_dataset_when_already_exists(self):
        manifest = _manifest(nombre="Updated Name", periodicidad="monthly")
        with patch("rawlake.manifests.sync.get_db_session") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            with patch("rawlake.manifests.sync.Repository") as mock_repo_cls:
                mock_repo = MagicMock()
                existing = MagicMock()
                existing.id = 42
                existing.nombre_corto = "test_ds"
                mock_repo.get_dataset_by_key.return_value = existing
                mock_repo_cls.return_value = mock_repo

                result = sync_dataset_from_manifest(manifest)

        assert result == SyncedDataset(id=42, nombre_corto="test_ds")
        assert existing.nombre == "Updated Name"
        assert existing.periodicidad == "monthly"


class TestSyncedDatasetIsDetachedSafe:
    def test_fields_readable_after_session_closed(self):
        """Regression for DetachedInstanceError: SyncedDataset must keep its values
        readable without a live SQLAlchemy session."""
        manifest = _manifest()

        with patch("rawlake.manifests.sync.get_db_session") as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            with patch("rawlake.manifests.sync.Repository") as mock_repo_cls:
                mock_repo = MagicMock()
                existing = MagicMock()
                existing.id = 99
                existing.nombre_corto = "test_ds"
                mock_repo.get_dataset_by_key.return_value = existing
                mock_repo_cls.return_value = mock_repo

                synced = sync_dataset_from_manifest(manifest)

        assert isinstance(synced, SyncedDataset)
        assert synced.id == 99
        assert synced.nombre_corto == "test_ds"
