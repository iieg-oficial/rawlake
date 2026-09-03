from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HttpExtractorConfig(BaseModel):
    type: Literal["http"]
    url: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 60
    extract_zip: bool = False
    inner_path: str | None = None
    inner_glob: str = "*.csv"
    filename_glob: str = "*.csv"


class CustomExtractorConfig(BaseModel):
    type: Literal["custom"]
    module: str
    class_name: str = Field(alias="class")
    config: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


ExtractorConfig = HttpExtractorConfig | CustomExtractorConfig


PeriodLabelStrategy = Literal[
    "current_month",
    "from_filename",
    "from_filename_with_fallback",
    "manual",
]


DEFAULT_PERIOD_LABEL_PATTERN = r"(?P<year>\d{4})_(?P<month>\d{2})\.csv$"


class LandingConfig(BaseModel):
    period_label_strategy: PeriodLabelStrategy = "current_month"
    period_label_pattern: str | None = None
    period_label_fallback: Literal["current_month", "error"] | None = None


class ScheduleConfig(BaseModel):
    cron: str
    timezone: str = "America/Mexico_City"
    enabled: bool = True


class StorageConfig(BaseModel):
    backend: Literal["local", "s3", "minio"] = "local"


class ProductManifest(BaseModel):
    dataset_key: str
    nombre: str
    fuente: str | None = None
    descripcion: str | None = None
    periodicidad: str | None = None
    desagregacion_geografica: str | None = None
    inicio_cobertura_temporal: str | None = None

    extractor: ExtractorConfig
    landing: LandingConfig = Field(default_factory=LandingConfig)
    schedule: ScheduleConfig | None = None
    storage: StorageConfig = Field(default_factory=StorageConfig)
