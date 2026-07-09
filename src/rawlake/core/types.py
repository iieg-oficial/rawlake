"""Type aliases y protocolos compartidos para RawLake."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from rawlake.metadata.models import Archivo, Dataset, Ingestion

# Type aliases para mejorar legibilidad
DatasetKey = str
PeriodLabel = str
StoragePath = str
RunID = str
HashSHA256 = str


@runtime_checkable
class RepositoryProtocol(Protocol):
    """Protocolo que define las operaciones del repositorio."""

    def get_dataset_by_key(self, dataset_key: str) -> Dataset | None: ...

    def create_dataset(
        self,
        nombre_corto: str,
        nombre: str,
        descripcion: str | None = None,
        fuente: str | None = None,
        periodicidad: str | None = None,
        desagregacion_geografica: str | None = None,
        inicio_cobertura_temporal: str | None = None,
    ) -> Dataset: ...

    def create_ingestion(
        self,
        dataset_id: int,
        run_id: str,
        ingestion_mode: str,
        trigger_type: str,
        created_by: str | None = None,
    ) -> Ingestion: ...

    def update_ingestion_success(
        self,
        ingestion_id: int,
        finished_at: datetime | None = None,
    ) -> None: ...

    def update_ingestion_failed(
        self,
        ingestion_id: int,
        error_message: str,
        finished_at: datetime | None = None,
    ) -> None: ...

    def create_archivo(
        self,
        ingestion_id: int,
        storage_path: str,
        nombre_archivo: str,
        hash_sha256: str,
        ingestion_mode: str,
        period_label: str | None = None,
        file_extension: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        source_url: str | None = None,
        uploaded_by: str | None = None,
    ) -> Archivo: ...

    def find_duplicate_by_hash(
        self,
        dataset_id: int,
        hash_sha256: str,
    ) -> Archivo | None: ...

    def get_latest_successful_ingestion(
        self,
        dataset_id: int,
    ) -> Ingestion | None: ...

    def get_archivos_by_ingestion(self, ingestion_id: int) -> list[Archivo]: ...


@runtime_checkable
class StorageBackendProtocol(Protocol):
    """Protocolo que define las operaciones de storage."""

    def store(self, source_path: str, destination_path: str) -> None: ...

    def exists(self, path: str) -> bool: ...

    def generate_version_path(
        self,
        root: str,
        dataset_key: str,
        period_label: str,
        version_timestamp: datetime,
        file_extension: str,
    ) -> str: ...

    def get_backend_name(self) -> str: ...
