import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from flightops.models import AircraftModel

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.integration


@pytest.mark.skipif(TEST_DATABASE_URL is None, reason="TEST_DATABASE_URL is not configured")
def test_aircraft_round_trip_against_postgresql() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)
    name = f"Integration {uuid.uuid4()}"
    aircraft = AircraftModel(
        name=name,
        max_wind_speed_mps=10,
        max_gust_speed_mps=15,
        max_precipitation_mm_per_hour=2,
        min_temperature_c=-10,
        max_temperature_c=40,
    )
    with Session(engine) as session:
        session.add(aircraft)
        session.commit()
        aircraft_id = aircraft.id

    with Session(engine) as session:
        stored = session.scalar(select(AircraftModel).where(AircraftModel.id == aircraft_id))
        assert stored is not None
        assert stored.name == name
        session.delete(stored)
        session.commit()
