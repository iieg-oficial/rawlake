from __future__ import annotations

import pytest

from rawlake.flows.ingestion_flow import run_ingestion
from rawlake.manifests.sync import SyncedDataset


class TestRunIngestionIsCallable:
    def test_flow_importable_and_callable(self):
        assert callable(run_ingestion)


class TestSyncedDatasetContract:
    def test_is_frozen(self):
        with pytest.raises((AttributeError, Exception)):
            s = SyncedDataset(id=1, nombre_corto="x")
            s.id = 2

    def test_equality_by_value(self):
        a = SyncedDataset(id=1, nombre_corto="x")
        b = SyncedDataset(id=1, nombre_corto="x")
        c = SyncedDataset(id=2, nombre_corto="x")
        assert a == b
        assert a != c
        assert hash(a) == hash(b)
