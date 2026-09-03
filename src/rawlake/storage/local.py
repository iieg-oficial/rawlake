from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from rawlake.core.exceptions import StorageError
from rawlake.storage.base import StorageBackend, build_version_path


class LocalStorageBackend(StorageBackend):
    def store(self, source_path: str, destination_path: str) -> None:
        dest = Path(destination_path)
        if dest.exists():
            raise StorageError(
                f"Destination already exists: {destination_path}. "
                "Refusing to overwrite. Check for path collisions in the "
                "version path generator or duplicate ingestion runs."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def generate_version_path(
        self,
        root: str,
        dataset_key: str,
        period_label: str,
        version_timestamp: datetime,
        nombre_archivo: str,
    ) -> str:
        return build_version_path(
            root=root,
            dataset_key=dataset_key,
            period_label=period_label,
            version_timestamp=version_timestamp,
            nombre_archivo=nombre_archivo,
        )

    def get_backend_name(self) -> str:
        return "local"
