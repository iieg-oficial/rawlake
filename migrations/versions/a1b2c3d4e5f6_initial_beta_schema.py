"""initial beta schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-07-08 10:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ingestionmode = postgresql.ENUM("MANUAL", "AUTOMATED", "HYBRID", name="ingestionmode")
    ingestionmode.create(op.get_bind(), checkfirst=True)

    runstatus = postgresql.ENUM("RUNNING", "SUCCESS", "FAILED", "DUPLICATED", name="runstatus")
    runstatus.create(op.get_bind(), checkfirst=True)

    triggertype = postgresql.ENUM(
        "SCHEDULED",
        "MANUAL_AIRFLOW",
        "MANUAL_DROPZONE",
        "MANUAL_CLI",
        "BACKFILL",
        "RETRY",
        name="triggertype",
    )
    triggertype.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_corto", sa.String(length=100), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("fuente", sa.Text(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("periodicidad", sa.Text(), nullable=True),
        sa.Column("desagregacion_geografica", sa.Text(), nullable=True),
        sa.Column("inicio_cobertura_temporal", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre_corto"),
    )

    op.create_table(
        "ingestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "RUNNING",
                "SUCCESS",
                "FAILED",
                "DUPLICATED",
                name="runstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "trigger_type",
            postgresql.ENUM(
                "SCHEDULED",
                "MANUAL_AIRFLOW",
                "MANUAL_DROPZONE",
                "MANUAL_CLI",
                "BACKFILL",
                "RETRY",
                name="triggertype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "ingestion_mode",
            postgresql.ENUM(
                "MANUAL", "AUTOMATED", "HYBRID", name="ingestionmode", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("orchestrator_name", sa.String(length=100), nullable=True),
        sa.Column("orchestrator_flow_id", sa.String(length=100), nullable=True),
        sa.Column("orchestrator_run_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("idx_ingestions_dataset_status", "ingestions", ["dataset_id", "status"])
    op.create_index("idx_ingestions_dataset_started", "ingestions", ["dataset_id", "started_at"])

    op.create_table(
        "archivos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingestion_id", sa.Integer(), nullable=False),
        sa.Column("nombre_archivo", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("hash_sha256", sa.String(length=64), nullable=False),
        sa.Column("period_label", sa.String(length=50), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_extension", sa.String(length=20), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=100), nullable=True),
        sa.Column(
            "ingestion_mode",
            postgresql.ENUM(
                "MANUAL", "AUTOMATED", "HYBRID", name="ingestionmode", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("fecha_ingesta", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_id"], ["ingestions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_archivos_hash", "archivos", ["hash_sha256"])
    op.create_index("idx_archivos_ingestion", "archivos", ["ingestion_id"])


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_archivos_ingestion")
    op.execute("DROP INDEX IF EXISTS idx_archivos_hash")
    op.drop_table("archivos")

    op.execute("DROP INDEX IF EXISTS idx_ingestions_dataset_started")
    op.execute("DROP INDEX IF EXISTS idx_ingestions_dataset_status")
    op.drop_table("ingestions")

    op.drop_table("datasets")

    op.execute("DROP TYPE IF EXISTS triggertype")
    op.execute("DROP TYPE IF EXISTS runstatus")
    op.execute("DROP TYPE IF EXISTS ingestionmode")
