from __future__ import annotations

import os
import tempfile


from rawlake.services.checksum_service import ChecksumService
from rawlake.services.versioning_service import VersioningService


def test_checksum_service_calculates_correctly():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("id,nombre,valor\n1,test,100\n")
        temp_path = f.name

    try:
        checksum = ChecksumService.calculate_sha256(temp_path)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)
    finally:
        os.unlink(temp_path)


def test_checksum_service_file_extension():
    assert ChecksumService.get_file_extension("/path/to/file.csv") == "csv"
    assert ChecksumService.get_file_extension("/path/to/file.tar.gz") == "gz"
    assert ChecksumService.get_file_extension("/path/to/file") == ""


def test_checksum_service_mime_type():
    assert ChecksumService.guess_mime_type("file.csv") == "text/csv"
    assert (
        ChecksumService.guess_mime_type("file.xlsx")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert ChecksumService.guess_mime_type("file.json") == "application/json"
    assert ChecksumService.guess_mime_type("file.unknown") == "application/octet-stream"


def test_checksum_service_file_size():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("id,nombre,valor\n1,test,100\n")
        temp_path = f.name

    try:
        size = ChecksumService.get_file_size(temp_path)
        assert size > 0
    finally:
        os.unlink(temp_path)


def test_versioning_service_generates_run_id():
    run_id = VersioningService.generate_run_id()
    assert run_id.startswith("run-")
    assert len(run_id) > 10


def test_versioning_service_generates_submission_id():
    submission_id = VersioningService.generate_submission_id()
    assert submission_id.startswith("submission-")
    assert len(submission_id) > 15


def test_versioning_service_format_timestamp():
    from datetime import datetime

    ts = datetime(2024, 1, 15, 10, 30, 0)
    formatted = VersioningService.format_version_timestamp(ts)
    assert formatted == "2024-01-15T10-30-00"


def test_build_version_path():
    from datetime import datetime
    from rawlake.storage.base import build_version_path

    ts = datetime(2024, 1, 15, 10, 30, 0)
    path = build_version_path(
        root="/mnt/datalake",
        product_key="test_product",
        source_key="test_source",
        period_label="2024-01",
        version_timestamp=ts,
        file_extension="csv",
    )

    assert path == (
        "/mnt/datalake/"
        "producto=test_product/"
        "fuente=test_source/"
        "periodo=2024-01/"
        "version=2024-01-15T10-30-00/"
        "original.csv"
    )
