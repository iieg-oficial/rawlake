from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HttpExtractorConfig(BaseModel):
    type: Literal["http"]
    url: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 60


class CustomExtractorConfig(BaseModel):
    type: Literal["custom"]
    module: str
    class_name: str = Field(alias="class")
    config: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


ExtractorConfig = HttpExtractorConfig | CustomExtractorConfig


class LandingConfig(BaseModel):
    period_label_strategy: Literal["current_month", "from_filename", "manual"] = "current_month"


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
