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


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATED = "duplicated"
    FAILED = "failed"


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_area: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_person: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sources: Mapped[list[Source]] = relationship("Source", back_populates="product")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    manual_upload_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_manifest: Mapped[bool] = mapped_column(Boolean, default=True)
    expected_file_types: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    period_type: Mapped[Optional[PeriodType]] = mapped_column(SQLEnum(PeriodType), nullable=True)
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (Index("idx_sources_product_key", "product_id", "source_key", unique=True),)

    product: Mapped[Product] = relationship("Product", back_populates="sources")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SQLEnum(RunStatus), nullable=False)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    trigger_type: Mapped[TriggerType] = mapped_column(SQLEnum(TriggerType), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    airflow_dag_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    airflow_run_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped[Product] = relationship("Product")
    source: Mapped[Source] = relationship("Source")


class RawAsset(Base):
    __tablename__ = "raw_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ingestion_mode: Mapped[IngestionMode] = mapped_column(SQLEnum(IngestionMode), nullable=False)
    is_latest_for_period: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_raw_assets_product_source_period",
            "product_id",
            "source_id",
            "period_label",
        ),
        Index("idx_raw_assets_checksum", "checksum_sha256"),
        Index(
            "idx_raw_assets_latest",
            "product_id",
            "source_id",
            "period_label",
            "is_latest_for_period",
        ),
        Index(
            "idx_raw_assets_unique_version",
            "product_id",
            "source_id",
            "period_label",
            "version_number",
            unique=True,
        ),
    )

    run: Mapped[IngestionRun] = relationship("IngestionRun")
    product: Mapped[Product] = relationship("Product")
    source: Mapped[Source] = relationship("Source")


class ManualSubmission(Base):
    __tablename__ = "manual_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id"), nullable=True)
    period_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dropzone_path: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_file_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[SubmissionStatus] = mapped_column(SQLEnum(SubmissionStatus), nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ingestion_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product: Mapped[Optional[Product]] = relationship("Product")
    source: Mapped[Optional[Source]] = relationship("Source")
    processed_run: Mapped[Optional[IngestionRun]] = relationship("IngestionRun")
