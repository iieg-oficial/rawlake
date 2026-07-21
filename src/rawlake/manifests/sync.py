from __future__ import annotations

from rawlake.core.database import get_db_session
from rawlake.metadata.models import Dataset
from rawlake.metadata.repository import Repository
from rawlake.schemas.product_manifest import ProductManifest


def sync_dataset_from_manifest(manifest: ProductManifest) -> Dataset:
    with get_db_session() as session:
        repo = Repository(session)
        dataset = repo.get_dataset_by_key(manifest.dataset_key)

        if dataset is None:
            dataset = repo.create_dataset(
                nombre_corto=manifest.dataset_key,
                nombre=manifest.nombre,
                fuente=manifest.fuente,
                descripcion=manifest.descripcion,
                periodicidad=manifest.periodicidad,
                desagregacion_geografica=manifest.desagregacion_geografica,
                inicio_cobertura_temporal=manifest.inicio_cobertura_temporal,
            )
        else:
            dataset.nombre = manifest.nombre
            dataset.fuente = manifest.fuente
            dataset.descripcion = manifest.descripcion
            dataset.periodicidad = manifest.periodicidad
            dataset.desagregacion_geografica = manifest.desagregacion_geografica
            dataset.inicio_cobertura_temporal = manifest.inicio_cobertura_temporal

        session.flush()
        session.refresh(dataset)
        return dataset
