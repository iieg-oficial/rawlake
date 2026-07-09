"""Clase base para todos los flujos de Prefect."""

from abc import ABC, abstractmethod
from typing import Any

from prefect import flow, get_run_logger

from rawlake.core.exceptions import RawLakeError


class BaseFlow(ABC):
    """
    Clase base abstracta para flujos de Prefect.

    Proporciona estructura común y manejo de errores para todos los flujos.
    Los flujos específicos deben heredar de esta clase e implementar run_flow().

    Attributes:
        flow_name: Nombre del flujo (usado en Prefect UI)
        retries: Número de reintentos en caso de fallo
        retry_delay_seconds: Segundos entre reintentos
    """

    def __init__(
        self,
        flow_name: str,
        retries: int = 0,
        retry_delay_seconds: int = 60,
    ):
        self.flow_name = flow_name
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    @abstractmethod
    def run_flow(self, **kwargs) -> Any:
        """
        Lógica principal del flujo. Debe ser implementada por subclases.

        Args:
            **kwargs: Argumentos específicos del flujo

        Returns:
            Resultado del flujo

        Raises:
            RawLakeError: Si el flujo falla
        """
        pass

    def execute(self, **kwargs) -> Any:
        """
        Ejecutar el flujo con manejo de errores y logging.

        Este método crea el flow de Prefect y ejecuta run_flow() con
        manejo automático de errores y logging.

        Args:
            **kwargs: Argumentos a pasar a run_flow()

        Returns:
            Resultado del flujo
        """
        logger = get_run_logger()

        @flow(
            name=self.flow_name,
            retries=self.retries,
            retry_delay_seconds=self.retry_delay_seconds,
        )
        def _prefect_flow(**flow_kwargs):
            try:
                logger.info(f"Starting flow: {self.flow_name}")
                result = self.run_flow(**flow_kwargs)
                logger.info(f"Flow completed successfully: {self.flow_name}")
                return result
            except RawLakeError as e:
                logger.error(f"Flow failed with RawLakeError: {e}")
                raise
            except Exception as e:
                logger.error(f"Flow failed with unexpected error: {e}")
                raise

        return _prefect_flow(**kwargs)
