"""Módulo de extractores de datos."""

from rawlake.extractors.base import BaseExtractor
from rawlake.extractors.http import HttpExtractor
from rawlake.extractors.registry import resolve_extractor

__all__ = ["BaseExtractor", "HttpExtractor", "resolve_extractor"]
