from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rawlake.core.config import config
from rawlake.core.database import get_db_session
from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.metadata.repository import Repository
from rawlake.services.checksum_service import ChecksumService
from rawlake.services.versioning_service import VersioningService
from rawlake.storage.base import StorageBackend
from rawlake.storage.local import LocalStorageBackend


@dataclass
class ArchivoInfo:
    hash_sha256: str
    storage_path: str
    file_size_bytes: int | None
    nombre_archivo: str


@dataclass
class RegisterResult:
    success: bool
    archivo: ArchivoInfo | None = None
    is_duplicate: bool = False
    error_message: str | None = None


class IngestionService:
    def __init__(
        self,
        storage_backend: StorageBackend | None = None,
    ):
        self._storage = storage_backend or LocalStorageBackend()
        self._checksum = ChecksumService()
        self._versioning = VersioningService()

    def register_archivo(
        self,
        dataset_key: str,
        period_label: str,
        file_path: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        actor: str | None = None,
        source_url: str | None = None,
        notes: str | None = None,
    ) -> RegisterResult:
        with get_db_session() as session:
            repo = Repository(session)

            dataset = repo.get_dataset_by_key(dataset_key)
            if not dataset:
                return RegisterResult(
                    success=False,
                    error_message=f"Dataset not found: {dataset_key}",
                )

            if not Path(file_path).exists():
                return RegisterResult(
                    success=False,
                    error_message=f"File not found: {file_path}",
                )

            file_size = self._checksum.get_file_size(file_path)
            if file_size == 0:
                return RegisterResult(
                    success=False,
                    error_message="File is empty",
                )

            checksum = self._checksum.calculate_sha256(file_path)
            file_ext = self._checksum.get_file_extension(file_path)
            mime_type = self._checksum.guess_mime_type(file_path)
            original_name = Path(file_path).name

            duplicate = repo.find_duplicate_by_hash(dataset.id, checksum)
            if duplicate:
                run_id = self._versioning.generate_run_id()
                ingestion = repo.create_ingestion(
                    dataset_id=dataset.id,
                    run_id=run_id,
                    ingestion_mode=ingestion_mode,
                    trigger_type=trigger_type,
                    created_by=actor,
                )
                repo.update_ingestion_duplicated(ingestion.id)
                session.commit()
                return RegisterResult(
                    success=True,
                    archivo=ArchivoInfo(
                        hash_sha256=duplicate.hash_sha256,
                        storage_path=duplicate.storage_path,
                        file_size_bytes=duplicate.file_size_bytes,
                        nombre_archivo=duplicate.nombre_archivo,
                    ),
                    is_duplicate=True,
                )

            version_timestamp = self._versioning.generate_version_timestamp()

            storage_root = config.RAWLAKE_LOCAL_ROOT

            storage_path = self._storage.generate_version_path(
                root=storage_root,
                dataset_key=dataset_key,
                period_label=period_label,
                version_timestamp=version_timestamp,
                nombre_archivo=original_name,
            )

            run_id = self._versioning.generate_run_id()
            ingestion = repo.create_ingestion(
                dataset_id=dataset.id,
                run_id=run_id,
                ingestion_mode=ingestion_mode,
                trigger_type=trigger_type,
                created_by=actor,
            )

            self._storage.store(file_path, storage_path)

            archivo = repo.create_archivo(
                ingestion_id=ingestion.id,
                storage_path=storage_path,
                nombre_archivo=original_name,
                file_extension=file_ext,
                mime_type=mime_type,
                file_size_bytes=file_size,
                hash_sha256=checksum,
                period_label=period_label,
                source_url=source_url,
                uploaded_by=actor,
                ingestion_mode=ingestion_mode,
            )

            self._write_metadata_json(
                storage_path=storage_path,
                dataset_key=dataset_key,
                period_label=period_label,
                nombre_archivo=original_name,
                file_size_bytes=file_size,
                hash_sha256=checksum,
                ingestion_mode=ingestion_mode,
                trigger_type=trigger_type,
                source_url=source_url,
                uploaded_by=actor,
            )

            repo.update_ingestion_success(ingestion.id)
            session.commit()

            return RegisterResult(
                success=True,
                archivo=ArchivoInfo(
                    hash_sha256=archivo.hash_sha256,
                    storage_path=archivo.storage_path,
                    file_size_bytes=archivo.file_size_bytes,
                    nombre_archivo=archivo.nombre_archivo,
                ),
            )

    def _write_metadata_json(
        self,
        storage_path: str,
        dataset_key: str,
        period_label: str,
        nombre_archivo: str,
        file_size_bytes: int,
        hash_sha256: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        source_url: str | None = None,
        uploaded_by: str | None = None,
    ) -> None:
        metadata = {
            "dataset_key": dataset_key,
            "period_label": period_label,
            "ingestion_mode": ingestion_mode.value,
            "trigger_type": trigger_type.value,
            "nombre_archivo": nombre_archivo,
            "stored_file_name": Path(storage_path).name,
            "storage_path": storage_path,
            "file_size_bytes": file_size_bytes,
            "hash_sha256": hash_sha256,
            "source_url": source_url,
            "uploaded_by": uploaded_by,
            "created_at": datetime.utcnow().isoformat(),
        }

        metadata_path = str(Path(storage_path).parent / "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)


def register_archivo(
    dataset_key: str,
    period_label: str,
    file_path: str,
    ingestion_mode: IngestionMode,
    trigger_type: TriggerType,
    actor: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> RegisterResult:
    service = IngestionService()
    return service.register_archivo(
        dataset_key=dataset_key,
        period_label=period_label,
        file_path=file_path,
        ingestion_mode=ingestion_mode,
        trigger_type=trigger_type,
        actor=actor,
        source_url=source_url,
        notes=notes,
    )
