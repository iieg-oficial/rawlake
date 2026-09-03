from __future__ import annotations

from pathlib import Path

import pytest

from rawlake.flows.ingestion_flow import _resolve_period_labels
from rawlake.schemas.product_manifest import LandingConfig


def _path(name: str) -> Path:
    return Path(name)


class TestResolvePeriodLabelsCurrentMonth:
    def test_uses_current_month_for_all_files(self):
        landing = LandingConfig(period_label_strategy="current_month")
        files = [_path("a.csv"), _path("b.csv")]
        pairs = _resolve_period_labels(landing, files)
        assert len(pairs) == 2
        labels = {p.name: label for p, label in pairs}
        assert all(label.startswith("20") for label in labels.values())
        assert labels["a.csv"] == labels["b.csv"]


class TestResolvePeriodLabelsFromFilename:
    def test_extracts_year_month_from_filename(self):
        landing = LandingConfig(period_label_strategy="from_filename")
        files = [
            _path("conjunto_de_datos_imaief_entidad_jal2026_03.csv"),
            _path("conjunto_de_datos_imaief_actividad_industrial2025_12.csv"),
        ]
        pairs = _resolve_period_labels(landing, files)
        assert pairs[0] == (
            _path("conjunto_de_datos_imaief_entidad_jal2026_03.csv"),
            "2026-03",
        )
        assert pairs[1] == (
            _path("conjunto_de_datos_imaief_actividad_industrial2025_12.csv"),
            "2025-12",
        )

    def test_q_roo_with_space(self):
        landing = LandingConfig(period_label_strategy="from_filename")
        files = [_path("conjunto_de_datos_imaief_entidad_q roo2026_03.csv")]
        pairs = _resolve_period_labels(landing, files)
        assert pairs[0][1] == "2026-03"

    def test_raises_when_no_match_and_no_fallback(self):
        landing = LandingConfig(period_label_strategy="from_filename")
        files = [_path("indice.csv")]
        with pytest.raises(ValueError, match="Could not extract period_label"):
            _resolve_period_labels(landing, files)


class TestResolvePeriodLabelsWithFallback:
    def test_falls_back_to_current_month(self):
        landing = LandingConfig(
            period_label_strategy="from_filename_with_fallback",
            period_label_fallback="current_month",
        )
        files = [
            _path("conjunto_de_datos_imaief_entidad_jal2026_03.csv"),
            _path("indice.csv"),
        ]
        pairs = _resolve_period_labels(landing, files)
        assert pairs[0] == (
            _path("conjunto_de_datos_imaief_entidad_jal2026_03.csv"),
            "2026-03",
        )
        assert pairs[1][0] == _path("indice.csv")
        assert pairs[1][1].startswith("20")

    def test_raises_when_fallback_is_error(self):
        landing = LandingConfig(
            period_label_strategy="from_filename_with_fallback",
            period_label_fallback="error",
        )
        files = [_path("indice.csv")]
        with pytest.raises(ValueError, match="Could not extract period_label"):
            _resolve_period_labels(landing, files)

    def test_custom_pattern(self):
        landing = LandingConfig(
            period_label_strategy="from_filename",
            period_label_pattern=r"data-(?P<year>\d{4})-(?P<month>\d{2})\.csv$",
        )
        files = [_path("data-2024-07.csv")]
        pairs = _resolve_period_labels(landing, files)
        assert pairs[0] == (_path("data-2024-07.csv"), "2024-07")


class TestResolvePeriodLabelsExplicit:
    def test_explicit_overrides_strategy(self):
        landing = LandingConfig(period_label_strategy="from_filename")
        files = [
            _path("conjunto_de_datos_imaief_entidad_jal2026_03.csv"),
        ]
        pairs = _resolve_period_labels(landing, files, explicit_period="2099-12")
        assert pairs[0][1] == "2099-12"

    def test_manual_strategy_raises_for_multi_file(self):
        landing = LandingConfig(period_label_strategy="manual")
        files = [_path("a.csv"), _path("b.csv")]
        with pytest.raises(ValueError, match="manual"):
            _resolve_period_labels(landing, files)
