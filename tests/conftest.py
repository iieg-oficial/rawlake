from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_dataset() -> MagicMock:
    ds = MagicMock()
    ds.id = 1
    ds.nombre_corto = "test_ds"
    ds.nombre = "Test Dataset"
    return ds
