from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class IngestionMode(StrEnum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DUPLICATED = "duplicated"


class TriggerType(StrEnum):
    SCHEDULED = "scheduled"
    MANUAL_AIRFLOW = "manual_airflow"
    MANUAL_DROPZONE = "manual_dropzone"
    MANUAL_CLI = "manual_cli"
    BACKFILL = "backfill"
    RETRY = "retry"


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_corto: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    fuente: Mapped[str | None] = mapped_column(Text, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    periodicidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    desagregacion_geografica: Mapped[str | None] = mapped_column(Text, nullable=True)
    inicio_cobertura_temporal: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ingestions: Mapped[list[Ingestion]] = relationship("Ingestion", back_populates="dataset")


class Ingestion(Base):
    __tablename__ = "ingestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SQLEnum(RunStatus), nullable=False)
    trigger_type: Mapped[TriggerType] = mapped_column(SQLEnum(TriggerType), nullable=False)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    orchestrator_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    orchestrator_flow_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    orchestrator_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ingestions_dataset_status", "dataset_id", "status"),
        Index("idx_ingestions_dataset_started", "dataset_id", "started_at"),
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="ingestions")
    archivos: Mapped[list[Archivo]] = relationship("Archivo", back_populates="ingestion")


class Archivo(Base):
    __tablename__ = "archivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingestion_id: Mapped[int] = mapped_column(ForeignKey("ingestions.id"), nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    period_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    fecha_ingesta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_archivos_hash", "hash_sha256"),
        Index("idx_archivos_ingestion", "ingestion_id"),
    )

    ingestion: Mapped[Ingestion] = relationship("Ingestion", back_populates="archivos")
