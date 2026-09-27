# FlightOps API guide

The interactive OpenAPI contract is available at /docs. All timestamps must
include an offset and are normalized to UTC internally.

## Create an aircraft

~~~bash
curl -X POST http://localhost:8000/api/v1/aircraft \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Surveyor X1",
    "max_wind_speed_mps": 12,
    "max_gust_speed_mps": 18,
    "max_precipitation_mm_per_hour": 2,
    "min_temperature_c": -10,
    "max_temperature_c": 45
  }'
~~~

Maximum limits are inclusive. The gust limit must be at least the sustained-wind
limit, and the minimum temperature must be below the maximum.

## Create a mission

Replace AIRCRAFT_ID with the returned UUID.

~~~bash
curl -X POST http://localhost:8000/api/v1/missions \
  -H 'Content-Type: application/json' \
  -d '{
    "aircraft_id": "AIRCRAFT_ID",
    "name": "Coastal inspection",
    "planned_departure_at": "2026-09-28T08:00:00Z",
    "waypoints": [
      {"latitude": 36.8065, "longitude": 10.1815},
      {"latitude": 36.8500, "longitude": 10.2500},
      {"latitude": 36.9000, "longitude": 10.3000}
    ]
  }'
~~~

A mission requires 2–50 waypoints. List order becomes the immutable route order.

## Assess a mission

~~~bash
curl -X POST http://localhost:8000/api/v1/missions/MISSION_ID/assessments \
  -H 'Content-Type: application/json' \
  -d '{}'
~~~

Optionally provide candidate_departure_at to assess another departure. The
response contains overall status, limiting factor, rule version, every segment
and constraint reason, normalized weather observations, and retrieval metadata.

## Find flight windows

~~~bash
curl --get http://localhost:8000/api/v1/missions/MISSION_ID/flight-windows \
  --data-urlencode 'start_at=2026-09-28T08:00:00Z' \
  --data-urlencode 'end_at=2026-09-28T18:00:00Z' \
  --data-urlencode 'interval_minutes=60'
~~~

SAFE and WARNING candidates are suitable; UNSAFE candidates break a window.
end_at in a returned window is the last suitable candidate departure, not a
guarantee for every instant until the next interval.

## Error shape

~~~json
{
  "error": {
    "code": "mission_not_found",
    "message": "Mission was not found",
    "details": null
  }
}
~~~

Typical status codes are 422 for validation, 404 for missing resources, 409 for
conflicts, and 503 for forecast-provider failures.
