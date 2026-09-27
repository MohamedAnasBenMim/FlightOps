import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from flightops.domain import AssessmentStatus, OperationalLimits, Waypoint
from flightops.errors import AppError
from flightops.models import (
    AircraftModel,
    AssessmentModel,
    MissionModel,
    WaypointModel,
    WeatherSnapshotModel,
)
from flightops.risk import RULE_VERSION, evaluate_mission, serialize_result
from flightops.schemas import AircraftCreate, MissionCreate
from flightops.weather import WeatherProvider, WeatherProviderError


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def create_aircraft(session: Session, payload: AircraftCreate) -> AircraftModel:
    aircraft = AircraftModel(**payload.model_dump())
    session.add(aircraft)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise AppError(409, "aircraft_name_conflict", "Aircraft name already exists") from exc
    session.refresh(aircraft)
    return aircraft


def get_aircraft(session: Session, aircraft_id: uuid.UUID) -> AircraftModel:
    aircraft = session.get(AircraftModel, aircraft_id)
    if aircraft is None:
        raise AppError(404, "aircraft_not_found", "Aircraft was not found")
    return aircraft


def create_mission(session: Session, payload: MissionCreate) -> MissionModel:
    get_aircraft(session, payload.aircraft_id)
    mission = MissionModel(
        aircraft_id=payload.aircraft_id,
        name=payload.name,
        planned_departure_at=as_utc(payload.planned_departure_at),
        waypoints=[
            WaypointModel(
                sequence=index,
                latitude=waypoint.latitude,
                longitude=waypoint.longitude,
            )
            for index, waypoint in enumerate(payload.waypoints)
        ],
    )
    session.add(mission)
    session.commit()
    return get_mission(session, mission.id)


def get_mission(session: Session, mission_id: uuid.UUID) -> MissionModel:
    mission = session.scalar(
        select(MissionModel)
        .where(MissionModel.id == mission_id)
        .options(
            selectinload(MissionModel.waypoints),
            selectinload(MissionModel.aircraft),
        )
    )
    if mission is None:
        raise AppError(404, "mission_not_found", "Mission was not found")
    return mission


def to_waypoints(records: Sequence[WaypointModel]) -> list[Waypoint]:
    return [
        Waypoint(item.sequence, item.latitude, item.longitude)
        for item in sorted(records, key=lambda item: item.sequence)
    ]


def limits_for(aircraft: AircraftModel) -> OperationalLimits:
    return OperationalLimits(
        max_wind_speed_mps=aircraft.max_wind_speed_mps,
        max_gust_speed_mps=aircraft.max_gust_speed_mps,
        max_precipitation_mm_per_hour=aircraft.max_precipitation_mm_per_hour,
        min_temperature_c=aircraft.min_temperature_c,
        max_temperature_c=aircraft.max_temperature_c,
    )


def serialize_conditions(conditions: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "latitude": item.latitude,
            "longitude": item.longitude,
            "forecast_at": item.forecast_at.isoformat(),
            "wind_speed_mps": item.wind_speed_mps,
            "wind_gust_mps": item.wind_gust_mps,
            "precipitation_mm_per_hour": item.precipitation_mm_per_hour,
            "temperature_c": item.temperature_c,
        }
        for item in conditions
    ]


async def create_assessment(
    session: Session,
    mission_id: uuid.UUID,
    provider: WeatherProvider,
    departure_at: datetime | None = None,
) -> AssessmentModel:
    mission = get_mission(session, mission_id)
    candidate = as_utc(departure_at or mission.planned_departure_at)
    try:
        conditions = await provider.conditions_for_route(to_waypoints(mission.waypoints), candidate)
    except WeatherProviderError as exc:
        raise AppError(503, "weather_provider_unavailable", str(exc)) from exc

    result = evaluate_mission(conditions, limits_for(mission.aircraft))
    details = serialize_result(result)
    snapshot = WeatherSnapshotModel(
        provider=provider.__class__.__name__,
        retrieved_at=datetime.now(UTC),
        observations=serialize_conditions(conditions),
    )
    assessment = AssessmentModel(
        mission_id=mission.id,
        snapshot=snapshot,
        candidate_departure_at=candidate,
        status=result.status.value,
        limiting_factor=result.limiting_factor,
        rule_version=RULE_VERSION,
        details=details,
    )
    session.add(assessment)
    session.commit()
    return get_assessment(session, assessment.id)


def get_assessment(session: Session, assessment_id: uuid.UUID) -> AssessmentModel:
    assessment = session.scalar(
        select(AssessmentModel)
        .where(AssessmentModel.id == assessment_id)
        .options(selectinload(AssessmentModel.snapshot))
    )
    if assessment is None:
        raise AppError(404, "assessment_not_found", "Assessment was not found")
    return assessment


async def recommend_windows(
    session: Session,
    mission_id: uuid.UUID,
    provider: WeatherProvider,
    start_at: datetime,
    end_at: datetime,
    interval_minutes: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mission = get_mission(session, mission_id)
    start = as_utc(start_at)
    end = as_utc(end_at)
    if end <= start:
        raise AppError(422, "invalid_window_range", "end_at must be after start_at")
    count = int((end - start).total_seconds() // (interval_minutes * 60)) + 1
    if count > 48:
        raise AppError(422, "too_many_candidates", "Search is limited to 48 candidates")

    candidates: list[dict[str, Any]] = []
    current = start
    while current <= end:
        try:
            conditions = await provider.conditions_for_route(
                to_waypoints(mission.waypoints), current
            )
        except WeatherProviderError as exc:
            raise AppError(503, "weather_provider_unavailable", str(exc)) from exc
        result = evaluate_mission(conditions, limits_for(mission.aircraft))
        candidates.append(
            {
                "departure_at": current,
                "status": result.status.value,
                "limiting_factor": result.limiting_factor,
            }
        )
        current += timedelta(minutes=interval_minutes)

    suitable = {
        AssessmentStatus.SAFE.value,
        AssessmentStatus.WARNING.value,
    }
    windows: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    for candidate in candidates:
        if candidate["status"] in suitable:
            if active is None:
                active = {
                    "start_at": candidate["departure_at"],
                    "end_at": candidate["departure_at"],
                    "best_status": candidate["status"],
                }
            else:
                active["end_at"] = candidate["departure_at"]
                if candidate["status"] == AssessmentStatus.SAFE.value:
                    active["best_status"] = AssessmentStatus.SAFE.value
        elif active is not None:
            windows.append(active)
            active = None
    if active is not None:
        windows.append(active)
    windows.sort(
        key=lambda item: (
            item["best_status"] != AssessmentStatus.SAFE.value,
            item["start_at"],
        )
    )
    return candidates, windows
