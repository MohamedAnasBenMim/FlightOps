import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AircraftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    max_wind_speed_mps: float = Field(ge=0, le=100)
    max_gust_speed_mps: float = Field(ge=0, le=150)
    max_precipitation_mm_per_hour: float = Field(ge=0, le=500)
    min_temperature_c: float = Field(ge=-100, le=100)
    max_temperature_c: float = Field(ge=-100, le=100)

    @model_validator(mode="after")
    def validate_limits(self) -> "AircraftCreate":
        if self.min_temperature_c >= self.max_temperature_c:
            raise ValueError("min_temperature_c must be below max_temperature_c")
        if self.max_gust_speed_mps < self.max_wind_speed_mps:
            raise ValueError("max_gust_speed_mps must be at least max_wind_speed_mps")
        return self


class AircraftOut(AircraftCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class WaypointCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class WaypointOut(WaypointCreate):
    model_config = ConfigDict(from_attributes=True)

    sequence: int


class MissionCreate(BaseModel):
    aircraft_id: uuid.UUID
    name: str = Field(min_length=1, max_length=160)
    planned_departure_at: datetime
    waypoints: list[WaypointCreate] = Field(min_length=2, max_length=50)

    @field_validator("planned_departure_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("planned_departure_at must include a timezone")
        return value


class MissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aircraft_id: uuid.UUID
    name: str
    planned_departure_at: datetime
    waypoints: list[WaypointOut]
    created_at: datetime


class AssessmentCreate(BaseModel):
    candidate_departure_at: datetime | None = None

    @field_validator("candidate_departure_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("candidate_departure_at must include a timezone")
        return value


class WeatherSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    retrieved_at: datetime
    observations: list[dict[str, Any]]


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mission_id: uuid.UUID
    candidate_departure_at: datetime
    status: str
    limiting_factor: str
    rule_version: str
    details: dict[str, Any]
    snapshot: WeatherSnapshotOut
    created_at: datetime


class WindowCandidate(BaseModel):
    departure_at: datetime
    status: str
    limiting_factor: str


class FlightWindow(BaseModel):
    start_at: datetime
    end_at: datetime
    best_status: str


class FlightWindowResponse(BaseModel):
    mission_id: uuid.UUID
    interval_minutes: int
    candidates: list[WindowCandidate]
    windows: list[FlightWindow]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
