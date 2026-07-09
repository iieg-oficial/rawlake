"""Core module - Componentes transversales del sistema RawLake."""

from rawlake.core.config import BaseConfig, get_config
from rawlake.core.database import get_db_session, get_session, init_db
from rawlake.core.exceptions import (
    ConfigurationError,
    DatasetNotFoundError,
    DuplicateFileError,
    ExtractorError,
    IngestionError,
    IngestionValidationError,
    RawLakeError,
    StorageError,
)
from rawlake.core.logging import Logger

__all__ = [
    # Config
    "get_config",
    "BaseConfig",
    # Database
    "get_db_session",
    "get_session",
    "init_db",
    # Logging
    "Logger",
    # Exceptions
    "RawLakeError",
    "DatasetNotFoundError",
    "IngestionError",
    "IngestionValidationError",
    "StorageError",
    "DuplicateFileError",
    "ExtractorError",
    "ConfigurationError",
]
