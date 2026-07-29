from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class StorageBackend(ABC):
    @abstractmethod
    def store(
        self,
        source_path: str,
        destination_path: str,
    ) -> None:
        """Copy a file to the storage destination."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""

    @abstractmethod
    def generate_version_path(
        self,
        root: str,
        dataset_key: str,
        period_label: str,
        version_timestamp: datetime,
        nombre_archivo: str,
    ) -> str:
        """Generate the canonical path for a versioned asset.

        The path is unique per (dataset_key, period_label, version_timestamp,
        nombre_archivo) tuple, allowing multiple files to coexist under the
        same version directory (e.g. ZIPs that expand to N CSVs).
        """

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return the name of this backend (e.g., 'local', 'minio')."""


def build_version_path(
    root: str,
    dataset_key: str,
    period_label: str,
    version_timestamp: datetime,
    nombre_archivo: str,
) -> str:
    """Build a versioned path following the datalake structure.

    Structure:
        {root}/dataset={dataset_key}/periodo={period_label}/version={timestamp}/{nombre_archivo}

    The ``nombre_archivo`` is included as the final path component so that
    multi-file datasets (e.g. a ZIP that expands to 45 CSVs under the same
    periodo) each get a unique path. A sidecar ``metadata.json`` is written
    alongside each file by the ingestion service.
    """
    ts_str = version_timestamp.strftime("%Y-%m-%dT%H-%M-%S")
    return f"{root}/dataset={dataset_key}/periodo={period_label}/version={ts_str}/{nombre_archivo}"
