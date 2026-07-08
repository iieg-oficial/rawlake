from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rawlake.storage.base import StorageBackend, build_version_path

if TYPE_CHECKING:
    pass


class LocalStorageBackend(StorageBackend):
    def store(self, source_path: str, destination_path: str) -> None:
        dest = Path(destination_path)
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
        file_extension: str,
    ) -> str:
        return build_version_path(
            root=root,
            dataset_key=dataset_key,
            period_label=period_label,
            version_timestamp=version_timestamp,
            file_extension=file_extension,
        )

    def get_backend_name(self) -> str:
        return "local"
