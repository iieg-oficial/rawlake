from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from rawlake.core.exceptions import StorageError
from rawlake.storage.base import build_version_path
from rawlake.storage.local import LocalStorageBackend


class TestBuildVersionPath:
    def test_includes_nombre_archivo_as_final_component(self):
        ts = datetime(2024, 1, 15, 10, 30, 0)
        path = build_version_path(
            root="/mnt/datalake",
            dataset_key="inegi_imaief",
            period_label="2026-03",
            version_timestamp=ts,
            nombre_archivo="conjunto_de_datos_imaief_entidad_jal2026_03.csv",
        )
        assert path == (
            "/mnt/datalake/"
            "dataset=inegi_imaief/"
            "periodo=2026-03/"
            "version=2024-01-15T10-30-00/"
            "conjunto_de_datos_imaief_entidad_jal2026_03.csv"
        )

    def test_preserves_q_roo_with_space(self):
        ts = datetime(2026, 3, 1, 0, 0, 0)
        path = build_version_path(
            root="/tmp/datalake",
            dataset_key="inegi_imaief",
            period_label="2026-03",
            version_timestamp=ts,
            nombre_archivo="conjunto_de_datos_imaief_entidad_q roo2026_03.csv",
        )
        assert path.endswith("conjunto_de_datos_imaief_entidad_q roo2026_03.csv")


class TestBuildVersionPathUniqueness:
    """Regression for the multi-file path collision bug.

    Before the fix, two files with the same dataset/periodo/version_timestamp
    collapsed onto the same 'original.csv' path, so shutil.copy2 in
    LocalStorageBackend.store() silently overwrote the first file with the
    second. 45 archivos mapped to 2 physical files.
    """

    def test_two_files_same_periodo_get_different_paths(self):
        ts = datetime(2026, 7, 29, 17, 8, 29)
        a = build_version_path(
            root="/tmp/datalake",
            dataset_key="inegi_imaief",
            period_label="2026-03",
            version_timestamp=ts,
            nombre_archivo="conjunto_de_datos_imaief_entidad_jal2026_03.csv",
        )
        b = build_version_path(
            root="/tmp/datalake",
            dataset_key="inegi_imaief",
            period_label="2026-03",
            version_timestamp=ts,
            nombre_archivo="conjunto_de_datos_imaief_entidad_mich2026_03.csv",
        )
        assert a != b
        assert Path(a).parent == Path(b).parent

    def test_imaief_full_batch_paths_are_unique(self):
        """Simulate the 45-file IMAIEF batch and assert all paths are unique."""
        ts = datetime(2026, 7, 29, 17, 8, 29)
        filenames = (
            [
                f"conjunto_de_datos_imaief_actividad_{tag}2026_03.csv"
                for tag in [
                    "212",
                    "21np",
                    "21p",
                    "2211",
                    "222",
                    "232",
                    "312",
                    "31_33",
                    "322",
                    "33",
                    "industrial",
                ]
            ]
            + [
                f"conjunto_de_datos_imaief_entidad_{state}2026_03.csv"
                for state in [
                    "ags",
                    "bc",
                    "bcs",
                    "camp",
                    "cdmx",
                    "chih",
                    "chis",
                    "coah",
                    "col",
                    "dgo",
                    "gro",
                    "gto",
                    "hgo",
                    "jal",
                    "mex",
                    "mich",
                    "mor",
                    "nacional",
                    "nay",
                    "nl",
                    "oax",
                    "pue",
                    "q roo",
                    "qro",
                    "sin",
                    "slp",
                    "son",
                    "tab",
                    "tamps",
                    "tlax",
                    "ver",
                    "yuc",
                    "zac",
                ]
            ]
            + ["indice.csv"]
        )
        assert len(filenames) == 45

        paths = [
            build_version_path(
                root="/tmp/datalake",
                dataset_key="inegi_imaief",
                period_label=pl,
                version_timestamp=ts,
                nombre_archivo=name,
            )
            for name, pl in ([(f, "2026-03") for f in filenames[:-1]] + [("indice.csv", "2026-07")])
        ]
        assert len(set(paths)) == 45
        assert sum(1 for p in paths if "/periodo=2026-03/" in p) == 44
        assert sum(1 for p in paths if "/periodo=2026-07/" in p) == 1


class TestLocalStorageBackendStoreRefusesOverwrite:
    def test_raises_when_destination_exists(self, tmp_path):
        backend = LocalStorageBackend()
        src = tmp_path / "source.csv"
        src.write_text("hello")
        dst = tmp_path / "subdir" / "dest.csv"
        dst.parent.mkdir(parents=True)
        dst.write_text("existing content")

        with pytest.raises(StorageError, match="already exists"):
            backend.store(str(src), str(dst))

    def test_succeeds_when_destination_is_new(self, tmp_path):
        backend = LocalStorageBackend()
        src = tmp_path / "source.csv"
        src.write_text("hello")
        dst = tmp_path / "subdir" / "dest.csv"

        backend.store(str(src), str(dst))

        assert dst.read_text() == "hello"


class TestLocalStorageBackendGenerateVersionPath:
    def test_delegates_to_build_version_path(self):
        backend = LocalStorageBackend()
        ts = datetime(2026, 7, 29, 17, 8, 29)
        path = backend.generate_version_path(
            root="/tmp/datalake",
            dataset_key="inegi_imaief",
            period_label="2026-03",
            version_timestamp=ts,
            nombre_archivo="file.csv",
        )
        expected = (
            "/tmp/datalake/dataset=inegi_imaief/"
            "periodo=2026-03/version=2026-07-29T17-08-29/file.csv"
        )
        assert path == expected

    def test_backend_name_is_local(self):
        assert LocalStorageBackend().get_backend_name() == "local"
