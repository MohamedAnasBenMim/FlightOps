from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FlightOps"
    environment: str = "development"
    database_url: str | None = None
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = "flightops"
    db_username: str | None = None
    db_password: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_seconds: float = 10.0

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_host and self.db_username and self.db_password:
            username = quote_plus(self.db_username)
            password = quote_plus(self.db_password)
            return (
                f"postgresql+psycopg://{username}:{password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return "sqlite:///./flightops.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
