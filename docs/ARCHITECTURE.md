# FlightOps architecture

## System shape

FlightOps uses a modular monolith for the API and a separately built Vue client.
This keeps deployment and local operation simple while preserving explicit
boundaries that can be tested independently.

~~~mermaid
flowchart LR
    UI[Vue 3 dashboard] --> API[FastAPI routes]
    API --> APP[Application services]
    APP --> DOMAIN[Domain models and risk rules]
    APP --> ORM[SQLAlchemy persistence]
    APP --> WEATHER[Weather provider interface]
    ORM --> PG[(PostgreSQL)]
    WEATHER --> OM[Open-Meteo]
~~~

## Backend boundaries

- api/routes.py: HTTP validation, status codes, dependency injection, and
  response models. It contains no weather or risk logic.
- services.py: use-case orchestration and transaction boundaries.
- domain.py: framework-independent value objects and route geometry.
- risk.py: pure, deterministic assessment and aggregation.
- weather.py: provider protocol, Open-Meteo HTTP access, and normalization.
- models.py: relational mappings only.
- database.py: engine and session lifecycle.
- schemas.py: HTTP request and response contracts.

The dependency direction is inward: domain logic imports neither FastAPI,
SQLAlchemy, nor provider response types.

## Assessment data flow

1. The API loads the mission, ordered waypoints, and aircraft.
2. Consecutive waypoints become route segments.
3. Weather is sampled at each segment midpoint for the candidate departure.
4. Open-Meteo hourly data is normalized to internal SI-unit conditions.
5. Pure rules evaluate each metric and aggregate each segment.
6. Worst-severity precedence produces the mission status.
7. The normalized conditions and versioned result are committed atomically.
8. Retrieval returns the stored result; it does not silently call the provider
   or recalculate history.

Midpoint and common-departure sampling are deliberate MVP approximations. They
avoid claiming interpolation precision the provider data does not support.
Segment traversal timing is a future improvement.

## Persistence design

- Aircraft own operational limits.
- A mission references one aircraft and owns ordered waypoints.
- The database enforces coordinate ranges and unique waypoint order per mission.
- Each assessment references exactly one immutable weather snapshot.
- Assessment details are stored as JSON because the evidence is retrieved as a
  cohesive document and is versioned by rule_version. Core searchable fields
  such as mission, status, departure, and limiting factor remain columns.

PostgreSQL is the target database. SQLite is used only for fast isolated API
tests and an optional zero-configuration developer fallback. CI also exercises
a real migrated PostgreSQL database.

## Failure behavior

- Boundary validation returns a stable validation_error.
- Missing resources return explicit 404 codes.
- Name conflicts return 409.
- Provider or normalization failure returns 503 and persists no partial result.
- Missing individual weather metrics fail closed as UNSAFE.
- Readiness queries the database; liveness only reports that the process can
  serve requests.

## Security and operations

- Both runtime images run as non-root users.
- Secrets come from environment variables and are excluded from Git.
- Logs include request IDs, status codes, paths, and duration without request
  bodies or credentials.
- Candidate searches are capped at 48 provider evaluations.
- CORS origins are explicit.
- Migrations run as a one-off operation, not at every process startup.

Authentication and authorization are intentionally outside this single-user
portfolio MVP. Add them before exposing write endpoints to untrusted users.
