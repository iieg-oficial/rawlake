"""Jerarquía de excepciones personalizadas para RawLake."""


class RawLakeError(Exception):
    pass


class ConfigurationError(RawLakeError):
    pass


class DatasetNotFoundError(RawLakeError):
    def __init__(self, dataset_key: str):
        self.dataset_key = dataset_key
        super().__init__(f"Dataset not found: {dataset_key}")


class IngestionError(RawLakeError):
    pass


class IngestionValidationError(IngestionError):
    pass


class StorageError(RawLakeError):
    pass


class DuplicateFileError(RawLakeError):
    def __init__(self, hash_sha256: str, dataset_key: str):
        self.hash_sha256 = hash_sha256
        self.dataset_key = dataset_key
        super().__init__(f"Duplicate file detected (hash: {hash_sha256}) in dataset: {dataset_key}")


class ExtractorError(RawLakeError):
    pass


class ExtractorNotFoundError(RawLakeError):
    def __init__(self, extractor_type: str):
        self.extractor_type = extractor_type
        super().__init__(f"Extractor not found: {extractor_type}")


class ManifestError(RawLakeError):
    def __init__(self, dataset_key: str, reason: str):
        self.dataset_key = dataset_key
        self.reason = reason
        super().__init__(f"Invalid manifest for '{dataset_key}': {reason}")
