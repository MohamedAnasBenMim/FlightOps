"""Create the FlightOps MVP schema."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260927_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "aircraft",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("max_wind_speed_mps", sa.Float(), nullable=False),
        sa.Column("max_gust_speed_mps", sa.Float(), nullable=False),
        sa.Column("max_precipitation_mm_per_hour", sa.Float(), nullable=False),
        sa.Column("min_temperature_c", sa.Float(), nullable=False),
        sa.Column("max_temperature_c", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("max_gust_speed_mps >= 0", name="ck_aircraft_gust_positive"),
        sa.CheckConstraint(
            "max_precipitation_mm_per_hour >= 0",
            name="ck_aircraft_precipitation_positive",
        ),
        sa.CheckConstraint(
            "min_temperature_c < max_temperature_c",
            name="ck_aircraft_temperature_range",
        ),
        sa.CheckConstraint("max_wind_speed_mps >= 0", name="ck_aircraft_wind_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aircraft_name"), "aircraft", ["name"], unique=True)
    op.create_table(
        "missions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("aircraft_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("planned_departure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_missions_aircraft_id"), "missions", ["aircraft_id"])
    op.create_index(
        op.f("ix_missions_planned_departure_at"),
        "missions",
        ["planned_departure_at"],
    )
    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=60), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observations", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "waypoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_waypoint_latitude"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_waypoint_longitude"),
        sa.CheckConstraint("sequence >= 0", name="ck_waypoint_sequence_positive"),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mission_id", "sequence", name="uq_waypoint_mission_sequence"),
    )
    op.create_index(op.f("ix_waypoints_mission_id"), "waypoints", ["mission_id"])
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_departure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("limiting_factor", sa.String(length=80), nullable=False),
        sa.Column("rule_version", sa.String(length=30), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["weather_snapshots.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id"),
    )
    op.create_index(op.f("ix_assessments_mission_id"), "assessments", ["mission_id"])
    op.create_index(op.f("ix_assessments_status"), "assessments", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_assessments_status"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_mission_id"), table_name="assessments")
    op.drop_table("assessments")
    op.drop_index(op.f("ix_waypoints_mission_id"), table_name="waypoints")
    op.drop_table("waypoints")
    op.drop_table("weather_snapshots")
    op.drop_index(op.f("ix_missions_planned_departure_at"), table_name="missions")
    op.drop_index(op.f("ix_missions_aircraft_id"), table_name="missions")
    op.drop_table("missions")
    op.drop_index(op.f("ix_aircraft_name"), table_name="aircraft")
    op.drop_table("aircraft")
