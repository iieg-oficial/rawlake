from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DB_USER: str = Field(default="rawlake")
    DB_PASSWORD: str = Field(default="rawlake")
    DB_HOST: str = Field(default="localhost")
    DB_PORT: str = Field(default="5432")
    DB_NAME: str = Field(default="rawlake")
    LOG_LEVEL: str = Field(default="INFO")
    RAWLAKE_LOCAL_ROOT: str = Field(default="/mnt/datalake")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache
def get_config() -> BaseConfig:
    return BaseConfig()
