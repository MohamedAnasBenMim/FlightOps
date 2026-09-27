from datetime import UTC, datetime

import pytest

from flightops.domain import OperationalLimits, Waypoint, WeatherCondition, route_distance_km
from flightops.risk import evaluate_mission


def test_operational_limits_reject_invalid_temperature_range() -> None:
    with pytest.raises(ValueError, match="below"):
        OperationalLimits(10, 15, 2, 30, 20)


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (-91, 0), (0, 181), (0, -181)],
)
def test_waypoint_rejects_invalid_coordinates(latitude: float, longitude: float) -> None:
    with pytest.raises(ValueError):
        Waypoint(0, latitude, longitude)


def test_route_distance_uses_each_route_segment() -> None:
    distance = route_distance_km(
        [
            Waypoint(0, 0, 0),
            Waypoint(1, 0, 1),
            Waypoint(2, 1, 1),
        ]
    )
    assert distance == pytest.approx(222.39, rel=0.01)


def condition(**overrides: float | None) -> WeatherCondition:
    values: dict[str, float | None] = {
        "wind_speed_mps": 5.0,
        "wind_gust_mps": 7.0,
        "precipitation_mm_per_hour": 0.0,
        "temperature_c": 20.0,
    }
    values.update(overrides)
    return WeatherCondition(
        latitude=36,
        longitude=10,
        forecast_at=datetime(2026, 9, 28, tzinfo=UTC),
        **values,
    )


def limits() -> OperationalLimits:
    return OperationalLimits(10, 15, 2, -10, 40)


def test_safe_conditions_produce_safe_assessment() -> None:
    result = evaluate_mission([condition()], limits())
    assert result.status == "SAFE"


def test_near_limit_is_warning_and_exact_limit_is_warning() -> None:
    result = evaluate_mission([condition(wind_speed_mps=10)], limits())
    assert result.status == "WARNING"
    assert result.limiting_factor == "wind_speed"


def test_breached_limit_is_unsafe() -> None:
    result = evaluate_mission([condition(wind_gust_mps=16)], limits())
    assert result.status == "UNSAFE"
    assert result.limiting_factor == "wind_gust"


def test_missing_weather_fails_closed() -> None:
    result = evaluate_mission([condition(temperature_c=None)], limits())
    assert result.status == "UNSAFE"
    assert "missing" in result.segments[0].constraints[3].reason
