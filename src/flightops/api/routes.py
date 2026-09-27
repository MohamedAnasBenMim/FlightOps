import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from flightops.api.dependencies import get_weather_provider
from flightops.database import database_is_ready, get_session
from flightops.models import AircraftModel, AssessmentModel, MissionModel
from flightops.schemas import (
    AircraftCreate,
    AircraftOut,
    AssessmentCreate,
    AssessmentOut,
    FlightWindow,
    FlightWindowResponse,
    MissionCreate,
    MissionOut,
    WindowCandidate,
)
from flightops.services import (
    create_aircraft,
    create_assessment,
    create_mission,
    get_aircraft,
    get_assessment,
    get_mission,
    recommend_windows,
)
from flightops.weather import WeatherProvider

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
WeatherDep = Annotated[WeatherProvider, Depends(get_weather_provider)]


@router.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", tags=["health"])
def readiness(session: SessionDep) -> dict[str, str]:
    database_is_ready(session)
    return {"status": "ready"}


@router.post(
    "/api/v1/aircraft",
    response_model=AircraftOut,
    status_code=status.HTTP_201_CREATED,
    tags=["aircraft"],
)
def aircraft_create(payload: AircraftCreate, session: SessionDep) -> AircraftModel:
    return create_aircraft(session, payload)


@router.get("/api/v1/aircraft", response_model=list[AircraftOut], tags=["aircraft"])
def aircraft_list(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AircraftModel]:
    return list(
        session.scalars(
            select(AircraftModel)
            .order_by(AircraftModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


@router.get(
    "/api/v1/aircraft/{aircraft_id}",
    response_model=AircraftOut,
    tags=["aircraft"],
)
def aircraft_get(aircraft_id: uuid.UUID, session: SessionDep) -> AircraftModel:
    return get_aircraft(session, aircraft_id)


@router.post(
    "/api/v1/missions",
    response_model=MissionOut,
    status_code=status.HTTP_201_CREATED,
    tags=["missions"],
)
def mission_create(payload: MissionCreate, session: SessionDep) -> MissionModel:
    return create_mission(session, payload)


@router.get("/api/v1/missions", response_model=list[MissionOut], tags=["missions"])
def mission_list(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MissionModel]:
    return list(
        session.scalars(
            select(MissionModel)
            .options(selectinload(MissionModel.waypoints))
            .order_by(MissionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


@router.get(
    "/api/v1/missions/{mission_id}",
    response_model=MissionOut,
    tags=["missions"],
)
def mission_get(mission_id: uuid.UUID, session: SessionDep) -> MissionModel:
    return get_mission(session, mission_id)


@router.post(
    "/api/v1/missions/{mission_id}/assessments",
    response_model=AssessmentOut,
    status_code=status.HTTP_201_CREATED,
    tags=["assessments"],
)
async def assessment_create(
    mission_id: uuid.UUID,
    payload: AssessmentCreate,
    session: SessionDep,
    provider: WeatherDep,
) -> AssessmentModel:
    return await create_assessment(session, mission_id, provider, payload.candidate_departure_at)


@router.get(
    "/api/v1/assessments/{assessment_id}",
    response_model=AssessmentOut,
    tags=["assessments"],
)
def assessment_get(assessment_id: uuid.UUID, session: SessionDep) -> AssessmentModel:
    return get_assessment(session, assessment_id)


@router.get(
    "/api/v1/missions/{mission_id}/flight-windows",
    response_model=FlightWindowResponse,
    tags=["flight-windows"],
)
async def flight_windows(
    mission_id: uuid.UUID,
    session: SessionDep,
    provider: WeatherDep,
    start_at: datetime,
    end_at: datetime,
    interval_minutes: Annotated[int, Query(ge=15, le=360)] = 60,
) -> FlightWindowResponse:
    candidates, windows = await recommend_windows(
        session,
        mission_id,
        provider,
        start_at,
        end_at,
        interval_minutes,
    )
    return FlightWindowResponse(
        mission_id=mission_id,
        interval_minutes=interval_minutes,
        candidates=[WindowCandidate.model_validate(item) for item in candidates],
        windows=[FlightWindow.model_validate(item) for item in windows],
    )
