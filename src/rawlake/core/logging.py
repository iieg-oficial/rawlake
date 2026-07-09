import logging
import sys


class Logger:
    _instances: dict[str, logging.Logger] = {}

    def __init__(self, name: str, level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    @classmethod
    def get(cls, name: str, level: int | None = None) -> "Logger":
        if name not in cls._instances:
            cls._instances[name] = cls(name, level or logging.INFO)
        return cls._instances[name]

    def info(self, msg: str, **kwargs) -> None:
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._logger.error(msg, **kwargs)

    def debug(self, msg: str, **kwargs) -> None:
        self._logger.debug(msg, **kwargs)
