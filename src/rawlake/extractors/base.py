"""Clase base para todos los extractores de datos."""

from abc import ABC, abstractmethod
from pathlib import Path

from rawlake.core.exceptions import ExtractorError
from rawlake.metadata.models import Dataset


class BaseExtractor(ABC):
    """
    Clase base abstracta para extractores de datos.

    Todos los extractores específicos (HTTP, API, FTP, etc.) deben heredar
    de esta clase e implementar los métodos abstractos.

    Attributes:
        dataset: Dataset del cual se extraerán los datos
        config: Configuración del extractor (opcional)
    """

    def __init__(self, dataset: Dataset, config: dict | None = None):
        self.dataset = dataset
        self.config = config or {}

    @abstractmethod
    def extract(self, period_label: str | None = None) -> list[Path]:
        """
        Extraer datos del source y retornar lista de paths a archivos temporales.

        Args:
            period_label: Etiqueta del periodo a extraer (opcional)

        Returns:
            Lista de paths a archivos descargados

        Raises:
            ExtractorError: Si la extracción falla
        """
        pass

    @abstractmethod
    def validate(self, file_paths: list[Path]) -> bool:
        """
        Validar que los archivos extraídos sean correctos.

        Args:
            file_paths: Lista de paths a validar

        Returns:
            True si todos los archivos son válidos

        Raises:
            ExtractorError: Si la validación falla
        """
        pass

    def cleanup(self, file_paths: list[Path]) -> None:
        """
        Limpiar archivos temporales después de la extracción.

        Args:
            file_paths: Lista de paths a limpiar
        """
        for path in file_paths:
            if path.exists():
                path.unlink()

    def run(self, period_label: str | None = None) -> list[Path]:
        """
        Ejecutar el flujo completo de extracción: extract -> validate -> return.

        Args:
            period_label: Etiqueta del periodo a extraer (opcional)

        Returns:
            Lista de paths a archivos validados

        Raises:
            ExtractorError: Si cualquier paso falla
        """
        try:
            file_paths = self.extract(period_label)
            if not self.validate(file_paths):
                self.cleanup(file_paths)
                raise ExtractorError("Validation failed for extracted files")
            return file_paths
        except Exception as e:
            raise ExtractorError(f"Extraction failed: {e}") from e
