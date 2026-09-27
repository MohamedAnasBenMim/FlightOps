from datetime import UTC, datetime

import pytest

from flightops.weather import normalize_open_meteo


def test_normalize_open_meteo_selects_nearest_hour() -> None:
    payload: dict[str, object] = {
        "hourly": {
            "time": ["2026-09-28T08:00", "2026-09-28T09:00"],
            "temperature_2m": [19.0, 20.0],
            "precipitation": [0.0, 0.2],
            "wind_speed_10m": [4.0, 5.0],
            "wind_gusts_10m": [6.0, 7.0],
        }
    }
    result = normalize_open_meteo(
        payload,
        36.8,
        10.2,
        datetime(2026, 9, 28, 8, 50, tzinfo=UTC),
    )
    assert result.forecast_at == datetime(2026, 9, 28, 9, tzinfo=UTC)
    assert result.wind_speed_mps == 5


def test_normalize_open_meteo_preserves_missing_metric() -> None:
    payload: dict[str, object] = {
        "hourly": {
            "time": ["2026-09-28T08:00"],
            "temperature_2m": [None],
            "precipitation": [0],
            "wind_speed_10m": [4],
            "wind_gusts_10m": [6],
        }
    }
    result = normalize_open_meteo(
        payload,
        36.8,
        10.2,
        datetime(2026, 9, 28, 8, tzinfo=UTC),
    )
    assert result.temperature_c is None


def test_normalize_open_meteo_rejects_missing_timestamps() -> None:
    with pytest.raises(ValueError, match="timestamps"):
        normalize_open_meteo(
            {"hourly": {"time": []}},
            0,
            0,
            datetime.now(UTC),
        )


def test_normalize_open_meteo_rejects_time_outside_response_range() -> None:
    payload: dict[str, object] = {
        "hourly": {
            "time": ["2026-09-28T08:00"],
            "temperature_2m": [20],
            "precipitation": [0],
            "wind_speed_10m": [4],
            "wind_gusts_10m": [6],
        }
    }
    with pytest.raises(ValueError, match="outside"):
        normalize_open_meteo(
            payload,
            36.8,
            10.2,
            datetime(2026, 10, 20, 8, tzinfo=UTC),
        )


def test_open_meteo_provider_normalizes_mocked_http_response() -> None:
    import asyncio

    import httpx
    import respx

    from flightops.domain import Waypoint
    from flightops.weather import OpenMeteoWeatherProvider

    endpoint = "https://weather.example.test/forecast"
    payload = {
        "hourly": {
            "time": ["2026-09-28T08:00"],
            "temperature_2m": [20],
            "precipitation": [0],
            "wind_speed_10m": [4],
            "wind_gusts_10m": [6],
        }
    }
    with respx.mock:
        respx.get(endpoint).mock(return_value=httpx.Response(200, json=payload))
        result = asyncio.run(
            OpenMeteoWeatherProvider(endpoint).conditions_for_route(
                [Waypoint(0, 36.8, 10.1), Waypoint(1, 36.9, 10.3)],
                datetime(2026, 9, 28, 8, tzinfo=UTC),
            )
        )
    assert len(result) == 1
    assert result[0].wind_speed_mps == 4


def test_open_meteo_provider_translates_http_failure() -> None:
    import asyncio

    import httpx
    import respx

    from flightops.domain import Waypoint
    from flightops.weather import OpenMeteoWeatherProvider, WeatherProviderError

    endpoint = "https://weather.example.test/forecast"
    with respx.mock:
        respx.get(endpoint).mock(return_value=httpx.Response(503))
        with pytest.raises(WeatherProviderError, match="unavailable"):
            asyncio.run(
                OpenMeteoWeatherProvider(endpoint).conditions_for_route(
                    [Waypoint(0, 36.8, 10.1), Waypoint(1, 36.9, 10.3)],
                    datetime(2026, 9, 28, 8, tzinfo=UTC),
                )
            )
