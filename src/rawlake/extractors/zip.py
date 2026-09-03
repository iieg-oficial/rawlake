from __future__ import annotations

import fnmatch
import zipfile
from pathlib import Path

from rawlake.core.exceptions import ExtractorError
from rawlake.schemas.product_manifest import HttpExtractorConfig

_ZIP_MAGIC = b"PK\x03\x04"


class ZipExtractor:
    def __init__(self, config: HttpExtractorConfig):
        self._config = config

    def looks_like_zip(self, content: bytes) -> bool:
        return content[:4] == _ZIP_MAGIC

    def extract(self, content: bytes, tmp_dir: Path) -> list[Path]:
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
                        f"inner_glob={self._config.inner_glob!r}"
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
            raise ExtractorError(f"Invalid ZIP: {e}") from e
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
