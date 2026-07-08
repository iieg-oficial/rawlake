from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from rawlake.metadata.models import (
    Archivo,
    Dataset,
    Ingestion,
    IngestionMode,
    RunStatus,
    TriggerType,
)


class Repository:
    def __init__(self, session: Session):
        self._session = session

    def get_dataset_by_key(self, dataset_key: str) -> Dataset | None:
        stmt = select(Dataset).where(Dataset.nombre_corto == dataset_key)
        return self._session.scalars(stmt).first()

    def create_dataset(
        self,
        nombre_corto: str,
        nombre: str,
        descripcion: str | None = None,
        fuente: str | None = None,
        periodicidad: str | None = None,
        desagregacion_geografica: str | None = None,
        inicio_cobertura_temporal: str | None = None,
    ) -> Dataset:
        dataset = Dataset(
            nombre_corto=nombre_corto,
            nombre=nombre,
            descripcion=descripcion,
            fuente=fuente,
            periodicidad=periodicidad,
            desagregacion_geografica=desagregacion_geografica,
            inicio_cobertura_temporal=inicio_cobertura_temporal,
        )
        self._session.add(dataset)
        self._session.flush()
        return dataset

    def create_ingestion(
        self,
        dataset_id: int,
        run_id: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        created_by: str | None = None,
    ) -> Ingestion:
        ingestion = Ingestion(
            dataset_id=dataset_id,
            run_id=run_id,
            status=RunStatus.RUNNING,
            ingestion_mode=ingestion_mode,
            trigger_type=trigger_type,
            created_by=created_by,
        )
        self._session.add(ingestion)
        self._session.flush()
        return ingestion

    def update_ingestion_success(
        self,
        ingestion_id: int,
        finished_at: datetime | None = None,
    ) -> None:
        stmt = (
            update(Ingestion)
            .where(Ingestion.id == ingestion_id)
            .values(
                status=RunStatus.SUCCESS,
                finished_at=finished_at or datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def update_ingestion_failed(
        self,
        ingestion_id: int,
        error_message: str,
        finished_at: datetime | None = None,
    ) -> None:
        stmt = (
            update(Ingestion)
            .where(Ingestion.id == ingestion_id)
            .values(
                status=RunStatus.FAILED,
                error_message=error_message,
                finished_at=finished_at or datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def update_ingestion_duplicated(self, ingestion_id: int) -> None:
        stmt = (
            update(Ingestion)
            .where(Ingestion.id == ingestion_id)
            .values(
                status=RunStatus.DUPLICATED,
                finished_at=datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def find_duplicate_by_hash(
        self,
        dataset_id: int,
        hash_sha256: str,
    ) -> Archivo | None:
        stmt = (
            select(Archivo)
            .join(Ingestion)
            .where(
                Ingestion.dataset_id == dataset_id,
                Archivo.hash_sha256 == hash_sha256,
            )
        )
        return self._session.scalars(stmt).first()

    def create_archivo(
        self,
        ingestion_id: int,
        storage_path: str,
        nombre_archivo: str,
        hash_sha256: str,
        ingestion_mode: IngestionMode,
        period_label: str | None = None,
        file_extension: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        source_url: str | None = None,
        uploaded_by: str | None = None,
    ) -> Archivo:
        archivo = Archivo(
            ingestion_id=ingestion_id,
            storage_path=storage_path,
            nombre_archivo=nombre_archivo,
            file_extension=file_extension,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            hash_sha256=hash_sha256,
            period_label=period_label,
            source_url=source_url,
            uploaded_by=uploaded_by,
            ingestion_mode=ingestion_mode,
        )
        self._session.add(archivo)
        self._session.flush()
        return archivo

    def get_latest_successful_ingestion(
        self,
        dataset_id: int,
    ) -> Ingestion | None:
        stmt = (
            select(Ingestion)
            .where(
                Ingestion.dataset_id == dataset_id,
                Ingestion.status == RunStatus.SUCCESS,
            )
            .order_by(Ingestion.started_at.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()

    def get_archivos_by_ingestion(self, ingestion_id: int) -> list[Archivo]:
        stmt = select(Archivo).where(Archivo.ingestion_id == ingestion_id)
        return list(self._session.scalars(stmt).all())

    def get_latest_archivo_by_dataset(
        self,
        dataset_id: int,
    ) -> Archivo | None:
        latest_ingestion = self.get_latest_successful_ingestion(dataset_id)
        if not latest_ingestion:
            return None
        archivos = self.get_archivos_by_ingestion(latest_ingestion.id)
        return archivos[0] if archivos else None

    def list_datasets(self) -> list[Dataset]:
        stmt = select(Dataset).order_by(Dataset.nombre_corto)
        return list(self._session.scalars(stmt).all())

    def list_ingestions(
        self,
        dataset_key: str | None = None,
        limit: int = 100,
    ) -> list[Ingestion]:
        if dataset_key:
            dataset = self.get_dataset_by_key(dataset_key)
            if not dataset:
                return []
            stmt = (
                select(Ingestion)
                .where(Ingestion.dataset_id == dataset.id)
                .order_by(Ingestion.created_at.desc())
                .limit(limit)
            )
        else:
            stmt = select(Ingestion).order_by(Ingestion.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())
