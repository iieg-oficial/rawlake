from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import yaml


@dataclass
class SourceConfig:
    product_key: str
    source_key: str
    name: str
    url: str
    extractor_type: str
    extract_pattern: str
    period_type: str
    expected_file_types: list[str]
    headers: dict = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, period_label: str, output_dir: str) -> Path:
        pass

    @abstractmethod
    def validate_period(self, period_label: str) -> bool:
        pass


class ExtractorFactory:
    _sources_config: ClassVar[dict[str, SourceConfig] | None] = None

    @classmethod
    def _load_sources(cls) -> dict[str, SourceConfig]:
        if cls._sources_config is not None:
            return cls._sources_config

        config_path = Path(__file__).parent / "sources.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Sources config not found: {config_path}")

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        cls._sources_config = {}
        for key, values in data.get("sources", {}).items():
            cls._sources_config[key] = SourceConfig(
                product_key=values["product_key"],
                source_key=values["source_key"],
                name=values["name"],
                url=values["url"],
                extractor_type=values["extractor_type"],
                extract_pattern=values["extract_pattern"],
                period_type=values["period_type"],
                expected_file_types=values.get("expected_file_types", []),
                headers=values.get("headers", {}),
            )

        return cls._sources_config

    @classmethod
    def get_source_config(cls, source_key: str) -> SourceConfig:
        sources = cls._load_sources()
        if source_key not in sources:
            raise ValueError(f"Source not found: {source_key}")
        return sources[source_key]

    @classmethod
    def list_sources(cls, extractor_type: str | None = None) -> dict[str, SourceConfig]:
        sources = cls._load_sources()
        if extractor_type:
            return {
                k: v for k, v in sources.items() if v.extractor_type == extractor_type
            }
        return sources

    @classmethod
    def get_extractor(cls, source_key: str) -> BaseExtractor:
        from rawlake.extractors.http_extractor import HTTPZipExtractor

        config = cls.get_source_config(source_key)
        extractor_type = config.extractor_type

        if extractor_type == "http_zip":
            return HTTPZipExtractor(config)
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")