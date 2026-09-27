from flightops.config import get_settings
from flightops.weather import OpenMeteoWeatherProvider, WeatherProvider


def get_weather_provider() -> WeatherProvider:
    settings = get_settings()
    return OpenMeteoWeatherProvider(
        settings.open_meteo_base_url,
        settings.weather_timeout_seconds,
    )
