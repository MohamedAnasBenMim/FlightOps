from collections.abc import Generator, Sequence
from datetime import UTC, datetime
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from flightops.api.dependencies import get_weather_provider
from flightops.database import Base, get_session
from flightops.domain import Waypoint, WeatherCondition
from flightops.main import create_app


class StubWeatherProvider:
    def __init__(
        self,
        *,
        wind: float | None = 5,
        gust: float | None = 7,
        precipitation: float | None = 0,
        temperature: float | None = 20,
    ) -> None:
        self.wind = wind
        self.gust = gust
        self.precipitation = precipitation
        self.temperature = temperature

    async def conditions_for_route(
        self, waypoints: Sequence[Waypoint], departure_at: datetime
    ) -> list[WeatherCondition]:
        return [
            WeatherCondition(
                latitude=(start.latitude + end.latitude) / 2,
                longitude=(start.longitude + end.longitude) / 2,
                forecast_at=departure_at.astimezone(UTC),
                wind_speed_mps=self.wind,
                wind_gust_mps=self.gust,
                precipitation_mm_per_hour=self.precipitation,
                temperature_c=self.temperature,
            )
            for start, end in zip(waypoints, waypoints[1:], strict=False)
        ]


@pytest.fixture
def weather_provider() -> StubWeatherProvider:
    return StubWeatherProvider()


@pytest.fixture
def client(weather_provider: StubWeatherProvider) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(
        engine,
        "connect",
        lambda connection, _record: connection.execute("PRAGMA foreign_keys=ON"),
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_weather_provider] = lambda: weather_provider
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)


@pytest.fixture
def aircraft_payload() -> dict[str, object]:
    return {
        "name": "Surveyor X1",
        "max_wind_speed_mps": 12,
        "max_gust_speed_mps": 18,
        "max_precipitation_mm_per_hour": 2,
        "min_temperature_c": -10,
        "max_temperature_c": 45,
    }


@pytest.fixture
def created_aircraft(client: TestClient, aircraft_payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


@pytest.fixture
def created_mission(client: TestClient, created_aircraft: dict[str, object]) -> dict[str, object]:
    response = client.post(
        "/api/v1/missions",
        json={
            "aircraft_id": created_aircraft["id"],
            "name": "Coastal inspection",
            "planned_departure_at": "2026-09-28T08:00:00Z",
            "waypoints": [
                {"latitude": 36.8065, "longitude": 10.1815},
                {"latitude": 36.85, "longitude": 10.25},
                {"latitude": 36.9, "longitude": 10.3},
            ],
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())
