from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.services.ingestion_service import IngestionService


def _make_temp_csv(content: str = "id,valor\n1,100\n") -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestRegisterArchivoDatasetNotFound:
    def test_returns_error_when_dataset_missing(self):
        service = IngestionService()
        tmp = _make_temp_csv()
        try:
            with patch("rawlake.services.ingestion_service.get_db_session") as mock_db:
                mock_session = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db.return_value.__exit__ = MagicMock(return_value=False)

                with patch("rawlake.services.ingestion_service.Repository") as mock_repo_cls:
                    mock_repo = MagicMock()
                    mock_repo.get_dataset_by_key.return_value = None
                    mock_repo_cls.return_value = mock_repo

                    result = service.register_archivo(
                        dataset_key="nonexistent",
                        period_label="2026-01",
                        file_path=tmp,
                        ingestion_mode=IngestionMode.MANUAL,
                        trigger_type=TriggerType.MANUAL_CLI,
                    )

            assert result.success is False
            assert "not found" in result.error_message.lower()
        finally:
            os.unlink(tmp)


class TestRegisterArchivoFileValidation:
    def test_returns_error_when_file_missing(self):
        service = IngestionService()
        with patch("rawlake.services.ingestion_service.get_db_session") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            with patch("rawlake.services.ingestion_service.Repository") as mock_repo_cls:
                mock_repo = MagicMock()
                mock_dataset = MagicMock()
                mock_dataset.id = 1
                mock_repo.get_dataset_by_key.return_value = mock_dataset
                mock_repo_cls.return_value = mock_repo

                result = service.register_archivo(
                    dataset_key="test_ds",
                    period_label="2026-01",
                    file_path="/nonexistent/file.csv",
                    ingestion_mode=IngestionMode.MANUAL,
                    trigger_type=TriggerType.MANUAL_CLI,
                )

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_returns_error_when_file_empty(self):
        service = IngestionService()
        tmp = _make_temp_csv(content="")
        try:
            with patch("rawlake.services.ingestion_service.get_db_session") as mock_db:
                mock_session = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db.return_value.__exit__ = MagicMock(return_value=False)

                with patch("rawlake.services.ingestion_service.Repository") as mock_repo_cls:
                    mock_repo = MagicMock()
                    mock_dataset = MagicMock()
                    mock_dataset.id = 1
                    mock_repo.get_dataset_by_key.return_value = mock_dataset
                    mock_repo_cls.return_value = mock_repo

                    result = service.register_archivo(
                        dataset_key="test_ds",
                        period_label="2026-01",
                        file_path=tmp,
                        ingestion_mode=IngestionMode.MANUAL,
                        trigger_type=TriggerType.MANUAL_CLI,
                    )

            assert result.success is False
            assert "empty" in result.error_message.lower()
        finally:
            os.unlink(tmp)


class TestRegisterArchivoDuplicate:
    def test_detects_duplicate_by_hash(self):
        service = IngestionService()
        tmp = _make_temp_csv()
        try:
            with patch("rawlake.services.ingestion_service.get_db_session") as mock_db:
                mock_session = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db.return_value.__exit__ = MagicMock(return_value=False)

                with patch("rawlake.services.ingestion_service.Repository") as mock_repo_cls:
                    mock_repo = MagicMock()
                    mock_dataset = MagicMock()
                    mock_dataset.id = 1
                    mock_repo.get_dataset_by_key.return_value = mock_dataset

                    mock_duplicate = MagicMock()
                    mock_duplicate.hash_sha256 = "abc123"
                    mock_duplicate.storage_path = "/some/path.csv"
                    mock_duplicate.file_size_bytes = 100
                    mock_duplicate.nombre_archivo = "old.csv"
                    mock_repo.find_duplicate_by_hash.return_value = mock_duplicate

                    mock_ingestion = MagicMock()
                    mock_ingestion.id = 42
                    mock_repo.create_ingestion.return_value = mock_ingestion
                    mock_repo_cls.return_value = mock_repo

                    result = service.register_archivo(
                        dataset_key="test_ds",
                        period_label="2026-01",
                        file_path=tmp,
                        ingestion_mode=IngestionMode.MANUAL,
                        trigger_type=TriggerType.MANUAL_CLI,
                    )

            assert result.success is True
            assert result.is_duplicate is True
            assert result.archivo.hash_sha256 == "abc123"
        finally:
            os.unlink(tmp)
