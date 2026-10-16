import os
from typing import Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    app_name: str = "Deribit Tracker App"
    debug: bool = False

    # database config(postgres)
    db_name: str = "deribit_db"
    db_user: str = "postgres"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432

    # deribit.com config
    base_url: str = "https://deribit.com"
    tickers: list[str] = ["btc_usd", "eth_usd"]
    delay: float = 60

    # celery
    broker_url: str
    backend_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def db_url(self: Self) -> str:
        user_password = f"{self.db_user}:{self.db_password}"
        host_port = f"{self.db_host}:{self.db_port}"
        return f"{user_password}@{host_port}/{self.db_name}"

    @property
    def database_url_async(self: Self) -> str:
        return f"postgresql+asyncpg://{self.db_url}"

    @property
    def database_url_sync(self: Self) -> str:
        return f"postgresql://{self.db_url}"


class DevelopmentConfig(BaseConfig):
    debug: bool = True


class ProductionConfig(BaseConfig):
    debug: bool = False


class TestingConfig(BaseConfig):
    DEBUG: bool = True

    @property
    def database_url_async(self) -> str:
        return "sqlite+aiosqlite:///:memory:"

    @property
    def database_url_sync(self) -> str:
        return "sqlite:///:memory:"


def get_settings() -> BaseConfig:
    env_mode = os.getenv("ENV_MODE", "production").lower()

    if env_mode == "production":
        return ProductionConfig()
    if env_mode == "testing":
        return TestingConfig()
    return DevelopmentConfig()


settings = get_settings()
