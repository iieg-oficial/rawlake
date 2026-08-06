from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from rawlake.core.exceptions import ExtractorError
from rawlake.core.logging import Logger
from rawlake.extractors.base import BaseExtractor
from rawlake.extractors.zip import ZipExtractor
from rawlake.metadata.models import Dataset
from rawlake.schemas.product_manifest import HttpExtractorConfig

logger = Logger.get("http_extractor")


class HttpExtractor(BaseExtractor):
    def __init__(self, dataset: Dataset, config: HttpExtractorConfig):
        super().__init__(dataset, config.model_dump())
        self._config = config
        self._url = config.url
        self._method = config.method
        self._headers = config.headers
        self._timeout = config.timeout_seconds
        self._zip_extractor = ZipExtractor(config)

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

        content = response.content
        filename = Path(urlparse(self._url).path).name or "downloaded_file"

        if self._config.extract_zip and self._zip_extractor.looks_like_zip(content):
            tmp_dir = self.register_temp_dir(Path(tempfile.mkdtemp()))
            return self._zip_extractor.extract(content, tmp_dir)

        tmp_dir = self.register_temp_dir(Path(tempfile.mkdtemp()))
        file_path = tmp_dir / filename
        file_path.write_bytes(content)
        return [file_path]

    def validate(self, file_paths: list[Path]) -> bool:
        for path in file_paths:
            if not path.exists() or path.stat().st_size == 0:
                return False
        return True
