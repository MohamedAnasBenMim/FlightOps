from fastapi.testclient import TestClient

from tests.conftest import StubWeatherProvider


def test_aircraft_create_get_and_list(
    client: TestClient, aircraft_payload: dict[str, object]
) -> None:
    created = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert created.status_code == 201
    aircraft_id = created.json()["id"]

    fetched = client.get(f"/api/v1/aircraft/{aircraft_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Surveyor X1"
    assert len(client.get("/api/v1/aircraft").json()) == 1


def test_duplicate_aircraft_name_returns_standard_conflict(
    client: TestClient, aircraft_payload: dict[str, object]
) -> None:
    assert client.post("/api/v1/aircraft", json=aircraft_payload).status_code == 201
    response = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "aircraft_name_conflict"


def test_aircraft_validation_uses_standard_error(
    client: TestClient, aircraft_payload: dict[str, object]
) -> None:
    aircraft_payload["max_wind_speed_mps"] = -1
    response = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_mission_requires_existing_aircraft(client: TestClient) -> None:
    response = client.post(
        "/api/v1/missions",
        json={
            "aircraft_id": "b1767759-038c-4306-977d-fbe88fa1e809",
            "name": "Unknown aircraft",
            "planned_departure_at": "2026-09-28T08:00:00Z",
            "waypoints": [{"latitude": 1, "longitude": 2}, {"latitude": 3, "longitude": 4}],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "aircraft_not_found"


def test_mission_preserves_waypoint_order(
    client: TestClient, created_mission: dict[str, object]
) -> None:
    mission = client.get(f"/api/v1/missions/{created_mission['id']}")
    assert mission.status_code == 200
    assert [point["sequence"] for point in mission.json()["waypoints"]] == [0, 1, 2]


def test_assessment_is_persisted_with_snapshot(
    client: TestClient, created_mission: dict[str, object]
) -> None:
    response = client.post(f"/api/v1/missions/{created_mission['id']}/assessments", json={})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SAFE"
    assert body["rule_version"] == "2026-01"
    assert len(body["snapshot"]["observations"]) == 2

    fetched = client.get(f"/api/v1/assessments/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["details"] == body["details"]


def test_unsafe_assessment_explains_limiting_factor(
    client: TestClient,
    created_mission: dict[str, object],
    weather_provider: StubWeatherProvider,
) -> None:
    weather_provider.wind = 20
    response = client.post(f"/api/v1/missions/{created_mission['id']}/assessments", json={})
    assert response.status_code == 201
    assert response.json()["status"] == "UNSAFE"
    assert response.json()["limiting_factor"] == "wind_speed"


def test_flight_windows_group_adjacent_suitable_candidates(
    client: TestClient, created_mission: dict[str, object]
) -> None:
    response = client.get(
        f"/api/v1/missions/{created_mission['id']}/flight-windows",
        params={
            "start_at": "2026-09-28T08:00:00Z",
            "end_at": "2026-09-28T10:00:00Z",
            "interval_minutes": 60,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["candidates"]) == 3
    assert body["windows"] == [
        {
            "start_at": "2026-09-28T08:00:00Z",
            "end_at": "2026-09-28T10:00:00Z",
            "best_status": "SAFE",
        }
    ]


def test_readiness_checks_database(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
