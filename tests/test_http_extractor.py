import tempfile
import zipfile
from pathlib import Path

import pytest

from rawlake.extractors.base import ExtractorFactory, SourceConfig
from rawlake.extractors.http_extractor import HTTPZipExtractor


class TestExtractorFactory:
    def test_list_sources_returns_all(self):
        sources = ExtractorFactory.list_sources()
        assert len(sources) >= 1
        assert "imaief_mensual" in sources

    def test_list_sources_filters_by_type(self):
        sources = ExtractorFactory.list_sources(extractor_type="http_zip")
        assert len(sources) == 1
        assert "imaief_mensual" in sources

    def test_list_sources_unknown_type_returns_empty(self):
        sources = ExtractorFactory.list_sources(extractor_type="unknown_type")
        assert len(sources) == 0

    def test_get_source_config_returns_config(self):
        config = ExtractorFactory.get_source_config("imaief_mensual")
        assert config.product_key == "inegi-imaief"
        assert config.source_key == "imaief_mensual"
        assert config.extractor_type == "http_zip"
        assert "csv" in config.extract_pattern

    def test_get_source_config_raises_for_unknown(self):
        with pytest.raises(ValueError, match="Source not found"):
            ExtractorFactory.get_source_config("unknown_source")

    def test_get_extractor_returns_http_extractor(self):
        extractor = ExtractorFactory.get_extractor("imaief_mensual")
        assert isinstance(extractor, HTTPZipExtractor)


class TestHTTPZipExtractor:
    def test_validate_period_monthly_format(self):
        config = SourceConfig(
            product_key="test",
            source_key="test",
            name="Test",
            url="http://test.com/file.zip",
            extractor_type="http_zip",
            extract_pattern="*.csv",
            period_type="monthly",
            expected_file_types=["csv", "zip"],
        )
        extractor = HTTPZipExtractor(config)

        assert extractor.validate_period("2018-01") is True
        assert extractor.validate_period("2024-12") is True
        assert extractor.validate_period("2018-1") is False
        assert extractor.validate_period("201801") is False
        assert extractor.validate_period("2018-1-01") is False

    def test_extract_creates_files(self):
        config = SourceConfig(
            product_key="test",
            source_key="test_extract",
            name="Test Extract",
            url="http://test.com/file.zip",
            extractor_type="http_zip",
            extract_pattern="*.csv",
            period_type="monthly",
            expected_file_types=["csv", "zip"],
        )
        extractor = HTTPZipExtractor(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_content = "id,value\n1,100\n2,200\n"
            zip_path = Path(tmpdir) / "test.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("data.csv", csv_content)
                zf.writestr("readme.txt", "This should not be extracted")

            extracted = extractor.extract("2018-01", tmpdir, downloaded_zip_path=zip_path)

            assert len(extracted) == 1
            assert extracted[0].name == "data.csv"
            assert extracted[0].read_text() == csv_content

    def test_extract_matches_pattern(self):
        config = SourceConfig(
            product_key="test",
            source_key="test_pattern",
            name="Test Pattern",
            url="http://test.com/file.zip",
            extractor_type="http_zip",
            extract_pattern="*.csv",
            period_type="monthly",
            expected_file_types=["csv", "zip"],
        )
        extractor = HTTPZipExtractor(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("file1.csv", "csv content")
                zf.writestr("file2.txt", "text content")
                zf.writestr("nested/file3.csv", "nested csv")

            extracted = extractor.extract("2018-01", tmpdir, downloaded_zip_path=zip_path)

            assert len(extracted) == 2
            names = [e.name for e in extracted]
            assert "file1.csv" in names
            assert "file3.csv" in names
            assert "file2.txt" not in names


class TestSourceConfig:
    def test_headers_default_to_empty_dict(self):
        config = SourceConfig(
            product_key="test",
            source_key="test",
            name="Test",
            url="http://test.com",
            extractor_type="http_zip",
            extract_pattern="*.csv",
            period_type="monthly",
            expected_file_types=["csv"],
        )
        assert config.headers == {}