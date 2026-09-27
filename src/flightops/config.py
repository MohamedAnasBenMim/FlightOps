from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FlightOps"
    environment: str = "development"
    database_url: str = "sqlite:///./flightops.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
