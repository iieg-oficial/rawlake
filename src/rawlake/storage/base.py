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
        product_key: str,
        source_key: str,
        period_label: str,
        version_timestamp: datetime,
        file_extension: str,
    ) -> str:
        """Generate the canonical path for a versioned asset."""

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return the name of this backend (e.g., 'local', 'minio')."""


def build_version_path(
    root: str,
    product_key: str,
    source_key: str,
    period_label: str,
    version_timestamp: datetime,
    file_extension: str,
) -> str:
    """Build a versioned path following the datalake structure.

    Structure:
        {root}/producto={product_key}/fuente={source_key}/periodo={period_label}/version={timestamp}/original.{ext}
    """
    ts_str = version_timestamp.strftime("%Y-%m-%dT%H-%M-%S")
    return (
        f"{root}/"
        f"producto={product_key}/"
        f"fuente={source_key}/"
        f"periodo={period_label}/"
        f"version={ts_str}/"
        f"original.{file_extension}"
    )
