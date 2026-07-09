"""Jerarquía de excepciones personalizadas para RawLake."""


class RawLakeError(Exception):
    """Excepción base para todos los errores de RawLake."""

    pass


class DatasetNotFoundError(RawLakeError):
    """Raised when a dataset is not found."""

    def __init__(self, dataset_key: str):
        self.dataset_key = dataset_key
        super().__init__(f"Dataset not found: {dataset_key}")


class IngestionError(RawLakeError):
    """Raised when an ingestion operation fails."""

    pass


class IngestionValidationError(IngestionError):
    """Raised when ingestion validation fails."""

    pass


class StorageError(RawLakeError):
    """Raised when storage operations fail."""

    pass


class DuplicateFileError(RawLakeError):
    """Raised when a duplicate file is detected."""

    def __init__(self, hash_sha256: str, dataset_key: str):
        self.hash_sha256 = hash_sha256
        self.dataset_key = dataset_key
        super().__init__(f"Duplicate file detected (hash: {hash_sha256}) in dataset: {dataset_key}")


class ExtractorError(RawLakeError):
    """Raised when an extractor fails."""

    pass


class ConfigurationError(RawLakeError):
    """Raised when configuration is invalid or missing."""

    pass
