from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from rawlake.core.exceptions import ExtractorError
from rawlake.extractors.http import HttpExtractor
from rawlake.schemas.product_manifest import HttpExtractorConfig


def _build_zip(path: Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)


@pytest.fixture
def sample_imaief_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "imaief.zip"
    members = {
        "conjunto_de_datos/indice.csv": '"a.csv","x"\n',
        "conjunto_de_datos/conjunto_de_datos_imaief_entidad_jal2026_03.csv": (
            "Descriptores,2026|Enero\nvalor,100\n"
        ),
        "conjunto_de_datos/conjunto_de_datos_imaief_entidad_q roo2026_03.csv": (
            "Descriptores,2026|Enero\nvalor,200\n"
        ),
        "conjunto_de_datos/conjunto_de_datos_imaief_actividad_industrial2026_03.csv": (
            "Descriptores,2026|Enero\nvalor,300\n"
        ),
        "conjunto_de_datos/conjunto_de_datos_imaief_entidad_jal2026_03.txt": (
            '"Leyendas."\n"NA","No Aplica"\n'
        ),
        "metadatos/metadatos_imaief2026_03.txt": "Modified: 2026-07-06\n",
    }
    _build_zip(zip_path, members)
    return zip_path


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _patch_requests(monkeypatch, content: bytes) -> None:
    class _Resp:
        def __init__(self, c: bytes):
            self.content = c

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(
        "rawlake.extractors.http.requests.request",
        lambda **_: _Resp(content),
    )


class TestHttpExtractorZip:
    def test_extracts_all_csvs_from_inner_path(
        self, sample_imaief_zip: Path, monkeypatch, mock_dataset
    ):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.csv",
            filename_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        paths = extractor.run()
        try:
            names = sorted(p.name for p in paths)
            assert names == [
                "conjunto_de_datos_imaief_actividad_industrial2026_03.csv",
                "conjunto_de_datos_imaief_entidad_jal2026_03.csv",
                "conjunto_de_datos_imaief_entidad_q roo2026_03.csv",
                "indice.csv",
            ]
        finally:
            extractor.cleanup(paths)

    def test_excludes_txt_files(self, sample_imaief_zip: Path, monkeypatch, mock_dataset):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.csv",
            filename_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        paths = extractor.run()
        try:
            assert all(p.suffix == ".csv" for p in paths)
            assert not any(p.suffix == ".txt" for p in paths)
        finally:
            extractor.cleanup(paths)

    def test_preserves_q_roo_with_space(self, sample_imaief_zip: Path, monkeypatch, mock_dataset):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        paths = extractor.run()
        try:
            q_roo = [
                p for p in paths if p.name == "conjunto_de_datos_imaief_entidad_q roo2026_03.csv"
            ]
            assert len(q_roo) == 1
            assert " " in q_roo[0].name
        finally:
            extractor.cleanup(paths)

    def test_validate_passes_for_real_csvs(
        self, sample_imaief_zip: Path, monkeypatch, mock_dataset
    ):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        paths = extractor.run()
        try:
            assert extractor.validate(paths) is True
        finally:
            extractor.cleanup(paths)

    def test_raises_when_inner_glob_matches_nothing(
        self, sample_imaief_zip: Path, monkeypatch, mock_dataset
    ):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.does_not_exist",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        with pytest.raises(ExtractorError, match="No files matched"):
            extractor.run()

    def test_raw_mode_when_not_zip(self, monkeypatch, mock_dataset):
        config = HttpExtractorConfig(
            type="http",
            url="https://example.com/data.csv",
            extract_zip=True,
            inner_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, b"col\nval\n")
        paths = extractor.run()
        try:
            assert len(paths) == 1
            assert paths[0].name == "data.csv"
            assert paths[0].read_bytes() == b"col\nval\n"
        finally:
            extractor.cleanup(paths)

    def test_cleanup_removes_temp_dirs(self, sample_imaief_zip: Path, monkeypatch, mock_dataset):
        config = HttpExtractorConfig(
            type="http",
            url=f"file://{sample_imaief_zip}",
            extract_zip=True,
            inner_path="conjunto_de_datos",
            inner_glob="*.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        _patch_requests(monkeypatch, _read_bytes(sample_imaief_zip))
        paths = extractor.run()
        temp_dirs = list(extractor._temp_dirs)
        assert len(temp_dirs) >= 1
        assert all(d.exists() for d in temp_dirs)
        extractor.cleanup(paths)
        assert all(not d.exists() for d in temp_dirs)
        assert extractor._temp_dirs == []

    def test_register_temp_dir_via_base_api(self, mock_dataset):
        config = HttpExtractorConfig(
            type="http",
            url="https://example.com/x.csv",
        )
        extractor = HttpExtractor(dataset=mock_dataset, config=config)
        sentinel = Path(tempfile.mkdtemp())
        try:
            result = extractor.register_temp_dir(sentinel)
            assert result is sentinel
            assert sentinel in extractor._temp_dirs
        finally:
            if sentinel.exists():
                shutil.rmtree(sentinel, ignore_errors=True)
