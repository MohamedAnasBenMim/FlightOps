from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx

from flightops.domain import Waypoint, WeatherCondition


class WeatherProviderError(RuntimeError):
    pass


class WeatherProvider(Protocol):
    async def conditions_for_route(
        self, waypoints: Sequence[Waypoint], departure_at: datetime
    ) -> list[WeatherCondition]: ...


class OpenMeteoWeatherProvider:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url
        self._timeout = timeout_seconds

    async def conditions_for_route(
        self, waypoints: Sequence[Waypoint], departure_at: datetime
    ) -> list[WeatherCondition]:
        if len(waypoints) < 2:
            raise ValueError("A route requires at least two waypoints")
        conditions: list[WeatherCondition] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for start, end in zip(waypoints, waypoints[1:], strict=False):
                latitude = (start.latitude + end.latitude) / 2
                longitude = (start.longitude + end.longitude) / 2
                conditions.append(
                    await self._fetch_condition(client, latitude, longitude, departure_at)
                )
        return conditions

    async def _fetch_condition(
        self,
        client: httpx.AsyncClient,
        latitude: float,
        longitude: float,
        forecast_at: datetime,
    ) -> WeatherCondition:
        params: dict[str, str | float | int] = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ("temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m"),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "forecast_days": 16,
        }
        try:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()
            payload = response.json()
            return normalize_open_meteo(payload, latitude, longitude, forecast_at)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError) as exc:
            raise WeatherProviderError(f"Open-Meteo forecast unavailable: {exc}") from exc


def normalize_open_meteo(
    payload: dict[str, object],
    latitude: float,
    longitude: float,
    forecast_at: datetime,
) -> WeatherCondition:
    hourly = payload["hourly"]
    if not isinstance(hourly, dict):
        raise ValueError("hourly data must be an object")
    raw_times = hourly["time"]
    if not isinstance(raw_times, list) or not raw_times:
        raise ValueError("hourly timestamps are missing")
    times = [datetime.fromisoformat(str(item)).replace(tzinfo=UTC) for item in raw_times]
    target = forecast_at.astimezone(UTC)
    index = min(range(len(times)), key=lambda position: abs(times[position] - target))
    if abs(times[index] - target) > timedelta(minutes=90):
        raise ValueError("forecast time is outside the provider response range")

    def optional_number(name: str) -> float | None:
        values = hourly.get(name)
        if not isinstance(values, list) or index >= len(values):
            return None
        value = values[index]
        return None if value is None else float(value)

    return WeatherCondition(
        latitude=latitude,
        longitude=longitude,
        forecast_at=times[index],
        wind_speed_mps=optional_number("wind_speed_10m"),
        wind_gust_mps=optional_number("wind_gusts_10m"),
        precipitation_mm_per_hour=optional_number("precipitation"),
        temperature_c=optional_number("temperature_2m"),
    )
