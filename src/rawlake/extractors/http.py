from __future__ import annotations

import fnmatch
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from rawlake.core.exceptions import ExtractorError
from rawlake.core.logging import Logger
from rawlake.extractors.base import BaseExtractor
from rawlake.metadata.models import Dataset
from rawlake.schemas.product_manifest import HttpExtractorConfig

logger = Logger.get("http_extractor")

_ZIP_MAGIC = b"PK\x03\x04"


class HttpExtractor(BaseExtractor):
    def __init__(self, dataset: Dataset, config: HttpExtractorConfig):
        super().__init__(dataset, config.model_dump())
        self._config = config
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

        content = response.content
        filename = Path(urlparse(self._url).path).name or "downloaded_file"

        if self._config.extract_zip and self._looks_like_zip(content):
            return self._extract_zip(content)

        tmp_dir = self.register_temp_dir(Path(tempfile.mkdtemp()))
        file_path = tmp_dir / filename
        file_path.write_bytes(content)
        return [file_path]

    def _looks_like_zip(self, content: bytes) -> bool:
        return content[:4] == _ZIP_MAGIC

    def _extract_zip(self, content: bytes) -> list[Path]:
        tmp_dir = self.register_temp_dir(Path(tempfile.mkdtemp()))
        raw_zip = tmp_dir / "_payload.zip"
        raw_zip.write_bytes(content)

        try:
            with zipfile.ZipFile(raw_zip) as zf:
                members = zf.namelist()
                if self._config.inner_path:
                    prefix = self._config.inner_path.rstrip("/") + "/"
                else:
                    prefix = self._detect_top_dir(members)

                selected = [
                    name
                    for name in members
                    if name.startswith(prefix)
                    and not name.endswith("/")
                    and fnmatch.fnmatch(Path(name).name, self._config.inner_glob)
                ]

                if not selected:
                    raise ExtractorError(
                        f"No files matched inner_path={self._config.inner_path!r} "
                        f"inner_glob={self._config.inner_glob!r} in {self._url}"
                    )

                for name in selected:
                    zf.extract(name, tmp_dir)

                extracted: list[Path] = []
                for name in selected:
                    full = tmp_dir / name
                    if not self._matches_filename_glob(full.name):
                        continue
                    extracted.append(full)
                return extracted
        except zipfile.BadZipFile as e:
            raise ExtractorError(f"Invalid ZIP at {self._url}: {e}") from e
        finally:
            raw_zip.unlink(missing_ok=True)

    def _detect_top_dir(self, members: list[str]) -> str:
        tops = {name.split("/", 1)[0] for name in members if name and not name.startswith("/")}
        dirs = {t for t in tops if t and ("/" in name for name in members if name.startswith(t))}
        if len(dirs) == 1:
            return next(iter(dirs)) + "/"
        return ""

    def _matches_filename_glob(self, name: str) -> bool:
        pattern = self._config.filename_glob
        if not pattern:
            return True
        return fnmatch.fnmatch(name, pattern)

    def validate(self, file_paths: list[Path]) -> bool:
        for path in file_paths:
            if not path.exists() or path.stat().st_size == 0:
                return False
        return True
