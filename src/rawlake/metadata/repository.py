from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from rawlake.metadata.models import (
    Archivo,
    Dataset,
    Distribucion,
    Ingestion,
    IngestionConfig,
    IngestionMode,
    PeriodType,
    RunStatus,
    SourceType,
    TriggerType,
)


class Repository:
    def __init__(self, session: Session):
        self._session = session

    def get_dataset_by_key(self, dataset_key: str) -> Optional[Dataset]:
        stmt = select(Dataset).where(Dataset.nombre_corto == dataset_key)
        return self._session.scalars(stmt).first()

    def get_distribucion_by_key(
        self, dataset_id: int, distribucion_key: str
    ) -> Optional[Distribucion]:
        stmt = select(Distribucion).where(
            Distribucion.dataset_id == dataset_id, Distribucion.nombre == distribucion_key
        )
        return self._session.scalars(stmt).first()

    def create_dataset(
        self,
        nombre_corto: str,
        nombre: str,
        descripcion: Optional[str] = None,
        fuente: Optional[str] = None,
        periodicidad: Optional[str] = None,
        desagregacion_geografica: Optional[str] = None,
        inicio_cobertura_temporal: Optional[str] = None,
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

    def create_distribucion(
        self,
        dataset_id: int,
        nombre: str,
        tipo_de_acceso: SourceType,
        descripcion: Optional[str] = None,
        manual_upload_allowed: bool = False,
        url: Optional[str] = None,
    ) -> Distribucion:
        distribucion = Distribucion(
            dataset_id=dataset_id,
            nombre=nombre,
            descripcion=descripcion,
            tipo_de_acceso=tipo_de_acceso,
            manual_upload_allowed=manual_upload_allowed,
            url=url,
        )
        self._session.add(distribucion)
        self._session.flush()
        return distribucion

    def create_ingestion_config(
        self,
        distribucion_id: int,
        extractor_class: str,
        ingestion_mode: IngestionMode,
        period_type: Optional[PeriodType] = None,
        expected_file_types: Optional[list[str]] = None,
        schedule: Optional[str] = None,
    ) -> IngestionConfig:
        config = IngestionConfig(
            distribucion_id=distribucion_id,
            extractor_class=extractor_class,
            ingestion_mode=ingestion_mode,
            period_type=period_type,
            expected_file_types=expected_file_types,
            schedule=schedule,
        )
        self._session.add(config)
        self._session.flush()
        return config

    def create_ingestion(
        self,
        dataset_id: int,
        distribucion_id: int,
        run_id: str,
        period_label: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        created_by: Optional[str] = None,
    ) -> Ingestion:
        ingestion = Ingestion(
            dataset_id=dataset_id,
            distribucion_id=distribucion_id,
            run_id=run_id,
            period_label=period_label,
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
        finished_at: Optional[datetime] = None,
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
        finished_at: Optional[datetime] = None,
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
        distribucion_id: int,
        period_label: str,
        hash_sha256: str,
    ) -> Optional[Archivo]:
        stmt = select(Archivo).where(
            Archivo.distribucion_id == distribucion_id,
            Archivo.period_label == period_label,
            Archivo.hash_sha256 == hash_sha256,
        )
        return self._session.scalars(stmt).first()

    def get_next_version_number(
        self,
        distribucion_id: int,
        period_label: str,
    ) -> int:
        stmt = select(Archivo).where(
            Archivo.distribucion_id == distribucion_id,
            Archivo.period_label == period_label,
        )
        existing = self._session.scalars(stmt).all()
        if not existing:
            return 1
        return max(a.version_number for a in existing) + 1

    def create_archivo(
        self,
        ingestion_id: int,
        distribucion_id: int,
        period_label: str,
        version_number: int,
        version_timestamp: datetime,
        storage_backend: str,
        storage_path: str,
        nombre_archivo: str,
        hash_sha256: str,
        ingestion_mode: IngestionMode,
        file_extension: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        source_url: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> Archivo:
        archivo = Archivo(
            ingestion_id=ingestion_id,
            distribucion_id=distribucion_id,
            period_label=period_label,
            version_number=version_number,
            version_timestamp=version_timestamp,
            storage_backend=storage_backend,
            storage_path=storage_path,
            nombre_archivo=nombre_archivo,
            file_extension=file_extension,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            hash_sha256=hash_sha256,
            source_url=source_url,
            uploaded_by=uploaded_by,
            ingestion_mode=ingestion_mode,
            is_latest_for_period=True,
        )
        self._session.add(archivo)
        self._session.flush()
        return archivo

    def update_old_archivos_not_latest(
        self,
        distribucion_id: int,
        period_label: str,
        exclude_archivo_id: int,
    ) -> None:
        stmt = (
            update(Archivo)
            .where(
                Archivo.distribucion_id == distribucion_id,
                Archivo.period_label == period_label,
                Archivo.id != exclude_archivo_id,
            )
            .values(is_latest_for_period=False)
        )
        self._session.execute(stmt)

    def get_latest_archivo(
        self,
        distribucion_id: int,
        period_label: str,
    ) -> Optional[Archivo]:
        stmt = select(Archivo).where(
            Archivo.distribucion_id == distribucion_id,
            Archivo.period_label == period_label,
            Archivo.is_latest_for_period == True,
        )
        return self._session.scalars(stmt).first()

    def list_datasets(self) -> list[Dataset]:
        stmt = select(Dataset).order_by(Dataset.nombre_corto)
        return list(self._session.scalars(stmt).all())

    def list_distribuciones(self, dataset_key: Optional[str] = None) -> list[Distribucion]:
        if dataset_key:
            dataset = self.get_dataset_by_key(dataset_key)
            if not dataset:
                return []
            stmt = (
                select(Distribucion)
                .where(Distribucion.dataset_id == dataset.id)
                .order_by(Distribucion.nombre)
            )
        else:
            stmt = select(Distribucion).order_by(Distribucion.nombre)
        return list(self._session.scalars(stmt).all())

    def list_ingestions(
        self,
        dataset_key: Optional[str] = None,
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
