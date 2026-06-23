from __future__ import annotations

import hashlib
from pathlib import Path


class ChecksumService:
    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        return Path(file_path).stat().st_size

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension without the dot."""
        return Path(file_path).suffix.lstrip(".")

    @staticmethod
    def guess_mime_type(file_path: str) -> str:
        """Guess MIME type from file extension."""
        ext = ChecksumService.get_file_extension(file_path).lower()
        mime_types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "json": "application/json",
            "zip": "application/zip",
            "pdf": "application/pdf",
            "txt": "text/plain",
        }
        return mime_types.get(ext, "application/octet-stream")
