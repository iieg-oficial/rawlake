from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    BigInteger,
    ARRAY,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import enum


class IngestionMode(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class SourceType(str, enum.Enum):
    MANUAL_UPLOAD = "manual_upload"
    HTTP_FILE = "http_file"
    API_JSON = "api_json"


class PeriodType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DUPLICATED = "duplicated"
    REJECTED = "rejected"
    PARTIAL = "partial"


class TriggerType(str, enum.Enum):
    SCHEDULED = "scheduled"
    MANUAL_AIRFLOW = "manual_airflow"
    MANUAL_DROPZONE = "manual_dropzone"
    MANUAL_CLI = "manual_cli"
    BACKFILL = "backfill"
    RETRY = "retry"


class LocatorType(str, enum.Enum):
    ROOT = "root"
    SHEET = "sheet"
    MEMBER = "member"
    JSON_PATH = "json_path"
    XPATH = "xpath"


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_corto: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    fuente: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    periodicidad: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    desagregacion_geografica: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inicio_cobertura_temporal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    distribuciones: Mapped[list[Distribucion]] = relationship(
        "Distribucion", back_populates="dataset"
    )
    ingestions: Mapped[list[Ingestion]] = relationship("Ingestion", back_populates="dataset")


class Distribucion(Base):
    __tablename__ = "distribuciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo_de_acceso: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False)
    manual_upload_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_distribuciones_dataset_nombre", "dataset_id", "nombre", unique=True),
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="distribuciones")
    ingestion_config: Mapped[Optional[IngestionConfig]] = relationship(
        "IngestionConfig", back_populates="distribucion", uselist=False
    )
    ingestions: Mapped[list[Ingestion]] = relationship("Ingestion", back_populates="distribucion")
    archivos: Mapped[list[Archivo]] = relationship("Archivo", back_populates="distribucion")
    recurso_datos: Mapped[list[RecursoDatos]] = relationship(
        "RecursoDatos", back_populates="distribucion"
    )


class IngestionConfig(Base):
    __tablename__ = "ingestion_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    distribucion_id: Mapped[int] = mapped_column(ForeignKey("distribuciones.id"), nullable=False)
    extractor_class: Mapped[str] = mapped_column(String(100), nullable=False)
    period_type: Mapped[Optional[PeriodType]] = mapped_column(SQLEnum(PeriodType), nullable=True)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    expected_file_types: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    distribucion: Mapped[Distribucion] = relationship(
        "Distribucion", back_populates="ingestion_config"
    )


class Ingestion(Base):
    __tablename__ = "ingestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    distribucion_id: Mapped[int] = mapped_column(ForeignKey("distribuciones.id"), nullable=False)
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SQLEnum(RunStatus), nullable=False)
    trigger_type: Mapped[TriggerType] = mapped_column(SQLEnum(TriggerType), nullable=False)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    nombre_archivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dropzone_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manifest_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    orchestrator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    orchestrator_flow_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    orchestrator_run_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="ingestions")
    distribucion: Mapped[Distribucion] = relationship("Distribucion", back_populates="ingestions")
    archivos: Mapped[list[Archivo]] = relationship("Archivo", back_populates="ingestion")


class RecursoDatos(Base):
    __tablename__ = "recurso_datos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    distribucion_id: Mapped[int] = mapped_column(ForeignKey("distribuciones.id"), nullable=False)
    recurso_key: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_recurso_datos_distribucion_key", "distribucion_id", "recurso_key", unique=True),
    )

    distribucion: Mapped[Distribucion] = relationship(
        "Distribucion", back_populates="recurso_datos"
    )
    archivo_recursos: Mapped[list[ArchivoRecurso]] = relationship(
        "ArchivoRecurso", back_populates="recurso_datos"
    )


class Archivo(Base):
    __tablename__ = "archivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingestion_id: Mapped[int] = mapped_column(ForeignKey("ingestions.id"), nullable=False)
    distribucion_id: Mapped[int] = mapped_column(ForeignKey("distribuciones.id"), nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_latest_for_period: Mapped[bool] = mapped_column(Boolean, default=False)
    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    fecha_ingesta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_archivos_hash", "hash_sha256"),
        Index("idx_archivos_period", "period_label"),
        Index(
            "idx_archivos_latest",
            "distribucion_id",
            "period_label",
            "is_latest_for_period",
        ),
        Index(
            "idx_archivos_unique_version",
            "distribucion_id",
            "period_label",
            "version_number",
            unique=True,
        ),
    )

    ingestion: Mapped[Ingestion] = relationship("Ingestion", back_populates="archivos")
    distribucion: Mapped[Distribucion] = relationship("Distribucion", back_populates="archivos")
    archivo_recursos: Mapped[list[ArchivoRecurso]] = relationship(
        "ArchivoRecurso", back_populates="archivo"
    )


class ArchivoRecurso(Base):
    __tablename__ = "archivo_recurso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivos.id"), nullable=False)
    recurso_datos_id: Mapped[int] = mapped_column(ForeignKey("recurso_datos.id"), nullable=False)
    locator_type: Mapped[LocatorType] = mapped_column(SQLEnum(LocatorType), nullable=False)
    locator_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_archivo_recurso_unique",
            "archivo_id",
            "recurso_datos_id",
            unique=True,
        ),
    )

    archivo: Mapped[Archivo] = relationship("Archivo", back_populates="archivo_recursos")
    recurso_datos: Mapped[RecursoDatos] = relationship(
        "RecursoDatos", back_populates="archivo_recursos"
    )
