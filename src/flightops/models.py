import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flightops.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class AircraftModel(Base):
    __tablename__ = "aircraft"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    max_wind_speed_mps: Mapped[float] = mapped_column(Float)
    max_gust_speed_mps: Mapped[float] = mapped_column(Float)
    max_precipitation_mm_per_hour: Mapped[float] = mapped_column(Float)
    min_temperature_c: Mapped[float] = mapped_column(Float)
    max_temperature_c: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    missions: Mapped[list["MissionModel"]] = relationship(
        back_populates="aircraft", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("max_wind_speed_mps >= 0", name="ck_aircraft_wind_positive"),
        CheckConstraint("max_gust_speed_mps >= 0", name="ck_aircraft_gust_positive"),
        CheckConstraint(
            "max_precipitation_mm_per_hour >= 0",
            name="ck_aircraft_precipitation_positive",
        ),
        CheckConstraint(
            "min_temperature_c < max_temperature_c",
            name="ck_aircraft_temperature_range",
        ),
    )


class MissionModel(Base):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    aircraft_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aircraft.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    planned_departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    aircraft: Mapped[AircraftModel] = relationship(back_populates="missions")
    waypoints: Mapped[list["WaypointModel"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="WaypointModel.sequence",
    )
    assessments: Mapped[list["AssessmentModel"]] = relationship(
        back_populates="mission", cascade="all, delete-orphan"
    )


class WaypointModel(Base):
    __tablename__ = "waypoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    mission: Mapped[MissionModel] = relationship(back_populates="waypoints")

    __table_args__ = (
        UniqueConstraint("mission_id", "sequence", name="uq_waypoint_mission_sequence"),
        CheckConstraint("sequence >= 0", name="ck_waypoint_sequence_positive"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_waypoint_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_waypoint_longitude"),
    )


class WeatherSnapshotModel(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(60))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observations: Mapped[list[dict[str, Any]]] = mapped_column(JSON)


class AssessmentModel(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), index=True
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("weather_snapshots.id", ondelete="RESTRICT"), unique=True
    )
    candidate_departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), index=True)
    limiting_factor: Mapped[str] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(30))
    details: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    mission: Mapped[MissionModel] = relationship(back_populates="assessments")
    snapshot: Mapped[WeatherSnapshotModel] = relationship()
