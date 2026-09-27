from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import asin, cos, radians, sin, sqrt


class AssessmentStatus(StrEnum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    UNSAFE = "UNSAFE"


@dataclass(frozen=True)
class OperationalLimits:
    max_wind_speed_mps: float
    max_gust_speed_mps: float
    max_precipitation_mm_per_hour: float
    min_temperature_c: float
    max_temperature_c: float

    def __post_init__(self) -> None:
        if any(
            value < 0
            for value in (
                self.max_wind_speed_mps,
                self.max_gust_speed_mps,
                self.max_precipitation_mm_per_hour,
            )
        ):
            raise ValueError("Maximum weather limits cannot be negative")
        if self.min_temperature_c >= self.max_temperature_c:
            raise ValueError("Minimum temperature must be below maximum temperature")


@dataclass(frozen=True)
class Waypoint:
    sequence: int
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("Waypoint sequence cannot be negative")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")


@dataclass(frozen=True)
class WeatherCondition:
    latitude: float
    longitude: float
    forecast_at: datetime
    wind_speed_mps: float | None
    wind_gust_mps: float | None
    precipitation_mm_per_hour: float | None
    temperature_c: float | None


@dataclass(frozen=True)
class ConstraintResult:
    metric: str
    status: AssessmentStatus
    value: float | None
    limit: float | str
    margin: float | None
    reason: str


@dataclass(frozen=True)
class SegmentResult:
    segment_index: int
    status: AssessmentStatus
    constraints: tuple[ConstraintResult, ...]


@dataclass(frozen=True)
class MissionResult:
    status: AssessmentStatus
    limiting_factor: str
    segments: tuple[SegmentResult, ...]


def route_distance_km(waypoints: list[Waypoint]) -> float:
    def distance(start: Waypoint, end: Waypoint) -> float:
        radius_km = 6371.0
        lat1, lat2 = radians(start.latitude), radians(end.latitude)
        delta_lat = radians(end.latitude - start.latitude)
        delta_lon = radians(end.longitude - start.longitude)
        value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 2 * radius_km * asin(sqrt(value))

    return sum(distance(a, b) for a, b in zip(waypoints, waypoints[1:], strict=False))
