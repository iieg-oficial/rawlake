from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from rawlake.core.exceptions import ExtractorError
from rawlake.extractors.base import BaseExtractor
from rawlake.metadata.models import Dataset
from rawlake.schemas.product_manifest import HttpExtractorConfig


class HttpExtractor(BaseExtractor):
    def __init__(self, dataset: Dataset, config: HttpExtractorConfig):
        super().__init__(dataset, config.model_dump())
        self._url = config.url
        self._method = config.method
        self._headers = config.headers
        self._timeout = config.timeout_seconds

    def extract(self, period_label: str | None = None) -> list[Path]:
        try:
            response = requests.request(
                method=self._method,
                url=self._url,
                headers=self._headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ExtractorError(f"HTTP request failed for {self._url}: {e}") from e

        parsed = urlparse(self._url)
        filename = Path(parsed.path).name or "downloaded_file"

        tmp_dir = Path(tempfile.mkdtemp())
        file_path = tmp_dir / filename
        file_path.write_bytes(response.content)

        return [file_path]

    def validate(self, file_paths: list[Path]) -> bool:
        for path in file_paths:
            if not path.exists() or path.stat().st_size == 0:
                return False
        return True
