from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from rawlake.core.exceptions import ExtractorNotFoundError
from rawlake.extractors.http import HttpExtractor

if TYPE_CHECKING:
    from rawlake.extractors.base import BaseExtractor
    from rawlake.metadata.models import Dataset
    from rawlake.schemas.product_manifest import ProductManifest

_BUILTIN: dict[str, type] = {
    "http": HttpExtractor,
}


def resolve_extractor(
    manifest: ProductManifest,
    dataset: Dataset,
) -> BaseExtractor:
    extractor_cfg = manifest.extractor

    if extractor_cfg.type == "http":
        return HttpExtractor(dataset=dataset, config=extractor_cfg)

    if extractor_cfg.type == "custom":
        try:
            module = importlib.import_module(extractor_cfg.module)
        except ImportError as e:
            raise ExtractorNotFoundError(f"custom:{extractor_cfg.module}") from e

        cls = getattr(module, extractor_cfg.class_name, None)
        if cls is None:
            raise ExtractorNotFoundError(
                f"custom:{extractor_cfg.module}.{extractor_cfg.class_name}"
            )

        return cls(dataset=dataset, config=extractor_cfg.config)

    raise ExtractorNotFoundError(extractor_cfg.type)
