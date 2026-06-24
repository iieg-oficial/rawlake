from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from rawlake.metadata.models import (
    IngestionMode,
    IngestionRun,
    ManualSubmission,
    PeriodType,
    Product,
    RawAsset,
    RunStatus,
    Source,
    SourceType,
    SubmissionStatus,
    TriggerType,
)


class Repository:
    def __init__(self, session: Session):
        self._session = session

    def get_product_by_key(self, product_key: str) -> Optional[Product]:
        stmt = select(Product).where(Product.product_key == product_key)
        return self._session.scalars(stmt).first()

    def get_source_by_key(self, product_id: int, source_key: str) -> Optional[Source]:
        stmt = select(Source).where(
            Source.product_id == product_id, Source.source_key == source_key
        )
        return self._session.scalars(stmt).first()

    def create_product(
        self,
        product_key: str,
        name: str,
        description: Optional[str] = None,
        owner_area: Optional[str] = None,
        owner_person: Optional[str] = None,
    ) -> Product:
        product = Product(
            product_key=product_key,
            name=name,
            description=description,
            owner_area=owner_area,
            owner_person=owner_person,
        )
        self._session.add(product)
        self._session.flush()
        return product

    def create_source(
        self,
        product_id: int,
        source_key: str,
        name: str,
        source_type: SourceType,
        ingestion_mode: IngestionMode,
        description: Optional[str] = None,
        manual_upload_allowed: bool = False,
        requires_manifest: bool = True,
        expected_file_types: Optional[list[str]] = None,
        period_type: Optional[PeriodType] = None,
        schedule: Optional[str] = None,
    ) -> Source:
        source = Source(
            product_id=product_id,
            source_key=source_key,
            name=name,
            description=description,
            source_type=source_type,
            ingestion_mode=ingestion_mode,
            manual_upload_allowed=manual_upload_allowed,
            requires_manifest=requires_manifest,
            expected_file_types=expected_file_types,
            period_type=period_type,
            schedule=schedule,
        )
        self._session.add(source)
        self._session.flush()
        return source

    def create_run(
        self,
        product_id: int,
        source_id: int,
        run_id: str,
        period_label: str,
        ingestion_mode: IngestionMode,
        trigger_type: TriggerType,
        created_by: Optional[str] = None,
    ) -> IngestionRun:
        run = IngestionRun(
            product_id=product_id,
            source_id=source_id,
            run_id=run_id,
            period_label=period_label,
            status=RunStatus.RUNNING,
            ingestion_mode=ingestion_mode,
            trigger_type=trigger_type,
            created_by=created_by,
        )
        self._session.add(run)
        self._session.flush()
        return run

    def update_run_success(
        self,
        run_id: int,
        finished_at: Optional[datetime] = None,
    ) -> None:
        stmt = (
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(
                status=RunStatus.SUCCESS,
                finished_at=finished_at or datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def update_run_failed(
        self,
        run_id: int,
        error_message: str,
        finished_at: Optional[datetime] = None,
    ) -> None:
        stmt = (
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(
                status=RunStatus.FAILED,
                error_message=error_message,
                finished_at=finished_at or datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def update_run_duplicated(self, run_id: int) -> None:
        stmt = (
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(
                status=RunStatus.DUPLICATED,
                finished_at=datetime.utcnow(),
            )
        )
        self._session.execute(stmt)

    def find_duplicate_by_hash(
        self,
        product_id: int,
        source_id: int,
        period_label: str,
        checksum_sha256: str,
    ) -> Optional[RawAsset]:
        stmt = select(RawAsset).where(
            RawAsset.product_id == product_id,
            RawAsset.source_id == source_id,
            RawAsset.period_label == period_label,
            RawAsset.checksum_sha256 == checksum_sha256,
        )
        return self._session.scalars(stmt).first()

    def get_next_version_number(
        self,
        product_id: int,
        source_id: int,
        period_label: str,
    ) -> int:
        stmt = select(RawAsset).where(
            RawAsset.product_id == product_id,
            RawAsset.source_id == source_id,
            RawAsset.period_label == period_label,
        )
        existing = self._session.scalars(stmt).all()
        if not existing:
            return 1
        return max(a.version_number for a in existing) + 1

    def create_asset(
        self,
        run_id: int,
        product_id: int,
        source_id: int,
        period_label: str,
        version_number: int,
        version_timestamp: datetime,
        storage_backend: str,
        storage_path: str,
        original_file_name: str,
        checksum_sha256: str,
        ingestion_mode: IngestionMode,
        file_extension: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        source_url: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> RawAsset:
        asset = RawAsset(
            run_id=run_id,
            product_id=product_id,
            source_id=source_id,
            period_label=period_label,
            version_number=version_number,
            version_timestamp=version_timestamp,
            storage_backend=storage_backend,
            storage_path=storage_path,
            original_file_name=original_file_name,
            file_extension=file_extension,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            checksum_sha256=checksum_sha256,
            source_url=source_url,
            uploaded_by=uploaded_by,
            ingestion_mode=ingestion_mode,
            is_latest_for_period=True,
        )
        self._session.add(asset)
        self._session.flush()
        return asset

    def update_old_assets_not_latest(
        self,
        product_id: int,
        source_id: int,
        period_label: str,
        exclude_asset_id: int,
    ) -> None:
        stmt = (
            update(RawAsset)
            .where(
                RawAsset.product_id == product_id,
                RawAsset.source_id == source_id,
                RawAsset.period_label == period_label,
                RawAsset.id != exclude_asset_id,
            )
            .values(is_latest_for_period=False)
        )
        self._session.execute(stmt)

    def get_latest_asset(
        self,
        product_id: int,
        source_id: int,
        period_label: str,
    ) -> Optional[RawAsset]:
        stmt = select(RawAsset).where(
            RawAsset.product_id == product_id,
            RawAsset.source_id == source_id,
            RawAsset.period_label == period_label,
            RawAsset.is_latest_for_period == True,
        )
        return self._session.scalars(stmt).first()

    def list_products(self) -> list[Product]:
        stmt = select(Product).order_by(Product.product_key)
        return list(self._session.scalars(stmt).all())

    def list_sources(self, product_key: Optional[str] = None) -> list[Source]:
        if product_key:
            product = self.get_product_by_key(product_key)
            if not product:
                return []
            stmt = select(Source).where(Source.product_id == product.id).order_by(Source.source_key)
        else:
            stmt = select(Source).order_by(Source.source_key)
        return list(self._session.scalars(stmt).all())

    def list_runs(
        self,
        product_key: Optional[str] = None,
        limit: int = 100,
    ) -> list[IngestionRun]:
        if product_key:
            product = self.get_product_by_key(product_key)
            if not product:
                return []
            stmt = (
                select(IngestionRun)
                .where(IngestionRun.product_id == product.id)
                .order_by(IngestionRun.created_at.desc())
                .limit(limit)
            )
        else:
            stmt = select(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def create_manual_submission(
        self,
        submission_id: str,
        dropzone_path: str,
        status: SubmissionStatus = SubmissionStatus.PENDING,
        product_id: Optional[int] = None,
        source_id: Optional[int] = None,
        period_label: Optional[str] = None,
        manifest_path: Optional[str] = None,
        original_file_name: Optional[str] = None,
        submitted_by: Optional[str] = None,
    ) -> ManualSubmission:
        submission = ManualSubmission(
            submission_id=submission_id,
            product_id=product_id,
            source_id=source_id,
            period_label=period_label,
            dropzone_path=dropzone_path,
            manifest_path=manifest_path,
            original_file_name=original_file_name,
            submitted_by=submitted_by,
            status=status,
        )
        self._session.add(submission)
        self._session.flush()
        return submission

    def update_manual_submission(
        self,
        submission_id: str,
        status: Optional[SubmissionStatus] = None,
        review_notes: Optional[str] = None,
        processed_run_id: Optional[int] = None,
    ) -> Optional[ManualSubmission]:
        submission = self._session.scalars(
            select(ManualSubmission).where(ManualSubmission.submission_id == submission_id)
        ).first()
        if not submission:
            return None
        if status is not None:
            submission.status = status
        if review_notes is not None:
            submission.review_notes = review_notes
        if processed_run_id is not None:
            submission.processed_run_id = processed_run_id
        self._session.flush()
        return submission
