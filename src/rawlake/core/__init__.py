"""Core module - Componentes transversales del sistema RawLake."""

from rawlake.core.config import BaseConfig, get_config
from rawlake.core.database import get_db_session, get_session
from rawlake.core.exceptions import (
    ConfigurationError,
    DatasetNotFoundError,
    DuplicateFileError,
    ExtractorError,
    ExtractorNotFoundError,
    IngestionError,
    IngestionValidationError,
    ManifestError,
    RawLakeError,
    StorageError,
)
from rawlake.core.logging import Logger

__all__ = [
    "get_config",
    "BaseConfig",
    "get_db_session",
    "get_session",
    "Logger",
    "RawLakeError",
    "DatasetNotFoundError",
    "IngestionError",
    "IngestionValidationError",
    "StorageError",
    "DuplicateFileError",
    "ExtractorError",
    "ExtractorNotFoundError",
    "ManifestError",
    "ConfigurationError",
]
