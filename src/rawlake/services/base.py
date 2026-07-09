"""Clase base para todos los servicios de RawLake."""

from abc import ABC

from rawlake.core.database import get_db_session
from rawlake.metadata.repository import Repository


class BaseService(ABC):
    """
    Clase base abstracta para servicios.

    Proporciona acceso común al repositorio y gestión de sesiones de BD.
    Todos los servicios específicos deben heredar de esta clase.

    Attributes:
        _repo: Instancia del repositorio para operaciones de BD
    """

    def __init__(self, repository: Repository | None = None):
        """
        Inicializar el servicio con un repositorio.

        Args:
            repository: Instancia del repositorio (opcional, se crea uno nuevo si None)
        """
        if repository is None:
            # Crear una sesión temporal si no se proporciona repositorio
            # Los servicios que necesiten transacciones deben manejar esto explícitamente
            with get_db_session() as session:
                self._repo = Repository(session)
        else:
            self._repo = repository

    @property
    def repository(self) -> Repository:
        """Acceso de solo lectura al repositorio."""
        return self._repo
