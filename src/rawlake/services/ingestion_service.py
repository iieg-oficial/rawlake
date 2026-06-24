from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from rawlake.config import get_config
from rawlake.metadata.db import get_db_session

env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from rawlake.metadata.models import (
    IngestionMode,
    TriggerType,
)
from rawlake.metadata.repository import Repository
from rawlake.services.checksum_service import ChecksumService
from rawlake.services.versioning_service import VersioningService
from rawlake.storage.base import StorageBackend
from rawlake.storage.local import LocalStorageBackend


@dataclass
class ArchivoInfo:
    version_number: int
    hash_sha256: str
    storage_path: str
    file_size_bytes: Optional[int]
    nombre_archivo: str


@dataclass
class RegisterResult:
    success: bool
    archivo: Optional[ArchivoInfo] = None
    is_duplicate: bool = False
    error_message: Optional[str] = None


class IngestionService:
    def __init__(
        self,
        storage_backend: Optional[StorageBackend] = None,
    ):
        self._storage = storage_backend or LocalStorageBackend()
        self._checksum = ChecksumService()
        self._versioning = VersioningService()

    def register_archivo(
        self,
        dataset_key: str,
        distribucion_key: str,
        period_label: str,
        file_path: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        actor: Optional[str] = None,
        source_url: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> RegisterResult:
        """Register an archivo in the datalake.

        This is the core function of the system. It orchestrates:
        1. Validation of dataset and distribucion
        2. File validation (exists, not empty)
        3. Hash calculation
        4. Duplicate detection
        5. Versioning
        6. Storage copy
        7. metadata.json generation
        8. DB registration
        """
        with get_db_session() as session:
            repo = Repository(session)

            dataset = repo.get_dataset_by_key(dataset_key)
            if not dataset:
                return RegisterResult(
                    success=False,
                    error_message=f"Dataset not found: {dataset_key}",
                )

            distribucion = repo.get_distribucion_by_key(dataset.id, distribucion_key)
            if not distribucion:
                return RegisterResult(
                    success=False,
                    error_message=f"Distribucion not found: {distribucion_key} for dataset {dataset_key}",
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

            duplicate = repo.find_duplicate_by_hash(distribucion.id, period_label, checksum)
            if duplicate:
                run_id = self._versioning.generate_run_id()
                ingestion = repo.create_ingestion(
                    dataset_id=dataset.id,
                    distribucion_id=distribucion.id,
                    run_id=run_id,
                    period_label=period_label,
                    ingestion_mode=ingestion_mode,
                    trigger_type=trigger_type,
                    created_by=actor,
                )
                repo.update_ingestion_duplicated(ingestion.id)
                session.commit()
                return RegisterResult(
                    success=True,
                    archivo=ArchivoInfo(
                        version_number=duplicate.version_number,
                        hash_sha256=duplicate.hash_sha256,
                        storage_path=duplicate.storage_path,
                        file_size_bytes=duplicate.file_size_bytes,
                        nombre_archivo=duplicate.nombre_archivo,
                    ),
                    is_duplicate=True,
                )

            version_timestamp = self._versioning.generate_version_timestamp()
            version_number = repo.get_next_version_number(distribucion.id, period_label)

            storage_root = get_config().RAWLAKE_LOCAL_ROOT

            storage_path = self._storage.generate_version_path(
                root=storage_root,
                dataset_key=dataset_key,
                distribucion_key=distribucion_key,
                period_label=period_label,
                version_timestamp=version_timestamp,
                file_extension=file_ext,
            )

            run_id = self._versioning.generate_run_id()
            ingestion = repo.create_ingestion(
                dataset_id=dataset.id,
                distribucion_id=distribucion.id,
                run_id=run_id,
                period_label=period_label,
                ingestion_mode=ingestion_mode,
                trigger_type=trigger_type,
                created_by=actor,
            )

            self._storage.store(file_path, storage_path)

            archivo = repo.create_archivo(
                ingestion_id=ingestion.id,
                distribucion_id=distribucion.id,
                period_label=period_label,
                version_number=version_number,
                version_timestamp=version_timestamp,
                storage_backend=self._storage.get_backend_name(),
                storage_path=storage_path,
                nombre_archivo=original_name,
                file_extension=file_ext,
                mime_type=mime_type,
                file_size_bytes=file_size,
                hash_sha256=checksum,
                source_url=source_url,
                uploaded_by=actor,
                ingestion_mode=ingestion_mode,
            )

            repo.update_old_archivos_not_latest(distribucion.id, period_label, archivo.id)

            self._write_metadata_json(
                storage_path=storage_path,
                dataset_key=dataset_key,
                distribucion_key=distribucion_key,
                period_label=period_label,
                version_number=version_number,
                version_timestamp=version_timestamp,
                nombre_archivo=original_name,
                storage_backend=self._storage.get_backend_name(),
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
                    version_number=archivo.version_number,
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
        distribucion_key: str,
        period_label: str,
        version_number: int,
        version_timestamp: datetime,
        nombre_archivo: str,
        storage_backend: str,
        file_size_bytes: int,
        hash_sha256: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        source_url: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> None:
        metadata = {
            "dataset_key": dataset_key,
            "distribucion_key": distribucion_key,
            "period_label": period_label,
            "version_number": version_number,
            "version_timestamp": version_timestamp.isoformat(),
            "ingestion_mode": ingestion_mode.value,
            "trigger_type": trigger_type.value,
            "nombre_archivo": nombre_archivo,
            "stored_file_name": Path(storage_path).name,
            "storage_path": storage_path,
            "storage_backend": storage_backend,
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
    distribucion_key: str,
    period_label: str,
    file_path: str,
    ingestion_mode: IngestionMode,
    trigger_type: TriggerType,
    actor: Optional[str] = None,
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> RegisterResult:
    """Convenience function to register an archivo.

    Args:
        dataset_key: The dataset key (e.g., 'inegi-imaief')
        distribucion_key: The distribucion key (e.g., 'mensual_csv')
        period_label: The period label (e.g., '2026-01')
        file_path: Path to the file to register
        ingestion_mode: 'manual' or 'automated'
        trigger_type: What triggered this ingestion
        actor: Who/what initiated this (e.g., username)
        source_url: Original URL of the file
        notes: Additional notes

    Returns:
        RegisterResult with success status and archivo info
    """
    service = IngestionService()
    return service.register_archivo(
        dataset_key=dataset_key,
        distribucion_key=distribucion_key,
        period_label=period_label,
        file_path=file_path,
        ingestion_mode=ingestion_mode,
        trigger_type=trigger_type,
        actor=actor,
        source_url=source_url,
        notes=notes,
    )
