from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

from rawlake.extractors.base import BaseExtractor, SourceConfig
from rawlake.utils import Logger


class HTTPZipExtractor(BaseExtractor):
    def __init__(self, config: SourceConfig):
        self.config = config
        self._logger = Logger.get(__name__)

    def extract(
        self, period_label: str, output_dir: str, downloaded_zip_path: Optional[Path] = None
    ) -> list[Path]:
        if not self.validate_period(period_label):
            raise ValueError(f"Invalid period format: {period_label}")

        self._logger.info(f"Downloading {self.config.source_key} for period {period_label}...")

        if downloaded_zip_path is None:
            downloaded_zip_path = self._download(period_label)

        self._logger.info(f"Extracting: {downloaded_zip_path}")

        extracted_files = self._extract_zip(downloaded_zip_path, output_dir, period_label)

        self._logger.info(f"Extracted {len(extracted_files)} file(s)")
        for f in extracted_files:
            self._logger.info(f"  - {f}")

        return extracted_files

    def validate_period(self, period_label: str) -> bool:
        if self.config.period_type == "monthly":
            return len(period_label) == 7 and period_label[4] == "-"
        return True

    def _download(self, period_label: str) -> Path:
        download_dir = Path(tempfile.gettempdir()) / "rawlake" / "downloads" / self.config.source_key
        download_dir.mkdir(parents=True, exist_ok=True)

        zip_path = download_dir / f"{period_label}.zip"

        url = self.config.url
        self._logger.info(f"Downloading from: {url}")

        try:
            with urllib.request.urlopen(url) as response:
                with open(zip_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)
        except Exception as e:
            raise RuntimeError(f"Failed to download {url}: {e}")

        self._logger.info(f"Downloaded to: {zip_path}")
        return zip_path

    def _extract_zip(self, zip_path: Path, output_dir: str, period_label: str) -> list[Path]:
        extract_dir = Path(output_dir) / self.config.source_key / period_label
        extract_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if self._matches_pattern(member):
                    zf.extract(member, extract_dir)
                    extracted_files.append(extract_dir / member)

        if not extracted_files:
            raise RuntimeError(f"No files matching pattern '{self.config.extract_pattern}' found in ZIP")

        return extracted_files

    def _matches_pattern(self, filename: str) -> bool:
        import fnmatch

        pattern = self.config.extract_pattern.replace(".", r"\.").replace("*", ".*")
        filename_only = Path(filename).name
        return fnmatch.fnmatch(filename_only, self.config.extract_pattern)